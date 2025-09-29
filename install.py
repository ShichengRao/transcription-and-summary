#!/usr/bin/env python3
"""
Smart installer script that detects your system and installs appropriate dependencies.
"""

import sys
import subprocess
import platform
import importlib.util


def run_command(cmd):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    
    if version.major == 3 and version.minor >= 12:
        print("⚠️  Python 3.12+ detected - some packages may have limited compatibility")
    
    print("✅ Python version compatible")
    return True


def detect_platform():
    """Detect platform and architecture."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    print(f"Platform: {system} {machine}")
    
    # Check for Apple Silicon
    if system == "darwin" and machine in ["arm64", "aarch64"]:
        return "macos_arm"
    elif system == "darwin":
        return "macos_intel"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def install_pytorch_cpu():
    """Install CPU-only PyTorch."""
    print("Installing PyTorch...")
    
    platform_type = detect_platform()
    
    # Different strategies for different platforms
    if platform_type.startswith("macos"):
        # macOS: Standard installation works better than CPU index
        commands = [
            "pip install torch torchaudio",
            "pip install torch==2.0.1 torchaudio==2.0.2",
            "pip install torch==1.13.1 torchaudio==0.13.1"
        ]
    else:
        # Linux/Windows: Try CPU index first
        commands = [
            "pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu",
            "pip install torch==2.0.1 torchaudio==2.0.2",
            "pip install torch torchaudio"
        ]
    
    for cmd in commands:
        print(f"Trying: {cmd}")
        success, stdout, stderr = run_command(cmd)
        if success:
            print("✅ PyTorch installed successfully")
            return True
        else:
            print(f"Failed: {stderr[:100]}...")
    
    print("❌ Failed to install PyTorch")
    return False


def install_requirements(requirements_file):
    """Install requirements from file."""
    print(f"Installing requirements from {requirements_file}...")
    
    success, stdout, stderr = run_command(f"pip install -r {requirements_file}")
    
    if success:
        print("✅ Requirements installed successfully")
        return True
    else:
        print(f"❌ Failed to install requirements: {stderr}")
        return False


def check_optional_dependencies():
    """Check which optional dependencies are available."""
    optional_deps = {
        "faster_whisper": "faster-whisper",
        "torch": "torch", 
        "openai": "openai",
        "anthropic": "anthropic",
        "google.auth": "google-auth"
    }
    
    print("\nChecking optional dependencies:")
    available = {}
    
    for module, package in optional_deps.items():
        try:
            importlib.import_module(module)
            print(f"✅ {package}")
            available[package] = True
        except ImportError:
            print(f"❌ {package}")
            available[package] = False
    
    return available


def main():
    """Main installation process."""
    print("🚀 Transcription App Smart Installer")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Detect platform
    platform_type = detect_platform()
    
    # Choose installation strategy
    print(f"\nChoose installation option:")
    print("1. Full installation (includes faster-whisper)")
    print("2. CPU-only installation (lighter)")
    print("3. Minimal installation (no transcription, AI only)")
    print("4. Auto-detect best option")
    
    choice = input("\nEnter choice (1-4) [4]: ").strip() or "4"
    
    success = False
    
    if choice == "1":
        # Try full installation
        success = install_requirements("requirements.txt")
    
    elif choice == "2":
        # CPU-only installation
        success = install_requirements("requirements-cpu.txt")
    
    elif choice == "3":
        # Minimal installation
        success = install_requirements("requirements-minimal.txt")
    
    elif choice == "4":
        # Auto-detect
        print("\nAuto-detecting best installation method...")
        platform_type = detect_platform()
        
        if platform_type.startswith("macos"):
            print("macOS detected - using macOS-optimized installation...")
            # For macOS, try CPU requirements first
            if install_requirements("requirements-cpu.txt"):
                print("✅ macOS installation successful")
                success = True
            else:
                print("Trying minimal installation...")
                success = install_requirements("requirements-minimal.txt")
        else:
            # For other platforms, try minimal first (most likely to succeed)
            if install_requirements("requirements-minimal.txt"):
                print("✅ Minimal installation successful")
                
                # Try to add transcription capabilities
                print("\nAttempting to add transcription support...")
                if install_pytorch_cpu():
                    pytorch_success, _, _ = run_command("pip install faster-whisper")
                    if pytorch_success:
                        print("✅ Transcription support added")
                    else:
                        print("⚠️  Transcription support failed - you can use AI-only mode")
                
                success = True
            else:
                print("❌ Installation failed")
    
    if success:
        print("\n🎉 Installation completed!")
        
        # Check what's available
        available = check_optional_dependencies()
        
        print("\n📋 Next steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your API keys to .env")
        
        if available.get("openai") or available.get("anthropic"):
            print("3. Configure AI provider in config.yaml")
        
        if available.get("faster-whisper") or available.get("torch"):
            print("4. Test with: python -m src.cli test audio")
        else:
            print("4. Note: Local transcription not available - AI summarization only")
        
        print("5. Run: python -m src.main")
        
    else:
        print("\n❌ Installation failed")
        print("\nTroubleshooting:")
        print("- Try: pip install --upgrade pip")
        print("- Try: python -m pip install --user -r requirements-minimal.txt")
        print("- Check Python version compatibility")
        sys.exit(1)


if __name__ == "__main__":
    main()