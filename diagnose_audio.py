#!/usr/bin/env python3
"""Diagnostic script to check audio setup and identify issues."""

import sys
import time
import numpy as np
from pathlib import Path

def test_imports():
    """Test that required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import sounddevice as sd
        print("✅ sounddevice imported successfully")
    except ImportError as e:
        print(f"❌ sounddevice import failed: {e}")
        return False
    
    try:
        from src.config import AppConfig
        print("✅ Config module imported successfully")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    return True

def list_audio_devices():
    """List all available audio input devices."""
    print("\n🎤 Available audio input devices:")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                is_default = i == sd.default.device[0] if sd.default.device[0] is not None else False
                default_marker = " (DEFAULT)" if is_default else ""
                print(f"  {i}: {device['name']}{default_marker}")
                print(f"     Channels: {device['max_input_channels']}, Sample Rate: {device['default_samplerate']}")
                input_devices.append(i)
        
        if not input_devices:
            print("❌ No input devices found!")
            return None
        
        return input_devices[0] if input_devices else None
        
    except Exception as e:
        print(f"❌ Error listing devices: {e}")
        return None

def test_microphone(device_id=None, duration=3):
    """Test microphone recording for a few seconds."""
    print(f"\n🎙️  Testing microphone recording (device {device_id}) for {duration} seconds...")
    
    try:
        import sounddevice as sd
        
        # Record audio
        sample_rate = 16000
        audio_data = sd.rec(
            int(duration * sample_rate), 
            samplerate=sample_rate, 
            channels=1, 
            device=device_id,
            dtype=np.float32
        )
        sd.wait()  # Wait for recording to complete
        
        # Analyze the recording
        rms = np.sqrt(np.mean(audio_data ** 2))
        max_amplitude = np.max(np.abs(audio_data))
        
        print(f"✅ Recording completed!")
        print(f"   RMS level: {rms:.6f}")
        print(f"   Max amplitude: {max_amplitude:.6f}")
        
        if rms < 0.001:
            print("⚠️  Very low audio level detected. Check:")
            print("   - Microphone is connected and working")
            print("   - Microphone permissions are granted")
            print("   - Correct input device is selected")
        elif rms > 0.01:
            print("✅ Good audio level detected!")
        else:
            print("⚠️  Low audio level. May need to adjust microphone gain.")
        
        return True
        
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\n⚙️  Testing configuration...")
    
    try:
        from src.config import AppConfig
        config = AppConfig.load()
        
        print("✅ Configuration loaded successfully")
        print(f"   Audio device: {config.audio.device_id}")
        print(f"   Sample rate: {config.audio.sample_rate}")
        print(f"   Chunk duration: {config.audio.chunk_duration}s")
        print(f"   Silence threshold: {config.audio.silence_threshold}")
        
        return config
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return None

def test_transcription_model():
    """Test if transcription model can be loaded."""
    print("\n🤖 Testing transcription model...")
    
    try:
        from src.transcription import TranscriptionService
        from src.config import TranscriptionConfig
        
        config = TranscriptionConfig()
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

def check_permissions():
    """Check microphone permissions on macOS."""
    print("\n🔒 Checking permissions...")
    
    import platform
    if platform.system() == "Darwin":  # macOS
        print("📋 On macOS, ensure microphone permissions are granted:")
        print("   1. Open System Preferences → Security & Privacy → Privacy")
        print("   2. Select 'Microphone' from the left sidebar")
        print("   3. Check the box next to your terminal app")
        print("   4. Restart your terminal if needed")
    else:
        print("ℹ️  Permission check is macOS-specific")

def main():
    """Run all diagnostic tests."""
    print("🔧 Audio Setup Diagnostics")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please install dependencies:")
        print("   pip install -r requirements.txt")
        return 1
    
    # Check permissions
    check_permissions()
    
    # List devices
    default_device = list_audio_devices()
    
    # Test configuration
    config = test_config()
    
    # Test microphone
    device_to_test = config.audio.device_id if config else default_device
    if not test_microphone(device_to_test):
        return 1
    
    # Test transcription model
    if not test_transcription_model():
        print("\n⚠️  Transcription model failed to load, but audio capture should still work")
    
    print("\n✅ Diagnostics completed!")
    print("\n💡 Recommendations:")
    print("   - If audio levels are low, adjust microphone gain in System Preferences")
    print("   - If no audio detected, check microphone permissions")
    print("   - If transcription fails, check your internet connection for model downloads")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())