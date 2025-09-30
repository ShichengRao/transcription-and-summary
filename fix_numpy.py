#!/usr/bin/env python3
"""
Quick fix for NumPy 2.x compatibility issues.
"""

import subprocess
import sys


def run_cmd(cmd):
    """Run command and return success."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    """Fix NumPy compatibility."""
    print("🔧 Fixing NumPy 2.x Compatibility Issues")
    print("=" * 50)
    
    print("This will downgrade NumPy to 1.x for compatibility with faster-whisper")
    
    proceed = input("Proceed? (y/N): ").lower().strip()
    if proceed != 'y':
        print("Cancelled")
        return 0
    
    print("\nStep 1: Uninstall NumPy 2.x")
    run_cmd("pip uninstall numpy -y")
    
    print("\nStep 2: Install NumPy 1.x")
    if run_cmd('pip install "numpy<2.0.0"'):
        print("✅ NumPy 1.x installed")
    else:
        print("❌ Failed to install NumPy 1.x")
        return 1
    
    print("\nStep 3: Reinstall faster-whisper")
    if run_cmd("pip install --force-reinstall faster-whisper"):
        print("✅ faster-whisper reinstalled")
    else:
        print("⚠️  faster-whisper reinstall failed")
    
    print("\nStep 4: Test imports")
    try:
        import numpy
        print(f"✅ NumPy {numpy.__version__} working")
        
        import faster_whisper
        print("✅ faster-whisper working")
        
        print("\n🎉 NumPy compatibility fixed!")
        print("You can now run: python test_sample.py")
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())