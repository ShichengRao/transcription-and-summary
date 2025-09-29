#!/usr/bin/env python3
"""
PyTorch-free installer for systems that can't install PyTorch.
Uses cloud-based transcription instead of local processing.
"""

import subprocess
import sys
import platform


def run_command(cmd):
    """Run a command and return success status."""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Success")
            return True
        else:
            print(f"❌ Failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_python():
    """Check Python version."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    
    print("✅ Python version compatible")
    return True


def install_system_deps():
    """Install system dependencies if on macOS."""
    if platform.system() == "Darwin":
        print("\n📦 Installing macOS system dependencies...")
        
        # Check if brew is available
        success, _, _ = subprocess.run("which brew", shell=True, capture_output=True, text=True)
        if success != 0:
            print("⚠️  Homebrew not found - please install manually:")
            print("  brew install ffmpeg portaudio")
            return True
        
        deps = ["ffmpeg", "portaudio"]
        for dep in deps:
            print(f"Installing {dep}...")
            if not run_command(f"brew install {dep}"):
                print(f"⚠️  Failed to install {dep}, continuing...")
    
    return True


def install_requirements():
    """Install Python requirements without PyTorch."""
    print("\n📋 Installing Python requirements (PyTorch-free)...")
    
    # Upgrade pip first
    if not run_command("pip install --upgrade pip"):
        print("⚠️  Failed to upgrade pip, continuing...")
    
    # Install requirements
    if run_command("pip install -r requirements-no-torch.txt"):
        print("✅ Requirements installed successfully!")
        return True
    else:
        print("❌ Failed to install requirements")
        return False


def test_installation():
    """Test the installation."""
    print("\n🧪 Testing installation...")
    
    test_imports = [
        ("numpy", "NumPy"),
        ("yaml", "PyYAML"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("sounddevice", "SoundDevice"),
        ("whisper", "OpenAI Whisper"),
        ("rich", "Rich"),
    ]
    
    success_count = 0
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name}")
            success_count += 1
        except ImportError:
            print(f"❌ {name}")
    
    print(f"\n📊 {success_count}/{len(test_imports)} components working")
    
    if success_count >= 5:
        print("🎉 Installation successful!")
        return True
    else:
        print("❌ Installation has issues")
        return False


def create_config():
    """Create a configuration optimized for cloud transcription."""
    config_content = """# Configuration for PyTorch-free installation
audio:
  sample_rate: 16000
  channels: 1
  chunk_duration: 300  # 5 minutes
  format: "wav"
  device_id: null
  silence_threshold: 0.01
  silence_duration: 2.0

transcription:
  # Use cloud-based transcription instead of local
  provider: "openai_api"  # Use OpenAI's Whisper API
  model_size: "base"
  language: "en"
  device: "cpu"
  beam_size: 5
  temperature: 0.0

summary:
  provider: "openai"  # or "claude"
  model: "gpt-3.5-turbo"
  max_tokens: 500
  temperature: 0.3
  daily_summary: true
  hourly_summary: false
  summary_time: "23:00"

google_docs:
  enabled: true
  credentials_path: "credentials.json"
  token_path: "token.json"
  folder_name: "Transcription Summaries"
  document_template: "Daily Transcript - {date}"

storage:
  base_dir: "transcripts"
  audio_dir: "audio"
  transcript_dir: "transcripts"
  summary_dir: "summaries"
  backup_dir: "backups"
  max_audio_age_days: 7
  max_transcript_age_days: 365

ui:
  system_tray: true
  auto_start: true
  notifications: true
  web_dashboard: false
  web_port: 8080

debug: false
log_level: "INFO"
"""
    
    try:
        with open("config-no-torch.yaml", "w") as f:
            f.write(config_content)
        print("✅ Created config-no-torch.yaml")
        return True
    except Exception as e:
        print(f"❌ Failed to create config: {e}")
        return False


def main():
    """Main installation process."""
    print("🚀 PyTorch-Free Transcription App Installer")
    print("=" * 50)
    print("This installer skips PyTorch and uses cloud-based transcription")
    print()
    
    if not check_python():
        sys.exit(1)
    
    print("This installer will:")
    print("1. Install system dependencies (macOS only)")
    print("2. Install Python requirements (without PyTorch)")
    print("3. Use OpenAI Whisper API for transcription")
    print("4. Test the installation")
    print("5. Create optimized configuration")
    
    proceed = input("\nProceed? (y/N): ").lower().strip()
    if proceed != 'y':
        print("Installation cancelled")
        sys.exit(0)
    
    # Install system dependencies
    install_system_deps()
    
    # Install Python requirements
    if not install_requirements():
        print("❌ Installation failed")
        sys.exit(1)
    
    # Test installation
    if test_installation():
        print("\n🎉 Installation completed successfully!")
        
        # Create config
        create_config()
        
        print("\n📋 Next steps:")
        print("1. cp .env.example .env")
        print("2. Edit .env and add your API keys:")
        print("   - OPENAI_API_KEY (required for transcription AND summarization)")
        print("   - CLAUDE_API_KEY (optional, alternative to OpenAI for summaries)")
        print("3. Use config-no-torch.yaml: cp config-no-torch.yaml config.yaml")
        print("4. Test: python -m src.cli status")
        print("5. Run: python -m src.main")
        
        print("\n💡 Note: This setup uses OpenAI's Whisper API for transcription")
        print("   instead of local processing. You'll need an OpenAI API key.")
        
    else:
        print("\n❌ Installation completed with issues")
        print("Try running: python diagnose_python.py")


if __name__ == "__main__":
    main()