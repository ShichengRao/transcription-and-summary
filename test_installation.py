#!/usr/bin/env python3
"""
Test script to validate installation and check which components are working.
"""

import sys
import importlib
from pathlib import Path


def test_import(module_name, package_name=None, optional=False):
    """Test if a module can be imported."""
    try:
        importlib.import_module(module_name)
        status = "✅"
        message = f"{package_name or module_name}"
    except ImportError as e:
        if optional:
            status = "⚠️ "
            message = f"{package_name or module_name} (optional - {str(e)[:50]}...)"
        else:
            status = "❌"
            message = f"{package_name or module_name} - {str(e)[:50]}..."
    
    print(f"{status} {message}")
    return status == "✅"


def test_core_dependencies():
    """Test core required dependencies."""
    print("Testing Core Dependencies:")
    print("-" * 40)
    
    core_deps = [
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("yaml", "PyYAML"),
        ("dotenv", "python-dotenv"),
        ("apscheduler", "APScheduler"),
        ("rich", "Rich"),
        ("PIL", "Pillow"),
    ]
    
    all_good = True
    for module, name in core_deps:
        if not test_import(module, name):
            all_good = False
    
    return all_good


def test_audio_dependencies():
    """Test audio-related dependencies."""
    print("\nTesting Audio Dependencies:")
    print("-" * 40)
    
    audio_deps = [
        ("sounddevice", "sounddevice"),
    ]
    
    all_good = True
    for module, name in audio_deps:
        if not test_import(module, name):
            all_good = False
    
    return all_good


def test_transcription_dependencies():
    """Test transcription-related dependencies."""
    print("\nTesting Transcription Dependencies:")
    print("-" * 40)
    
    transcription_deps = [
        ("faster_whisper", "faster-whisper", True),
        ("whisper", "openai-whisper", True),
        ("torch", "PyTorch", True),
        ("torchaudio", "TorchAudio", True),
    ]
    
    has_transcription = False
    for module, name, optional in transcription_deps:
        if test_import(module, name, optional):
            has_transcription = True
    
    if not has_transcription:
        print("⚠️  No transcription backend available - AI summarization only")
    
    return has_transcription


def test_ai_dependencies():
    """Test AI provider dependencies."""
    print("\nTesting AI Provider Dependencies:")
    print("-" * 40)
    
    ai_deps = [
        ("openai", "OpenAI", True),
        ("anthropic", "Anthropic (Claude)", True),
    ]
    
    has_ai = False
    for module, name, optional in ai_deps:
        if test_import(module, name, optional):
            has_ai = True
    
    if not has_ai:
        print("❌ No AI provider available - summaries will not work")
    
    return has_ai


def test_google_dependencies():
    """Test Google API dependencies."""
    print("\nTesting Google API Dependencies:")
    print("-" * 40)
    
    google_deps = [
        ("google.auth", "google-auth", True),
        ("googleapiclient", "google-api-python-client", True),
        ("google_auth_oauthlib", "google-auth-oauthlib", True),
    ]
    
    has_google = True
    for module, name, optional in google_deps:
        if not test_import(module, name, optional):
            has_google = False
    
    return has_google


def test_ui_dependencies():
    """Test UI-related dependencies."""
    print("\nTesting UI Dependencies:")
    print("-" * 40)
    
    ui_deps = [
        ("pystray", "pystray", True),
    ]
    
    has_ui = True
    for module, name, optional in ui_deps:
        if not test_import(module, name, optional):
            has_ui = False
    
    return has_ui


def test_app_imports():
    """Test if the app modules can be imported."""
    print("\nTesting App Modules:")
    print("-" * 40)
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    app_modules = [
        ("src.config", "Configuration"),
        ("src.logger", "Logger"),
        ("src.audio_capture", "Audio Capture"),
        ("src.transcription", "Transcription Service"),
        ("src.summarization", "Summarization Service"),
        ("src.google_docs", "Google Docs Integration"),
        ("src.automation", "Automation"),
        ("src.cli", "CLI"),
        ("src.main", "Main App"),
    ]
    
    all_good = True
    for module, name in app_modules:
        if not test_import(module, name):
            all_good = False
    
    return all_good


def print_summary(results):
    """Print installation summary."""
    print("\n" + "=" * 50)
    print("INSTALLATION SUMMARY")
    print("=" * 50)
    
    core_ok, audio_ok, transcription_ok, ai_ok, google_ok, ui_ok, app_ok = results
    
    if core_ok and audio_ok and ai_ok and app_ok:
        print("🎉 Installation successful!")
        
        capabilities = []
        if transcription_ok:
            capabilities.append("Local transcription")
        if ai_ok:
            capabilities.append("AI summarization")
        if google_ok:
            capabilities.append("Google Docs sync")
        if ui_ok:
            capabilities.append("System tray UI")
        
        print(f"Available capabilities: {', '.join(capabilities)}")
        
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Run: python -m src.cli status")
        print("3. Run: python -m src.main")
        
    else:
        print("❌ Installation has issues")
        
        if not core_ok:
            print("- Core dependencies missing")
        if not audio_ok:
            print("- Audio dependencies missing")
        if not ai_ok:
            print("- No AI provider available")
        if not app_ok:
            print("- App modules have import errors")
        
        print("\nTroubleshooting:")
        print("- Try: pip install -r requirements-minimal.txt")
        print("- Check Python version (3.8-3.11 recommended)")
        print("- See SETUP.md for detailed instructions")


def main():
    """Run all installation tests."""
    print("🔍 Testing Installation")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Run all tests
    results = (
        test_core_dependencies(),
        test_audio_dependencies(),
        test_transcription_dependencies(),
        test_ai_dependencies(),
        test_google_dependencies(),
        test_ui_dependencies(),
        test_app_imports()
    )
    
    # Print summary
    print_summary(results)
    
    # Return appropriate exit code
    core_ok, audio_ok, _, ai_ok, _, _, app_ok = results
    if core_ok and audio_ok and ai_ok and app_ok:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())