#!/usr/bin/env python3
"""
Quick fix script for macOS PyTorch issues.
This bypasses PyTorch entirely and sets up a working installation.
"""

import subprocess
import sys


def run_cmd(cmd):
    """Run command and return success."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    """Quick fix installation."""
    print("🚀 Quick Fix for macOS PyTorch Issues")
    print("=" * 50)
    print("This will install the app WITHOUT PyTorch")
    print("Uses cloud-based transcription instead")
    print()
    
    # Check Python version
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or version.minor < 8:
        print("❌ Need Python 3.8+")
        return 1
    
    print("Step 1: Upgrade pip")
    if not run_cmd("pip install --upgrade pip"):
        print("⚠️  Pip upgrade failed, continuing...")
    
    print("\nStep 2: Install core requirements (no PyTorch)")
    if not run_cmd("pip install -r requirements-no-torch.txt"):
        print("❌ Installation failed")
        return 1
    
    print("\nStep 3: Test installation")
    try:
        import openai
        import anthropic
        import yaml
        import sounddevice
        print("✅ Core packages working!")
    except ImportError as e:
        print(f"⚠️  Some packages missing: {e}")
    
    print("\nStep 4: Create .env file")
    env_content = """# AI API Keys (you need at least one)
OPENAI_API_KEY=your_openai_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here

# Google API credentials (optional)
GOOGLE_CREDENTIALS_PATH=credentials.json
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
    except:
        print("⚠️  Could not create .env file")
    
    print("\n🎉 Quick fix complete!")
    print("\nNext steps:")
    print("1. Edit .env and add your OpenAI API key")
    print("2. Run: python -m src.cli status")
    print("3. Run: python -m src.main")
    print("\nNote: This uses cloud transcription, not local PyTorch")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())