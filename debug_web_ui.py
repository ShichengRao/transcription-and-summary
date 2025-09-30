#!/usr/bin/env python3
"""
Debug script to check web UI startup issues.
"""

import sys
import os
from pathlib import Path

# Set environment variables
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['MKL_THREADING_LAYER'] = 'GNU'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import AppConfig


def debug_config():
    """Debug configuration loading."""
    print("🔍 Debugging Configuration")
    print("=" * 50)
    
    try:
        config = AppConfig.load()
        print("✅ Configuration loaded")
        
        print(f"Web dashboard enabled: {config.ui.web_dashboard}")
        print(f"Web host: {config.ui.web_host}")
        print(f"Web port: {config.ui.web_port}")
        
        return config
        
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return None


def debug_flask():
    """Debug Flask import."""
    print("\n🔍 Debugging Flask")
    print("=" * 50)
    
    try:
        import flask
        print(f"✅ Flask available: {flask.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Flask not available: {e}")
        return False


def debug_web_ui_class():
    """Debug WebUI class."""
    print("\n🔍 Debugging WebUI Class")
    print("=" * 50)
    
    try:
        from src.web_ui import WebUI
        print("✅ WebUI class imported")
        
        # Create a dummy app instance
        class DummyApp:
            def is_recording(self):
                return True
            def get_status(self):
                return {'running': True, 'paused': False}
        
        dummy_app = DummyApp()
        web_ui = WebUI(dummy_app, "127.0.0.1", 8080)
        print("✅ WebUI instance created")
        
        return True
        
    except Exception as e:
        print(f"❌ WebUI class failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run debug checks."""
    print("🐛 Web UI Debug Script")
    print("=" * 50)
    
    # Check config
    config = debug_config()
    if not config:
        return 1
    
    # Check Flask
    if not debug_flask():
        print("\n💡 Solution: pip install flask")
        return 1
    
    # Check WebUI class
    if not debug_web_ui_class():
        return 1
    
    print("\n🎉 All checks passed!")
    print("Web UI should work. Try running: python -m src.main")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())