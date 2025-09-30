#!/usr/bin/env python3
"""
Test script for PyTorch-free installation.
"""

import sys
from pathlib import Path


def test_imports():
    """Test if core packages can be imported."""
    print("Testing PyTorch-free installation...")
    print("-" * 40)
    
    # Core packages that should work without PyTorch
    packages = [
        ("numpy", "NumPy"),
        ("yaml", "PyYAML"),
        ("dotenv", "python-dotenv"),
        ("rich", "Rich"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("sounddevice", "SoundDevice"),
        ("PIL", "Pillow"),
    ]
    
    success_count = 0
    for module, name in packages:
        try:
            __import__(module)
            print(f"✅ {name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
    
    # Test transcription alternatives
    print("\nTesting transcription options:")
    transcription_available = False
    
    try:
        import whisper
        print("✅ OpenAI Whisper (cloud-based)")
        transcription_available = True
    except ImportError:
        print("❌ OpenAI Whisper")
    
    try:
        import faster_whisper
        print("✅ Faster Whisper (local)")
        transcription_available = True
    except ImportError:
        print("❌ Faster Whisper")
    
    if not transcription_available:
        print("⚠️  No transcription backend - will need cloud API")
    
    print(f"\n📊 Result: {success_count}/{len(packages)} core packages working")
    
    if success_count >= 6:
        print("🎉 PyTorch-free installation looks good!")
        return True
    else:
        print("❌ Installation has issues")
        return False


def test_app_modules():
    """Test if app modules can be imported."""
    print("\nTesting app modules:")
    print("-" * 40)
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    modules = [
        ("src.config", "Configuration"),
        ("src.logger", "Logger"),
        ("src.summarization", "Summarization"),
        ("src.google_docs", "Google Docs"),
    ]
    
    success_count = 0
    for module, name in modules:
        try:
            __import__(module)
            print(f"✅ {name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
    
    print(f"\n📊 App modules: {success_count}/{len(modules)} working")
    return success_count >= 3


def main():
    """Run tests."""
    print("🧪 PyTorch-Free Installation Test")
    print("=" * 50)
    
    core_ok = test_imports()
    app_ok = test_app_modules()
    
    print("\n" + "=" * 50)
    if core_ok and app_ok:
        print("🎉 PyTorch-free installation successful!")
        print("\nYou can use the app with cloud-based transcription:")
        print("1. Set OPENAI_API_KEY in .env")
        print("2. Configure transcription provider: 'openai_api'")
        print("3. Run: python -m src.main")
    else:
        print("❌ Installation needs work")
        print("Try: pip install -r requirements-no-torch.txt")
    
    return 0 if (core_ok and app_ok) else 1


if __name__ == "__main__":
    sys.exit(main())