"""Audio capture module for continuous microphone recording."""

import threading
import time
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Callable, Dict, List, Optional

import numpy as np
import sounddevice as sd

from .config import AudioConfig
from .logger import LoggerMixin


@dataclass
class AudioSegment:
    """Represents a recorded audio segment."""

    file_path: Path
    start_time: datetime
    end_time: datetime
    duration: float
    sample_rate: int


class AudioCapture(LoggerMixin):
    """Handles continuous audio recording with rolling segments."""

    def __init__(self, config: AudioConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._recording = False
        self._paused = False
        self._stop_event = threading.Event()
        self._record_thread: Optional[threading.Thread] = None

        # Audio buffer and processing
        self._audio_buffer: List[np.ndarray] = []
        self._buffer_lock = threading.Lock()
        self._segment_queue: Queue[AudioSegment] = Queue()

        # Callbacks
        self._on_segment_complete: Optional[Callable[[AudioSegment], None]] = None

        # Silence detection
        self._silence_start: Optional[float] = None
        self._last_audio_time: Optional[float] = None

        # Audio level monitoring for debugging
        self._last_debug_log: Optional[float] = None
        self._audio_level_history: List[float] = []
        self._max_recent_level: float = 0.0

        self.logger.info(f"AudioCapture initialized with output dir: {output_dir}")

    def set_segment_callback(self, callback: Callable[[AudioSegment], None]) -> None:
        """Set callback function to be called when a segment is complete."""
        self._on_segment_complete = callback

    def start_recording(self) -> None:
        """Start continuous audio recording."""
        if self._recording:
            self.logger.warning("Recording already in progress")
            return

        self._recording = True
        self._paused = False
        self._stop_event.clear()

        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()

        self.logger.info(f"Audio recording started with config:")
        self.logger.info(f"  Sample rate: {self.config.sample_rate}")
        self.logger.info(f"  Channels: {self.config.channels}")
        self.logger.info(f"  Silence threshold: {self.config.silence_threshold}")
        self.logger.info(f"  Silence duration: {self.config.silence_duration}s")
        self.logger.info(f"  Min audio duration: {getattr(self.config, 'min_audio_duration', 'N/A')}s")

    def stop_recording(self) -> None:
        """Stop audio recording and save any remaining buffer."""
        if not self._recording:
            return

        self._recording = False
        self._stop_event.set()

        if self._record_thread and self._record_thread.is_alive():
            self._record_thread.join(timeout=5.0)

        # Save any remaining audio in buffer
        self._save_current_buffer()

        # Clean up resources
        self._cleanup_resources()

        self.logger.info("Audio recording stopped")

    def _cleanup_resources(self) -> None:
        """Clean up audio resources."""
        try:
            # Clear buffers
            with self._buffer_lock:
                self._audio_buffer.clear()

            # Clear queue
            while not self._segment_queue.empty():
                try:
                    self._segment_queue.get_nowait()
                except:
                    break

        except Exception as e:
            self.logger.error(f"Error cleaning up audio resources: {e}")

    def pause_recording(self) -> None:
        """Pause recording (keeps thread alive but stops capturing)."""
        self._paused = True
        self.logger.info("Audio recording paused")

    def resume_recording(self) -> None:
        """Resume recording."""
        self._paused = False
        self.logger.info("Audio recording resumed")

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording and not self._paused

    def get_audio_levels(self) -> Dict[str, float]:
        """Get current audio level information for debugging."""
        if not self._audio_level_history:
            return {"current": 0.0, "average": 0.0, "maximum": 0.0, "threshold": self.config.silence_threshold}

        current = float(self._audio_level_history[-1]) if self._audio_level_history else 0.0
        average = float(sum(self._audio_level_history) / len(self._audio_level_history))
        maximum = float(max(self._audio_level_history))

        return {
            "current": current,
            "average": average,
            "maximum": maximum,
            "threshold": float(self.config.silence_threshold),
            "samples": len(self._audio_level_history),
        }

    def get_completed_segments(self) -> List[AudioSegment]:
        """Get all completed audio segments from the queue."""
        segments = []
        try:
            while True:
                segment = self._segment_queue.get_nowait()
                segments.append(segment)
        except Empty:
            pass
        return segments

    def _record_loop(self) -> None:
        """Main recording loop running in separate thread."""
        try:
            # Configure audio stream
            stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=np.float32,
                device=self.config.device_id,
                callback=self._audio_callback,
                blocksize=1024,
            )

            with stream:
                self.logger.info(
                    f"Audio stream started - Sample rate: {self.config.sample_rate}, "
                    f"Channels: {self.config.channels}"
                )

                segment_start_time = time.time()

                while not self._stop_event.is_set():
                    # Check if it's time to save a segment
                    current_time = time.time()
                    if current_time - segment_start_time >= self.config.chunk_duration:
                        self._save_current_buffer()
                        segment_start_time = current_time

                    # Check for silence-based segmentation
                    if self._should_segment_on_silence():
                        self._save_current_buffer()
                        segment_start_time = current_time

                    time.sleep(0.1)  # Small sleep to prevent busy waiting

        except Exception as e:
            self.logger.error(f"Error in recording loop: {e}")
        finally:
            self.logger.info("Recording loop ended")

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Callback function for audio stream."""
        if status:
            self.logger.warning(f"Audio callback status: {status}")

        if self._paused:
            return

        # Convert to mono if needed
        if indata.shape[1] > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata[:, 0]

        # Add to buffer
        with self._buffer_lock:
            self._audio_buffer.append(audio_data.copy())

        # Update silence detection
        self._update_silence_detection(audio_data)

    def _update_silence_detection(self, audio_data: np.ndarray) -> None:
        """Update silence detection state with improved noise filtering."""
        current_time = time.time()

        # Calculate RMS (root mean square) for volume detection
        rms = np.sqrt(np.mean(audio_data**2))

        # Use the configured silence threshold directly
        effective_threshold = self.config.silence_threshold

        # Track audio levels for debugging
        self._audio_level_history.append(rms)
        if len(self._audio_level_history) > 100:  # Keep last 100 samples
            self._audio_level_history.pop(0)

        # Update max recent level
        self._max_recent_level = max(self._audio_level_history)

        # Log audio levels periodically for debugging
        if self._last_debug_log is None or current_time - self._last_debug_log > 5:  # Every 5 seconds
            avg_level = sum(self._audio_level_history) / len(self._audio_level_history)
            self.logger.info(
                f"Audio levels - Current: {rms:.4f}, Avg: {avg_level:.4f}, Max: {self._max_recent_level:.4f}, Threshold: {effective_threshold:.4f}"
            )
            self._last_debug_log = current_time

        if rms > effective_threshold:
            # Audio detected - reset silence timer
            self._silence_start = None
            self._last_audio_time = current_time
            self.logger.debug(f"Audio detected: RMS={rms:.4f} > {effective_threshold:.4f}")
        else:
            # Potential silence detected
            if self._silence_start is None:
                self._silence_start = current_time

    def _should_segment_on_silence(self) -> bool:
        """Check if we should create a segment based on silence detection."""
        if self._silence_start is None or self._last_audio_time is None:
            return False

        current_time = time.time()
        silence_duration = current_time - self._silence_start

        # Only segment if we have some audio and sufficient silence
        has_audio = len(self._audio_buffer) > 0
        sufficient_silence = silence_duration >= self.config.silence_duration

        return has_audio and sufficient_silence

    def _save_current_buffer(self) -> None:
        """Save current audio buffer to file and create AudioSegment."""
        with self._buffer_lock:
            if not self._audio_buffer:
                return

            # Concatenate all audio data
            audio_data = np.concatenate(self._audio_buffer)
            self._audio_buffer.clear()

        if len(audio_data) == 0:
            return

        # Check minimum duration and audio quality
        duration = len(audio_data) / self.config.sample_rate
        min_duration = getattr(self.config, "min_audio_duration", 2.0)

        if duration < min_duration:
            self.logger.debug(f"Skipping short audio segment ({duration:.1f}s)")
            return

        # Check if audio has sufficient non-silence content
        if not self._has_sufficient_audio_content(audio_data):
            self.logger.debug(f"Skipping low-content audio segment ({duration:.1f}s)")
            return

        # Generate filename with timestamp
        timestamp = datetime.now()
        filename = f"audio_{timestamp.strftime('%Y%m%d_%H%M%S')}.wav"
        file_path = self.output_dir / filename

        try:
            # Save as WAV file
            with wave.open(str(file_path), "wb") as wav_file:
                wav_file.setnchannels(self.config.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.config.sample_rate)

                # Convert float32 to int16
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())

            # Create AudioSegment object
            end_time = timestamp
            start_time = datetime.fromtimestamp(timestamp.timestamp() - duration)

            segment = AudioSegment(
                file_path=file_path,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                sample_rate=self.config.sample_rate,
            )

            # Add to queue and call callback
            self._segment_queue.put(segment)

            if self._on_segment_complete:
                try:
                    self._on_segment_complete(segment)
                except Exception as e:
                    self.logger.error(f"Error in segment callback: {e}")

            self.logger.info(f"Audio segment saved: {filename} ({duration:.1f}s)")

        except Exception as e:
            self.logger.error(f"Error saving audio segment: {e}")
            # Clean up file if it was partially created
            if file_path.exists():
                file_path.unlink()

    def _has_sufficient_audio_content(self, audio_data: np.ndarray) -> bool:
        """Check if audio data has sufficient non-silence content to be worth transcribing."""
        # Calculate RMS for the entire segment
        rms = np.sqrt(np.mean(audio_data**2))

        # Use noise gate threshold if available, otherwise use silence threshold
        noise_threshold = getattr(self.config, "noise_gate_threshold", self.config.silence_threshold)

        # Check if overall RMS is above noise threshold
        if rms < noise_threshold:
            return False

        # Check what percentage of the audio is above the threshold
        # Split into small chunks and count how many are above threshold
        chunk_size = int(self.config.sample_rate * 0.1)  # 100ms chunks
        above_threshold_chunks = 0
        total_chunks = 0

        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i : i + chunk_size]
            if len(chunk) > 0:
                chunk_rms = np.sqrt(np.mean(chunk**2))
                if chunk_rms > noise_threshold:
                    above_threshold_chunks += 1
                total_chunks += 1

        # Require at least 10% of chunks to be above threshold (reduced from 20%)
        if total_chunks == 0:
            return False

        content_ratio = above_threshold_chunks / total_chunks
        self.logger.debug(
            f"Audio content analysis: {above_threshold_chunks}/{total_chunks} chunks above threshold ({content_ratio:.1%})"
        )
        return content_ratio >= 0.1

    def get_available_devices(self) -> List[dict]:
        """Get list of available audio input devices."""
        try:
            devices = sd.query_devices()
            input_devices = []

            for i, device in enumerate(devices):
                if device["max_input_channels"] > 0:
                    input_devices.append(
                        {
                            "id": i,
                            "name": device["name"],
                            "channels": device["max_input_channels"],
                            "sample_rate": device["default_samplerate"],
                        }
                    )

            return input_devices
        except Exception as e:
            self.logger.error(f"Error querying audio devices: {e}")
            return []

    def test_device(self, device_id: Optional[int] = None) -> bool:
        """Test if the specified audio device is working."""
        try:
            with sd.InputStream(
                samplerate=self.config.sample_rate, channels=self.config.channels, device=device_id, blocksize=1024
            ):
                time.sleep(0.1)  # Brief test
            return True
        except Exception as e:
            self.logger.error(f"Device test failed: {e}")
            return False
