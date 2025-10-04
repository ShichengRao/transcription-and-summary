"""Tests for configuration module."""

from pathlib import Path

import pytest
import yaml

from src.config import (
    AppConfig,
    AudioConfig,
    GoogleDocsConfig,
    StorageConfig,
    SummaryConfig,
    TranscriptionConfig,
    UIConfig,
)


class TestAudioConfig:
    """Tests for AudioConfig."""

    def test_default_values(self):
        """Test default audio configuration values."""
        config = AudioConfig()
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.silence_duration == 5.0
        assert config.min_audio_duration == 3.0
        assert config.silence_threshold == 0.02

    def test_custom_values(self):
        """Test custom audio configuration values."""
        config = AudioConfig(
            sample_rate=44100,
            channels=2,
            silence_duration=10.0,
            min_audio_duration=5.0,
        )
        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.silence_duration == 10.0
        assert config.min_audio_duration == 5.0


class TestAppConfig:
    """Tests for AppConfig."""

    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = AppConfig(
            audio=AudioConfig(),
            transcription=TranscriptionConfig(),
            summary=SummaryConfig(),
            google_docs=GoogleDocsConfig(),
            storage=StorageConfig(),
            ui=UIConfig(),
        )
        assert config.audio is not None
        assert config.transcription is not None
        assert config.summary is not None
        assert config.google_docs is not None
        assert config.storage is not None
        assert config.ui is not None

    def test_save_and_load_config(self, temp_dir):
        """Test saving and loading configuration."""
        config_path = temp_dir / "test_config.yaml"

        # Create and save config
        original_config = AppConfig(
            audio=AudioConfig(sample_rate=44100),
            transcription=TranscriptionConfig(model_size="base"),
            summary=SummaryConfig(provider="claude"),
            google_docs=GoogleDocsConfig(enabled=False),
            storage=StorageConfig(base_dir=str(temp_dir)),
            ui=UIConfig(web_port=9090),
        )
        original_config.save(str(config_path))

        # Load config
        assert config_path.exists()
        loaded_config = AppConfig.load(str(config_path))

        # Verify values
        assert loaded_config.audio.sample_rate == 44100
        assert loaded_config.transcription.model_size == "base"
        assert loaded_config.summary.provider == "claude"
        assert loaded_config.google_docs.enabled is False
        assert loaded_config.ui.web_port == 9090

    def test_get_storage_paths(self, test_config):
        """Test getting storage paths."""
        paths = test_config.get_storage_paths()

        assert "base" in paths
        assert "audio" in paths
        assert "transcripts" in paths
        assert "summaries" in paths
        assert "backups" in paths

        assert isinstance(paths["base"], Path)
        assert isinstance(paths["audio"], Path)

    def test_ensure_directories(self, test_config):
        """Test directory creation."""
        test_config.ensure_directories()

        paths = test_config.get_storage_paths()
        for path in paths.values():
            assert path.exists()
            assert path.is_dir()


class TestTranscriptionConfig:
    """Tests for TranscriptionConfig."""

    def test_default_provider(self):
        """Test default transcription provider."""
        config = TranscriptionConfig()
        assert config.provider == "local"
        assert config.model_size == "base"
        assert config.language == "en"

    def test_custom_provider(self):
        """Test custom transcription provider."""
        config = TranscriptionConfig(provider="openai_api", model_size="large", language="es")
        assert config.provider == "openai_api"
        assert config.model_size == "large"
        assert config.language == "es"


class TestSummaryConfig:
    """Tests for SummaryConfig."""

    def test_default_values(self):
        """Test default summary configuration."""
        config = SummaryConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-3.5-turbo"
        assert config.daily_summary is True
        assert config.summary_time == "23:00"

    def test_custom_values(self):
        """Test custom summary configuration."""
        config = SummaryConfig(
            provider="claude",
            model="claude-3-sonnet-20240229",
            daily_summary=False,
            hourly_summary=True,
        )
        assert config.provider == "claude"
        assert config.model == "claude-3-sonnet-20240229"
        assert config.daily_summary is False
        assert config.hourly_summary is True
