"""Pytest configuration and fixtures."""

import shutil
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from src.config import (
    AppConfig,
    AudioConfig,
    GoogleDocsConfig,
    StorageConfig,
    SummaryConfig,
    TranscriptionConfig,
    UIConfig,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup after test
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    config = AppConfig(
        audio=AudioConfig(
            sample_rate=16000,
            channels=1,
            chunk_duration=30,
            silence_threshold=0.02,
            silence_duration=5.0,
            min_audio_duration=3.0,
        ),
        transcription=TranscriptionConfig(
            provider="local",
            model_size="tiny",
            language="en",
        ),
        summary=SummaryConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            daily_summary=False,  # Disable for tests
        ),
        google_docs=GoogleDocsConfig(
            enabled=False,  # Disable for tests
        ),
        storage=StorageConfig(
            base_dir=str(temp_dir),
            audio_dir="audio",
            transcript_dir="transcripts",
            summary_dir="summaries",
            backup_dir="backups",
        ),
        ui=UIConfig(
            system_tray=False,
            web_dashboard=False,
        ),
        debug=True,
        log_level="DEBUG",
    )
    config.ensure_directories()
    return config


@pytest.fixture
def sample_transcript_text():
    """Sample transcript text for testing."""
    return """[10:30:15] Good morning, I need to schedule a meeting with the team.
[10:31:22] Let's discuss the project timeline and deliverables.
[10:32:45] I should also follow up with the client about their feedback.
[10:35:10] The presentation needs to be ready by Friday.
[10:36:30] Don't forget to review the budget proposal."""


@pytest.fixture
def sample_audio_data():
    """Generate sample audio data for testing."""
    import numpy as np

    sample_rate = 16000
    duration = 3  # 3 seconds
    frequency = 440  # A4 note

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3

    return audio_data.astype(np.float32)


@pytest.fixture
def mock_audio_segment(temp_dir):
    """Create a mock audio segment for testing."""
    import wave

    import numpy as np

    from src.audio_capture import AudioSegment

    # Create a test audio file
    audio_file = temp_dir / "test_audio.wav"
    sample_rate = 16000
    duration = 3

    # Generate simple audio
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = (np.sin(2 * np.pi * 440 * t) * 0.3 * 32767).astype(np.int16)

    with wave.open(str(audio_file), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    return AudioSegment(
        file_path=audio_file,
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration=duration,
        sample_rate=sample_rate,
    )
