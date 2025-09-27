"""Simple test script to verify the basic functionality."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import AppConfig, load_environment_variables
from src.logger import setup_logger


def test_configuration():
    """Test configuration loading."""
    print("Testing configuration...")
    try:
        config = AppConfig.load()
        print("✅ Configuration loaded successfully")
        print(f"  - Audio sample rate: {config.audio.sample_rate}")
        print(f"  - Transcription model: {config.transcription.model_size}")
        print(f"  - Summary provider: {config.summary.provider}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_logger():
    """Test logging setup."""
    print("\nTesting logger...")
    try:
        logger = setup_logger(level="INFO")
        logger.info("Test log message")
        print("✅ Logger test successful")
        return True
    except Exception as e:
        print(f"❌ Logger test failed: {e}")
        return False


def test_audio_devices():
    """Test audio device detection."""
    print("\nTesting audio devices...")
    try:
        from src.audio_capture import AudioCapture
        from src.config import AudioConfig
        
        audio_config = AudioConfig()
        audio_capture = AudioCapture(audio_config, Path("test_audio"))
        
        devices = audio_capture.get_available_devices()
        print(f"✅ Found {len(devices)} audio devices")
        
        for device in devices[:3]:  # Show first 3 devices
            print(f"  - {device['name']} ({device['channels']} channels)")
        
        return True
    except Exception as e:
        print(f"❌ Audio device test failed: {e}")
        return False


def test_transcription_model():
    """Test transcription model loading."""
    print("\nTesting transcription model...")
    try:
        from src.transcription import TranscriptionService
        from src.config import TranscriptionConfig
        
        config = TranscriptionConfig(model_size="tiny")  # Use smallest model for testing
        service = TranscriptionService(config)
        
        if service.initialize_model():
            print("✅ Transcription model loaded successfully")
            return True
        else:
            print("❌ Failed to load transcription model")
            return False
    except Exception as e:
        print(f"❌ Transcription model test failed: {e}")
        return False


def test_directories():
    """Test directory creation."""
    print("\nTesting directory creation...")
    try:
        config = AppConfig.load()
        config.ensure_directories()
        
        paths = config.get_storage_paths()
        all_exist = True
        
        for name, path in paths.items():
            if path.exists():
                print(f"✅ {name}: {path}")
            else:
                print(f"❌ {name}: {path} (not created)")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Directory test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Running basic functionality tests...\n")
    
    tests = [
        test_configuration,
        test_logger,
        test_directories,
        test_audio_devices,
        test_transcription_model
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(0.5)  # Small delay between tests
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("You may need to install missing dependencies or fix configuration.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())