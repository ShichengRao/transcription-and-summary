"""Configuration management for the transcription and summary application."""

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class AudioConfig:
    """Audio recording configuration."""

    sample_rate: int = 16000
    channels: int = 1
    chunk_duration: int = 300  # 5 minutes in seconds
    format: str = "wav"
    device_id: Optional[int] = None
    silence_threshold: float = 0.02  # Moderate increase from 0.01 to reduce ambient noise sensitivity
    silence_duration: float = 5.0  # Increased to 5 seconds to keep natural pauses in one file
    min_audio_duration: float = 3.0  # Minimum 3 seconds to filter out very short clips
    noise_gate_threshold: float = 0.015  # Additional noise gate threshold (lower than silence_threshold)


@dataclass
class TranscriptionConfig:
    """Transcription engine configuration."""

    provider: str = "local"  # local, openai_api, disabled
    model_size: str = "base"  # tiny, base, small, medium, large
    language: str = "en"
    compute_type: str = "float32"  # float32 for better compatibility, float16 for speed
    device: str = "auto"  # auto, cpu, cuda
    beam_size: int = 5
    temperature: float = 0.0


@dataclass
class SummaryConfig:
    """Summary generation configuration."""

    provider: str = "openai"  # openai, claude, local
    model: str = (
        "gpt-3.5-turbo"  # For OpenAI: gpt-3.5-turbo, gpt-4, etc. For Claude: claude-3-haiku-20240307, claude-3-sonnet-20240229, claude-3-opus-20240229
    )
    max_tokens: int = 500
    temperature: float = 0.3
    daily_summary: bool = True
    hourly_summary: bool = False
    summary_time: str = "23:00"  # Daily summary time


@dataclass
class GoogleDocsConfig:
    """Google Docs integration configuration."""

    enabled: bool = True
    credentials_path: str = "credentials.json"
    token_path: str = "token.json"
    folder_name: str = "Transcription Summaries"
    document_template: str = "Daily Transcript - {date}"


@dataclass
class StorageConfig:
    """Local storage configuration."""

    base_dir: str = "transcripts"
    audio_dir: str = "audio"
    transcript_dir: str = "transcripts"
    summary_dir: str = "summaries"
    backup_dir: str = "backups"
    max_audio_age_days: int = 7
    max_transcript_age_days: int = 365


@dataclass
class UIConfig:
    """User interface configuration."""

    system_tray: bool = True
    auto_start: bool = True
    notifications: bool = True
    web_dashboard: bool = True
    web_host: str = "127.0.0.1"
    web_port: int = 8080


@dataclass
class AppConfig:
    """Main application configuration."""

    audio: AudioConfig
    transcription: TranscriptionConfig
    summary: SummaryConfig
    google_docs: GoogleDocsConfig
    storage: StorageConfig
    ui: UIConfig
    debug: bool = False
    log_level: str = "INFO"

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AppConfig":
        """Load configuration from file or create default."""
        if config_path is None:
            config_path = "config.yaml"

        config_file = Path(config_path)

        if config_file.exists():
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)

            return cls(
                audio=AudioConfig(**config_data.get("audio", {})),
                transcription=TranscriptionConfig(**config_data.get("transcription", {})),
                summary=SummaryConfig(**config_data.get("summary", {})),
                google_docs=GoogleDocsConfig(**config_data.get("google_docs", {})),
                storage=StorageConfig(**config_data.get("storage", {})),
                ui=UIConfig(**config_data.get("ui", {})),
                debug=config_data.get("debug", False),
                log_level=config_data.get("log_level", "INFO"),
            )
        else:
            # Create default configuration
            default_config = cls(
                audio=AudioConfig(),
                transcription=TranscriptionConfig(),
                summary=SummaryConfig(),
                google_docs=GoogleDocsConfig(),
                storage=StorageConfig(),
                ui=UIConfig(),
            )
            default_config.save(config_path)
            return default_config

    def save(self, config_path: str = "config.yaml") -> None:
        """Save configuration to file."""
        config_dict = asdict(self)

        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

    def get_storage_paths(self) -> Dict[str, Path]:
        """Get all storage paths as Path objects."""
        base = Path(self.storage.base_dir)
        return {
            "base": base,
            "audio": base / self.storage.audio_dir,
            "transcripts": base / self.storage.transcript_dir,
            "summaries": base / self.storage.summary_dir,
            "backups": base / self.storage.backup_dir,
        }

    def ensure_directories(self) -> None:
        """Create all necessary directories."""
        paths = self.get_storage_paths()
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)


def load_environment_variables() -> None:
    """Load environment variables from .env file."""
    from dotenv import load_dotenv

    load_dotenv()


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment."""
    return os.getenv("OPENAI_API_KEY")


def get_claude_api_key() -> Optional[str]:
    """Get Claude API key from environment."""
    return os.getenv("CLAUDE_API_KEY")


def get_google_credentials_path() -> str:
    """Get Google credentials path from environment or default."""
    return os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
