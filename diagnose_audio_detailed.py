#!/usr/bin/env python3
"""Detailed audio diagnosis script to help debug audio capture issues."""

import numpy as np
import time
from pathlib import Path

def test_audio_import():
    """Test if audio libraries can be imported."""
    print("🔍 Testing audio library imports...")
    
    try:
        import sounddevice as sd
        print("✅ sounddevice imported successfully")
    except ImportError as e:
        print(f"❌ sounddevice import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False
    
    return True

def test_audio_devices():
    """Test available audio devices."""
    print("\n🎤 Testing audio devices...")
    
    try:
        import sounddevice as sd
        
        devices = sd.query_devices()
        print(f"Found {len(devices)} audio devices:")
        
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append((i, device))
                print(f"  [{i}] {device['name']} - {device['max_input_channels']} input channels")
        
        if not input_devices:
            print("❌ No input devices found!")
            return False
        
        # Test default device
        try:
            default_device = sd.default.device
            print(f"Default device: {default_device}")
        except Exception as e:
            print(f"⚠️ Could not get default device: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error querying devices: {e}")
        return False

def test_audio_recording():
    """Test basic audio recording."""
    print("\n🎙️ Testing audio recording...")
    
    try:
        import sounddevice as sd
        import numpy as np
        
        sample_rate = 16000
        duration = 3  # seconds
        
        print(f"Recording {duration} seconds of audio at {sample_rate}Hz...")
        print("Please speak or make noise now!")
        
        # Record audio
        audio_data = sd.rec(int(duration * sample_rate), 
                           samplerate=sample_rate, 
                           channels=1, 
                           dtype='float32')
        sd.wait()  # Wait until recording is finished
        
        # Analyze the recording
        audio_flat = audio_data.flatten()
        rms = np.sqrt(np.mean(audio_flat ** 2))
        max_amplitude = np.max(np.abs(audio_flat))
        
        print(f"✅ Recording completed!")
        print(f"   RMS level: {rms:.6f}")
        print(f"   Max amplitude: {max_amplitude:.6f}")
        print(f"   Samples: {len(audio_flat)}")
        
        # Check if we got any meaningful audio
        if rms < 0.001:
            print("⚠️ Very low audio levels detected - check microphone!")
        elif rms < 0.01:
            print("⚠️ Low audio levels - you may need to speak louder")
        else:
            print("✅ Good audio levels detected")
        
        return True, rms, max_amplitude
        
    except Exception as e:
        print(f"❌ Error during recording: {e}")
        return False, 0, 0

def test_config_thresholds():
    """Test the current configuration thresholds."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from src.config import AppConfig
        
        # Try to load config
        try:
            config = AppConfig.load("config_test.yaml")
            print("✅ Loaded config_test.yaml")
        except:
            try:
                config = AppConfig.load()
                print("✅ Loaded default config")
            except Exception as e:
                print(f"❌ Could not load config: {e}")
                return False
        
        audio_config = config.audio
        print(f"Current audio configuration:")
        print(f"   Silence threshold: {audio_config.silence_threshold}")
        print(f"   Silence duration: {audio_config.silence_duration}s")
        print(f"   Min audio duration: {getattr(audio_config, 'min_audio_duration', 'N/A')}s")
        print(f"   Noise gate threshold: {getattr(audio_config, 'noise_gate_threshold', 'N/A')}")
        print(f"   Sample rate: {audio_config.sample_rate}Hz")
        
        return True, audio_config
        
    except Exception as e:
        print(f"❌ Error testing config: {e}")
        return False, None

def main():
    """Run all diagnostic tests."""
    print("🔧 Audio Capture Diagnostic Tool")
    print("=" * 50)
    
    # Test 1: Import libraries
    if not test_audio_import():
        print("\n❌ Basic imports failed. Install requirements: pip install sounddevice numpy")
        return
    
    # Test 2: Audio devices
    if not test_audio_devices():
        print("\n❌ No audio devices available. Check microphone connection.")
        return
    
    # Test 3: Configuration
    config_ok, audio_config = test_config_thresholds()
    if not config_ok:
        print("\n⚠️ Could not load configuration, using defaults")
        silence_threshold = 0.02
    else:
        silence_threshold = audio_config.silence_threshold
    
    # Test 4: Record audio
    record_ok, rms, max_amp = test_audio_recording()
    if not record_ok:
        print("\n❌ Audio recording failed")
        return
    
    # Analysis
    print(f"\n📊 Analysis:")
    print(f"   Your audio RMS: {rms:.6f}")
    print(f"   Current threshold: {silence_threshold:.6f}")
    
    if rms > silence_threshold:
        print("✅ Your audio level is ABOVE the threshold - should be detected!")
    else:
        ratio = silence_threshold / rms if rms > 0 else float('inf')
        print(f"❌ Your audio level is BELOW the threshold by {ratio:.1f}x")
        print(f"   Suggested threshold: {rms * 0.5:.6f} (50% of your level)")
    
    print(f"\n💡 Recommendations:")
    if rms < silence_threshold:
        print("   1. Speak louder or move closer to microphone")
        print("   2. Check microphone sensitivity/gain settings")
        print(f"   3. Lower silence_threshold to {rms * 0.5:.6f} in config")
    else:
        print("   ✅ Audio levels look good!")
    
    print(f"\n🔧 To fix threshold issues:")
    print(f"   Edit your config file and set:")
    print(f"   silence_threshold: {max(rms * 0.5, 0.005):.6f}")

if __name__ == "__main__":
    main()