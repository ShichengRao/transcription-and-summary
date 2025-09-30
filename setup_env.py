#!/usr/bin/env python3
"""
Setup environment variables to fix common macOS issues.
Run this before using the transcription app.
"""

import os
import sys


def setup_environment():
    """Set up environment variables for optimal performance."""
    
    # Fix OpenMP duplicate library warning
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    # Suppress Intel MKL warnings
    os.environ['MKL_THREADING_LAYER'] = 'GNU'
    
    # Optimize NumPy threading
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    
    # Reduce multiprocessing warnings
    os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:multiprocessing'
    
    print("✅ Environment variables set for optimal performance")
    print("   - Fixed OpenMP duplicate library warnings")
    print("   - Suppressed Intel MKL warnings")
    print("   - Optimized threading for single-user app")


def create_shell_script():
    """Create a shell script to set environment variables."""
    script_content = '''#!/bin/bash
# Environment setup for transcription app
export KMP_DUPLICATE_LIB_OK=TRUE
export MKL_THREADING_LAYER=GNU
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONWARNINGS=ignore::UserWarning:multiprocessing

echo "✅ Environment variables set for transcription app"
'''
    
    try:
        with open('setup_env.sh', 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod('setup_env.sh', 0o755)
        
        print("✅ Created setup_env.sh script")
        print("   Run: source setup_env.sh")
        
    except Exception as e:
        print(f"❌ Failed to create shell script: {e}")


def main():
    """Main setup function."""
    print("🔧 Setting up environment for transcription app")
    print("=" * 50)
    
    setup_environment()
    create_shell_script()
    
    print("\n📋 Usage:")
    print("1. Run this script: python setup_env.py")
    print("2. Or source the shell script: source setup_env.sh")
    print("3. Then run the app: python -m src.main")
    
    print("\n💡 For permanent setup, add these to your ~/.zshrc or ~/.bashrc:")
    print("   export KMP_DUPLICATE_LIB_OK=TRUE")
    print("   export MKL_THREADING_LAYER=GNU")


if __name__ == "__main__":
    main()