#!/usr/bin/env python3
"""
Diagnostic script to check Python environment and PyTorch availability.
"""

import sys
import platform
import subprocess
import ssl
import urllib.request


def run_command(cmd):
    """Run a command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def check_python_info():
    """Check Python version and configuration."""
    print("🐍 Python Information:")
    print("-" * 40)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Machine: {platform.machine()}")
    
    if platform.system() == "Darwin":
        print(f"macOS version: {platform.mac_ver()[0]}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        print(f"Virtual env path: {sys.prefix}")
    else:
        print("⚠️  Not in virtual environment")


def check_pip_info():
    """Check pip configuration."""
    print("\n📦 Pip Information:")
    print("-" * 40)
    
    success, pip_version, _ = run_command("pip --version")
    if success:
        print(f"Pip version: {pip_version}")
    else:
        print("❌ Pip not found")
        return False
    
    # Check pip configuration
    success, pip_config, _ = run_command("pip config list")
    if success and pip_config:
        print(f"Pip config: {pip_config}")
    else:
        print("No custom pip configuration")
    
    return True


def check_internet_and_ssl():
    """Check internet connectivity and SSL."""
    print("\n🌐 Internet and SSL Check:")
    print("-" * 40)
    
    # Test basic connectivity
    try:
        response = urllib.request.urlopen('https://pypi.org', timeout=10)
        print("✅ Can reach PyPI")
    except Exception as e:
        print(f"❌ Cannot reach PyPI: {e}")
        return False
    
    # Test SSL
    try:
        ssl_context = ssl.create_default_context()
        print("✅ SSL context created successfully")
    except Exception as e:
        print(f"❌ SSL issue: {e}")
    
    return True


def check_pytorch_availability():
    """Check what PyTorch packages are available."""
    print("\n🔥 PyTorch Availability Check:")
    print("-" * 40)
    
    # Try to search for torch packages
    success, output, error = run_command("pip index versions torch")
    if success:
        print("Available torch versions:")
        print(output[:500] + "..." if len(output) > 500 else output)
    else:
        print(f"❌ Cannot query torch versions: {error}")
    
    # Try different PyPI indexes
    indexes = [
        "https://pypi.org/simple/",
        "https://download.pytorch.org/whl/",
        "https://download.pytorch.org/whl/cpu/"
    ]
    
    for index in indexes:
        print(f"\nTesting index: {index}")
        success, _, error = run_command(f"pip install --dry-run --index-url {index} torch")
        if success:
            print("✅ Index accessible")
        else:
            print(f"❌ Index failed: {error[:100]}...")


def check_python_compatibility():
    """Check Python version compatibility with PyTorch."""
    print("\n🔍 Python Compatibility Check:")
    print("-" * 40)
    
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    # PyTorch compatibility matrix
    if version.major < 3:
        print("❌ Python 2 not supported")
        return False
    elif version.minor < 8:
        print("❌ Python 3.7 and below not supported by modern PyTorch")
        return False
    elif version.minor > 11:
        print("⚠️  Python 3.12+ has limited PyTorch support")
        return "limited"
    else:
        print("✅ Python version should be compatible with PyTorch")
        return True


def suggest_fixes():
    """Suggest potential fixes."""
    print("\n🔧 Suggested Fixes:")
    print("-" * 40)
    
    version = sys.version_info
    
    if version.minor > 11:
        print("For Python 3.12+:")
        print("1. Try: pip install --pre torch torchaudio")
        print("2. Use conda: conda install pytorch torchaudio -c pytorch")
        print("3. Use minimal installation without PyTorch")
    
    print("\nGeneral fixes to try:")
    print("1. Upgrade pip: pip install --upgrade pip")
    print("2. Clear pip cache: pip cache purge")
    print("3. Try with --no-cache-dir: pip install --no-cache-dir torch")
    print("4. Use minimal installation: pip install -r requirements-minimal.txt")
    print("5. Install openai-whisper instead: pip install openai-whisper")


def test_minimal_installation():
    """Test if minimal installation would work."""
    print("\n🧪 Testing Minimal Installation:")
    print("-" * 40)
    
    minimal_packages = [
        "numpy",
        "PyYAML", 
        "python-dotenv",
        "openai",
        "anthropic",
        "rich"
    ]
    
    working_packages = []
    for package in minimal_packages:
        success, _, error = run_command(f"pip install --dry-run {package}")
        if success:
            print(f"✅ {package}")
            working_packages.append(package)
        else:
            print(f"❌ {package}: {error[:50]}...")
    
    print(f"\n{len(working_packages)}/{len(minimal_packages)} core packages available")
    
    if len(working_packages) >= 4:
        print("✅ Minimal installation should work!")
        return True
    else:
        print("❌ Even minimal installation may have issues")
        return False


def main():
    """Run all diagnostics."""
    print("🔍 Python Environment Diagnostics")
    print("=" * 50)
    
    check_python_info()
    
    if not check_pip_info():
        print("❌ Pip issues detected - cannot continue")
        return
    
    check_internet_and_ssl()
    check_pytorch_availability()
    compatibility = check_python_compatibility()
    
    print("\n" + "=" * 50)
    print("DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    if compatibility == "limited":
        print("⚠️  Python 3.12+ detected - PyTorch has limited support")
        print("Recommendation: Use minimal installation without PyTorch")
    elif compatibility:
        print("✅ Python version compatible, but PyTorch packages not found")
        print("This suggests a pip/network configuration issue")
    else:
        print("❌ Python version incompatible with modern PyTorch")
    
    suggest_fixes()
    
    if test_minimal_installation():
        print("\n🎯 RECOMMENDED ACTION:")
        print("Use minimal installation without PyTorch:")
        print("pip install -r requirements-minimal.txt")
        print("pip install openai-whisper")


if __name__ == "__main__":
    main()