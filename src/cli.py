"""Command-line interface for the transcription application."""

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Fix OpenMP and Intel MKL warnings
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["MKL_THREADING_LAYER"] = "GNU"

from .automation import TranscriptionApp
from .config import AppConfig, load_environment_variables
from .google_docs import GoogleDocsService
from .logger import setup_logger
from .summarization import SummarizationService
from .transcription import TranscriptionService


def cmd_test_audio():
    """Test audio capture functionality."""
    config = AppConfig.load()
    logger = setup_logger(level="INFO")

    from .audio_capture import AudioCapture

    audio_capture = AudioCapture(config.audio, Path("test_audio"))

    # List available devices
    devices = audio_capture.get_available_devices()
    print("Available audio devices:")
    for device in devices:
        print(f"  {device['id']}: {device['name']} ({device['channels']} channels)")

    # Test default device
    if audio_capture.test_device():
        print("✅ Default audio device is working")
    else:
        print("❌ Default audio device test failed")


def cmd_test_transcription(audio_file: str):
    """Test transcription with an audio file."""
    config = AppConfig.load()
    logger = setup_logger(level="INFO")

    transcription_service = TranscriptionService(config.transcription)

    audio_path = Path(audio_file)
    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return 1

    print(f"Transcribing: {audio_file}")
    result = transcription_service.transcribe_file(audio_path)

    if result:
        print("✅ Transcription successful")
        print(f"Language: {result.language}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"Text: {result.text}")
    else:
        print("❌ Transcription failed")
        return 1


def cmd_test_summary(text_file: str):
    """Test summarization with a text file."""
    config = AppConfig.load()
    load_environment_variables()
    logger = setup_logger(level="INFO")

    summarization_service = SummarizationService(config.summary)

    text_path = Path(text_file)
    if not text_path.exists():
        print(f"❌ Text file not found: {text_file}")
        return 1

    with open(text_path, "r", encoding="utf-8") as f:
        text_content = f.read()

    print(f"Generating summary for: {text_file}")
    print(f"Using provider: {config.summary.provider}")
    print(f"Using model: {config.summary.model}")

    summary = summarization_service.generate_daily_summary(text_content, date.today())

    if summary:
        print("✅ Summary generation successful")
        print(f"Word count: {summary.word_count}")
        print(f"Key topics: {', '.join(summary.key_topics)}")
        print(f"Summary: {summary.summary}")
        if summary.action_items:
            print(f"Action items: {', '.join(summary.action_items)}")
    else:
        print("❌ Summary generation failed")
        return 1


def cmd_test_google_docs():
    """Test Google Docs integration."""
    config = AppConfig.load()
    load_environment_variables()
    logger = setup_logger(level="INFO")

    google_docs_service = GoogleDocsService(config.google_docs)

    if google_docs_service.test_connection():
        print("✅ Google Docs connection successful")

        # List recent documents
        docs = google_docs_service.list_documents(limit=5)
        if docs:
            print("Recent documents:")
            for doc in docs:
                print(f"  - {doc['name']} (Modified: {doc['modifiedTime']})")
        else:
            print("No documents found")
    else:
        print("❌ Google Docs connection failed")
        return 1


def cmd_generate_summary(target_date: str = None):
    """Generate summary for a specific date."""
    config = AppConfig.load()
    load_environment_variables()
    logger = setup_logger(level="INFO")

    if target_date:
        try:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Invalid date format: {target_date}. Use YYYY-MM-DD")
            return 1
    else:
        date_obj = date.today() - timedelta(days=1)

    app = TranscriptionApp(config)

    if app.force_daily_summary(date_obj):
        print(f"✅ Daily summary generated for {date_obj}")
    else:
        print(f"❌ Failed to generate daily summary for {date_obj}")
        return 1


def cmd_process_audio():
    """Process any pending audio files."""
    config = AppConfig.load()
    load_environment_variables()
    logger = setup_logger(level="INFO")

    print("Processing pending audio files...")

    # Look for audio files in the audio directory
    audio_dir = config.get_storage_paths()["audio"]
    if not audio_dir.exists():
        print("❌ No audio directory found")
        return 1

    audio_files = list(audio_dir.glob("*.wav"))
    if not audio_files:
        print("✅ No pending audio files to process")
        return 0

    print(f"Found {len(audio_files)} audio files to process")

    # Initialize transcription service
    from .transcription import TranscriptionService

    transcription_service = TranscriptionService(config.transcription)

    if not transcription_service.start_processing():
        print("❌ Failed to start transcription service")
        return 1

    # Process each file
    processed = 0
    for audio_file in audio_files:
        print(f"Processing: {audio_file.name}")
        result = transcription_service.transcribe_file(audio_file)

        if result:
            print(f"✅ Transcribed: {result.text[:100]}...")
            # Clean up the audio file
            audio_file.unlink()
            processed += 1
        else:
            print(f"❌ Failed to transcribe: {audio_file.name}")

    transcription_service.stop_processing()
    print(f"✅ Processed {processed}/{len(audio_files)} audio files")
    return 0


def cmd_run():
    """Run the main application."""
    from .main import main

    return main()


def cmd_status():
    """Show application status."""
    config = AppConfig.load()

    print("Configuration Status:")
    print(f"  Audio device: {config.audio.device_id or 'Default'}")
    print(f"  Transcription model: {config.transcription.model_size}")
    print(f"  Summary provider: {config.summary.provider}")
    print(f"  Summary model: {config.summary.model}")
    print(f"  Google Docs: {'Enabled' if config.google_docs.enabled else 'Disabled'}")

    # Check API keys
    load_environment_variables()
    print("\nAPI Key Status:")
    if config.summary.provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        print(f"  OpenAI API Key: {'✅ Set' if openai_key else '❌ Missing'}")
    elif config.summary.provider == "claude":
        claude_key = os.getenv("CLAUDE_API_KEY")
        print(f"  Claude API Key: {'✅ Set' if claude_key else '❌ Missing'}")

    # Check storage directories
    paths = config.get_storage_paths()
    print("\nStorage Directories:")
    for name, path in paths.items():
        exists = "✅" if path.exists() else "❌"
        print(f"  {name}: {path} {exists}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Transcription and Summary Application CLI", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    subparsers.add_parser("run", help="Run the main application")

    # Test commands
    test_parser = subparsers.add_parser("test", help="Test various components")
    test_subparsers = test_parser.add_subparsers(dest="test_command")

    test_subparsers.add_parser("audio", help="Test audio capture")

    transcription_parser = test_subparsers.add_parser("transcription", help="Test transcription")
    transcription_parser.add_argument("audio_file", help="Path to audio file")

    summary_parser = test_subparsers.add_parser("summary", help="Test summarization")
    summary_parser.add_argument("text_file", help="Path to text file")

    test_subparsers.add_parser("google-docs", help="Test Google Docs integration")

    # Generate summary command
    summary_cmd_parser = subparsers.add_parser("generate-summary", help="Generate summary for a date")
    summary_cmd_parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: yesterday)")

    # Process audio command
    subparsers.add_parser("process-audio", help="Process any pending audio files")

    # Status command
    subparsers.add_parser("status", help="Show application status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "run":
            return cmd_run()
        elif args.command == "test":
            if args.test_command == "audio":
                return cmd_test_audio()
            elif args.test_command == "transcription":
                return cmd_test_transcription(args.audio_file)
            elif args.test_command == "summary":
                return cmd_test_summary(args.text_file)
            elif args.test_command == "google-docs":
                return cmd_test_google_docs()
            else:
                test_parser.print_help()
                return 1
        elif args.command == "generate-summary":
            return cmd_generate_summary(args.date)
        elif args.command == "process-audio":
            return cmd_process_audio()
        elif args.command == "status":
            return cmd_status()
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
