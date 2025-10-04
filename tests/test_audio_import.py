#!/usr/bin/env python3
"""Test script for audio import functionality."""

import sys
from datetime import datetime
from pathlib import Path


def test_filename_parsing():
    """Test the filename parsing functionality."""
    print("🔍 Testing Filename Parsing")
    print("=" * 40)

    try:
        from src.automation import TranscriptionApp
        from src.config import AppConfig
        from src.web_ui import WebUI

        # Create a dummy web UI instance for testing
        config = AppConfig.load()
        app = TranscriptionApp(config)
        web_ui = WebUI(app)

        # Test various filename patterns
        test_filenames = [
            "Recording 2024-09-30 14:30:15.m4a",
            "Recording 2024-09-30 14:30.m4a",
            "Voice Memo 2024-09-30.wav",
            "20240930_143015.wav",
            "20240930_1430.mp3",
            "random_filename.mp3",
            "meeting_notes.wav",
            "2024-09-30_important_call.m4a",
        ]

        print("Testing filename patterns:")
        for filename in test_filenames:
            timestamp = web_ui._extract_timestamp_from_filename(filename)
            print(f"  {filename:<35} → {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_supported_formats():
    """Test supported audio formats."""
    print("\n🎵 Supported Audio Formats")
    print("=" * 40)

    supported_formats = {".wav", ".mp3", ".m4a", ".mp4", ".flac", ".ogg", ".webm"}

    print("Supported formats:")
    for fmt in sorted(supported_formats):
        print(f"  ✅ {fmt}")

    print("\nCommon phone recording formats:")
    phone_formats = {
        "iPhone Voice Memos": ".m4a",
        "Android Voice Recorder": ".mp3 or .wav",
        "WhatsApp Voice Messages": ".ogg",
        "Zoom Recordings": ".mp4 or .wav",
        "Teams Recordings": ".mp4",
    }

    for app, fmt in phone_formats.items():
        supported = any(f in fmt for f in supported_formats)
        status = "✅" if supported else "❌"
        print(f"  {status} {app:<25} → {fmt}")


def create_sample_audio_file():
    """Create a sample audio file for testing."""
    print("\n🎤 Creating Sample Audio File")
    print("=" * 40)

    try:
        import wave

        import numpy as np

        # Create a simple test audio file
        sample_rate = 16000
        duration = 3  # 3 seconds
        frequency = 440  # A4 note

        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.3

        # Convert to 16-bit integers
        audio_data = (audio_data * 32767).astype(np.int16)

        # Save as WAV file
        test_file = Path("test_recording_2024-09-30_14-30-15.wav")

        with wave.open(str(test_file), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        print(f"✅ Created test audio file: {test_file}")
        print(f"   Duration: {duration}s")
        print(f"   Sample rate: {sample_rate}Hz")
        print(f"   File size: {test_file.stat().st_size} bytes")

        return test_file

    except Exception as e:
        print(f"❌ Failed to create test audio file: {e}")
        return None


def main():
    """Run all tests."""
    print("🎙️ Audio Import Functionality Tests")
    print("=" * 50)

    success = True

    # Test filename parsing
    if not test_filename_parsing():
        success = False

    # Test supported formats
    test_supported_formats()

    # Create sample file
    sample_file = create_sample_audio_file()

    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
        print("\n💡 To test audio import:")
        print("   1. Start the application: python -m src.main")
        print("   2. Go to http://127.0.0.1:8080")
        print("   3. Use the 'Import Audio Files' section")
        if sample_file:
            print(f"   4. Try uploading the test file: {sample_file}")
        print("\n📱 Phone recording tips:")
        print("   - Use descriptive filenames with dates")
        print("   - Record in quiet environments")
        print("   - Keep recordings under 10 minutes for best results")
    else:
        print("❌ Some tests failed!")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
