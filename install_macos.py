#!/usr/bin/env python3
"""
macOS-specific installer that handles PyTorch installation issues.
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


def check_macos():
    """Check if running on macOS."""
    if platform.system() != "Darwin":
        print("❌ This script is for macOS only")
        return False
    
    print(f"✅ macOS detected: {platform.mac_ver()[0]}")
    
    # Check for Apple Silicon
    machine = platform.machine()
    if machine in ["arm64", "aarch64"]:
        print("✅ Apple Silicon (M1/M2/M3) detected")
    else:
        print("✅ Intel Mac detected")
    
    return True


def install_system_deps():
    """Install system dependencies via Homebrew."""
    print("\n📦 Installing system dependencies...")
    
    # Check if brew is installed
    if not run_command("which brew"):
        print("Installing Homebrew...")
        install_brew_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        if not run_command(install_brew_cmd):
            print("❌ Failed to install Homebrew")
            return False
    
    # Install dependencies
    deps = ["ffmpeg", "portaudio"]
    for dep in deps:
        if not run_command(f"brew install {dep}"):
            print(f"⚠️  Failed to install {dep}, continuing...")
    
    return True


def install_pytorch_macos():
    """Install PyTorch on macOS using methods that actually work."""
    print("\n🔥 Installing PyTorch for macOS...")
    
    # Method 1: Standard pip installation (usually works best on macOS)
    methods = [
        "pip install torch torchaudio",
        "pip install torch==2.0.1 torchaudio==2.0.2",
        "pip install torch==1.13.1 torchaudio==0.13.1",
        "conda install pytorch torchaudio -c pytorch -y"  # If conda is available
    ]
    
    for method in methods:
        print(f"\nTrying method: {method}")
        if run_command(method):
            print("✅ PyTorch installed successfully!")
            return True
        print("❌ Method failed, trying next...")
    
    print("❌ All PyTorch installation methods failed")
    return False


def install_app_requirements():
    """Install application requirements."""
    print("\n📋 Installing application requirements...")
    
    # Try different requirement files in order of preference for macOS
    req_files = [
        "requirements-cpu.txt",
        "requirements-minimal.txt"
    ]
    
    for req_file in req_files:
        print(f"\nTrying: {req_file}")
        if run_command(f"pip install -r {req_file}"):
            print(f"✅ Installed requirements from {req_file}")
            return True
        print(f"❌ Failed to install from {req_file}")
    
    return False


def install_transcription():
    """Install transcription components."""
    print("\n🎤 Installing transcription support...")
    
    # Try faster-whisper first, then fallback to openai-whisper
    if run_command("pip install faster-whisper"):
        print("✅ faster-whisper installed")
        return True
    elif run_command("pip install openai-whisper"):
        print("✅ openai-whisper installed (fallback)")
        return True
    else:
        print("❌ Could not install transcription support")
        return False


def test_installation():
    """Test if the installation worked."""
    print("\n🧪 Testing installation...")
    
    test_imports = [
        ("numpy", "NumPy"),
        ("yaml", "PyYAML"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("sounddevice", "SoundDevice"),
    ]
    
    success_count = 0
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name}")
            success_count += 1
        except ImportError:
            print(f"❌ {name}")
    
    # Test transcription
    transcription_available = False
    for module in ["faster_whisper", "whisper"]:
        try:
            __import__(module)
            print(f"✅ Transcription ({module})")
            transcription_available = True
            break
        except ImportError:
            continue
    
    if not transcription_available:
        print("⚠️  No transcription backend available")
    
    print(f"\n📊 {success_count}/{len(test_imports)} core components working")
    
    if success_count >= 4:  # At least core components
        print("🎉 Installation successful!")
        return True
    else:
        print("❌ Installation has issues")
        return False


def main():
    """Main installation process for macOS."""
    print("🍎 macOS Transcription App Installer")
    print("=" * 50)
    
    if not check_macos():
        sys.exit(1)
    
    print("\nThis installer will:")
    print("1. Install system dependencies (ffmpeg, portaudio)")
    print("2. Install PyTorch using macOS-compatible methods")
    print("3. Install application requirements")
    print("4. Test the installation")
    
    proceed = input("\nProceed? (y/N): ").lower().strip()
    if proceed != 'y':
        print("Installation cancelled")
        sys.exit(0)
    
    # Step 1: System dependencies
    if not install_system_deps():
        print("⚠️  System dependencies failed, but continuing...")
    
    # Step 2: PyTorch
    pytorch_success = install_pytorch_macos()
    
    # Step 3: App requirements
    if not install_app_requirements():
        print("❌ Failed to install application requirements")
        sys.exit(1)
    
    # Step 4: Transcription (optional)
    if pytorch_success:
        install_transcription()
    else:
        print("⚠️  Skipping transcription support due to PyTorch issues")
    
    # Step 5: Test
    if test_installation():
        print("\n🎉 Installation completed successfully!")
        print("\nNext steps:")
        print("1. cp .env.example .env")
        print("2. Edit .env with your API keys")
        print("3. python -m src.cli status")
        print("4. python -m src.main")
    else:
        print("\n❌ Installation completed with issues")
        print("Try running: python test_installation.py")


if __name__ == "__main__":
    main()