"""Transcription service using faster-whisper for speech-to-text conversion."""

import os
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from queue import Queue, Empty
from dataclasses import dataclass

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from .config import TranscriptionConfig
from .logger import LoggerMixin
from .audio_capture import AudioSegment


@dataclass
class TranscriptionResult:
    """Result of transcription process."""
    audio_segment: AudioSegment
    text: str
    language: str
    confidence: float
    processing_time: float
    timestamp: datetime
    segments: List[Dict[str, Any]]  # Detailed segment info from Whisper


class TranscriptionService(LoggerMixin):
    """Service for transcribing audio segments using Whisper."""
    
    def __init__(self, config: TranscriptionConfig):
        self.config = config
        self._model: Optional[WhisperModel] = None
        self._model_lock = threading.Lock()
        
        # Processing queue and thread
        self._transcription_queue: Queue[AudioSegment] = Queue()
        self._result_queue: Queue[TranscriptionResult] = Queue()
        self._processing = False
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._on_transcription_complete: Optional[Callable[[TranscriptionResult], None]] = None
        
        # Statistics
        self._total_processed = 0
        self._total_processing_time = 0.0
        
        self.logger.info(f"TranscriptionService initialized with model: {config.model_size}")
    
    def initialize_model(self) -> bool:
        """Initialize the Whisper model."""
        if WhisperModel is None:
            self.logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
            return False
        
        try:
            with self._model_lock:
                if self._model is not None:
                    return True
                
                self.logger.info(f"Loading Whisper model: {self.config.model_size}")
                
                # Determine device
                device = self.config.device
                if device == "auto":
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                
                self._model = WhisperModel(
                    self.config.model_size,
                    device=device,
                    compute_type=self.config.compute_type
                )
                
                self.logger.info(f"Whisper model loaded successfully on {device}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Whisper model: {e}")
            return False
    
    def start_processing(self) -> bool:
        """Start the transcription processing thread."""
        if not self.initialize_model():
            return False
        
        if self._processing:
            self.logger.warning("Transcription processing already running")
            return True
        
        self._processing = True
        self._stop_event.clear()
        
        self._worker_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._worker_thread.start()
        
        self.logger.info("Transcription processing started")
        return True
    
    def stop_processing(self) -> None:
        """Stop the transcription processing thread."""
        if not self._processing:
            return
        
        self._processing = False
        self._stop_event.set()
        
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=10.0)
        
        self.logger.info("Transcription processing stopped")
    
    def set_transcription_callback(self, callback: Callable[[TranscriptionResult], None]) -> None:
        """Set callback function to be called when transcription is complete."""
        self._on_transcription_complete = callback
    
    def queue_audio_segment(self, segment: AudioSegment) -> None:
        """Add an audio segment to the transcription queue."""
        self._transcription_queue.put(segment)
        self.logger.debug(f"Audio segment queued for transcription: {segment.file_path.name}")
    
    def get_completed_transcriptions(self) -> List[TranscriptionResult]:
        """Get all completed transcription results from the queue."""
        results = []
        try:
            while True:
                result = self._result_queue.get_nowait()
                results.append(result)
        except Empty:
            pass
        return results
    
    def transcribe_file(self, audio_path: Path) -> Optional[TranscriptionResult]:
        """Transcribe a single audio file synchronously."""
        if not self.initialize_model():
            return None
        
        try:
            start_time = time.time()
            
            with self._model_lock:
                segments, info = self._model.transcribe(
                    str(audio_path),
                    language=self.config.language if self.config.language != "auto" else None,
                    beam_size=self.config.beam_size,
                    temperature=self.config.temperature,
                    word_timestamps=True
                )
            
            # Collect all segments and build full text
            segment_list = []
            full_text_parts = []
            
            for segment in segments:
                segment_dict = {
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'confidence': getattr(segment, 'avg_logprob', 0.0)
                }
                segment_list.append(segment_dict)
                full_text_parts.append(segment.text.strip())
            
            full_text = " ".join(full_text_parts).strip()
            processing_time = time.time() - start_time
            
            # Create dummy AudioSegment if we don't have one
            audio_segment = AudioSegment(
                file_path=audio_path,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=0.0,
                sample_rate=16000
            )
            
            result = TranscriptionResult(
                audio_segment=audio_segment,
                text=full_text,
                language=info.language,
                confidence=getattr(info, 'language_probability', 0.0),
                processing_time=processing_time,
                timestamp=datetime.now(),
                segments=segment_list
            )
            
            self.logger.info(f"Transcribed {audio_path.name} in {processing_time:.2f}s: "
                           f"{len(full_text)} characters")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error transcribing {audio_path}: {e}")
            return None
    
    def _processing_loop(self) -> None:
        """Main processing loop running in separate thread."""
        self.logger.info("Transcription processing loop started")
        
        while not self._stop_event.is_set():
            try:
                # Get audio segment from queue with timeout
                try:
                    segment = self._transcription_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Process the segment
                result = self._transcribe_segment(segment)
                
                if result:
                    # Add to result queue
                    self._result_queue.put(result)
                    
                    # Call callback if set
                    if self._on_transcription_complete:
                        try:
                            self._on_transcription_complete(result)
                        except Exception as e:
                            self.logger.error(f"Error in transcription callback: {e}")
                    
                    # Update statistics
                    self._total_processed += 1
                    self._total_processing_time += result.processing_time
                
                # Mark task as done
                self._transcription_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in transcription processing loop: {e}")
        
        self.logger.info("Transcription processing loop ended")
    
    def _transcribe_segment(self, segment: AudioSegment) -> Optional[TranscriptionResult]:
        """Transcribe a single audio segment."""
        if not segment.file_path.exists():
            self.logger.warning(f"Audio file not found: {segment.file_path}")
            return None
        
        try:
            start_time = time.time()
            
            with self._model_lock:
                segments, info = self._model.transcribe(
                    str(segment.file_path),
                    language=self.config.language if self.config.language != "auto" else None,
                    beam_size=self.config.beam_size,
                    temperature=self.config.temperature,
                    word_timestamps=True
                )
            
            # Collect all segments and build full text
            segment_list = []
            full_text_parts = []
            
            for seg in segments:
                segment_dict = {
                    'start': seg.start,
                    'end': seg.end,
                    'text': seg.text,
                    'confidence': getattr(seg, 'avg_logprob', 0.0)
                }
                segment_list.append(segment_dict)
                full_text_parts.append(seg.text.strip())
            
            full_text = " ".join(full_text_parts).strip()
            processing_time = time.time() - start_time
            
            result = TranscriptionResult(
                audio_segment=segment,
                text=full_text,
                language=info.language,
                confidence=getattr(info, 'language_probability', 0.0),
                processing_time=processing_time,
                timestamp=datetime.now(),
                segments=segment_list
            )
            
            self.logger.info(f"Transcribed {segment.file_path.name} in {processing_time:.2f}s: "
                           f"'{full_text[:100]}{'...' if len(full_text) > 100 else ''}'")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error transcribing segment {segment.file_path}: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get transcription processing statistics."""
        avg_processing_time = (
            self._total_processing_time / self._total_processed 
            if self._total_processed > 0 else 0.0
        )
        
        return {
            'total_processed': self._total_processed,
            'total_processing_time': self._total_processing_time,
            'average_processing_time': avg_processing_time,
            'queue_size': self._transcription_queue.qsize(),
            'model_loaded': self._model is not None,
            'processing': self._processing
        }
    
    def cleanup_audio_file(self, file_path: Path) -> None:
        """Clean up processed audio file."""
        try:
            if file_path.exists():
                file_path.unlink()
                self.logger.debug(f"Cleaned up audio file: {file_path.name}")
        except Exception as e:
            self.logger.error(f"Error cleaning up audio file {file_path}: {e}")
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        # Common languages supported by Whisper
        return [
            "auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", 
            "zh", "ar", "hi", "tr", "pl", "nl", "sv", "da", "no", "fi"
        ]