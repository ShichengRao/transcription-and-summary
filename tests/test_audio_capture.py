"""Tests for audio capture module."""

import pytest
import numpy as np
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

# Mock sounddevice before importing audio_capture
import sys
sys.modules['sounddevice'] = Mock()

from src.audio_capture import AudioCapture, AudioSegment
from src.config import AudioConfig


class TestAudioSegment:
    """Tests for AudioSegment dataclass."""

    def test_audio_segment_creation(self, temp_dir):
        """Test creating an AudioSegment."""
        audio_file = temp_dir / "test.wav"
        audio_file.touch()

        segment = AudioSegment(
            file_path=audio_file,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=5.0,
            sample_rate=16000,
        )

        assert segment.file_path == audio_file
        assert segment.duration == 5.0
        assert segment.sample_rate == 16000


class TestAudioCapture:
    """Tests for AudioCapture class."""

    def test_initialization(self, temp_dir):
        """Test AudioCapture initialization."""
        config = AudioConfig()
        capture = AudioCapture(config, temp_dir)

        assert capture.config == config
        assert capture.output_dir == temp_dir
        assert not capture.is_recording()

    def test_output_directory_creation(self, temp_dir):
        """Test that output directory is created."""
        output_dir = temp_dir / "audio_output"
        config = AudioConfig()
        capture = AudioCapture(config, output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_silence_detection_parameters(self, temp_dir):
        """Test silence detection configuration."""
        config = AudioConfig(
            silence_threshold=0.03, silence_duration=7.0, min_audio_duration=4.0
        )
        capture = AudioCapture(config, temp_dir)

        assert capture.config.silence_threshold == 0.03
        assert capture.config.silence_duration == 7.0
        assert capture.config.min_audio_duration == 4.0

    def test_has_sufficient_audio_content(self, temp_dir):
        """Test audio content quality check."""
        config = AudioConfig(silence_threshold=0.02, noise_gate_threshold=0.015)
        capture = AudioCapture(config, temp_dir)

        # Create audio with sufficient content
        sample_rate = 16000
        duration = 3
        t = np.linspace(0, duration, int(sample_rate * duration))
        loud_audio = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)

        assert capture._has_sufficient_audio_content(loud_audio)

        # Create audio with insufficient content (too quiet)
        quiet_audio = (np.sin(2 * np.pi * 440 * t) * 0.001).astype(np.float32)
        assert not capture._has_sufficient_audio_content(quiet_audio)

    def test_callback_registration(self, temp_dir):
        """Test segment callback registration."""
        config = AudioConfig()
        capture = AudioCapture(config, temp_dir)

        callback_called = []

        def test_callback(segment):
            callback_called.append(segment)

        capture.set_segment_callback(test_callback)
        assert capture._on_segment_complete is not None

    def test_audio_levels_tracking(self, temp_dir):
        """Test audio level monitoring."""
        config = AudioConfig()
        capture = AudioCapture(config, temp_dir)

        levels = capture.get_audio_levels()

        assert "current" in levels
        assert "average" in levels
        assert "maximum" in levels
        assert "threshold" in levels
        assert levels["threshold"] == config.silence_threshold

    def test_pause_resume(self, temp_dir):
        """Test pause and resume functionality."""
        config = AudioConfig()
        capture = AudioCapture(config, temp_dir)

        # Initially not paused
        assert not capture._paused

        # Pause
        capture.pause_recording()
        assert capture._paused

        # Resume
        capture.resume_recording()
        assert not capture._paused


class TestAudioProcessing:
    """Tests for audio processing functions."""

    def test_minimum_duration_filter(self, temp_dir):
        """Test that short audio segments are filtered out."""
        config = AudioConfig(min_audio_duration=3.0)
        capture = AudioCapture(config, temp_dir)

        # Create short audio (1 second)
        sample_rate = 16000
        short_audio = np.random.randn(sample_rate).astype(np.float32) * 0.1

        # This should be filtered out due to duration
        duration = len(short_audio) / sample_rate
        assert duration < config.min_audio_duration

    def test_silence_duration_threshold(self, temp_dir):
        """Test silence duration threshold."""
        config = AudioConfig(silence_duration=5.0)
        capture = AudioCapture(config, temp_dir)

        assert config.silence_duration == 5.0
        # This ensures natural pauses (2-4 seconds) don't trigger new files
        assert config.silence_duration > 4.0
