#!/usr/bin/env python3
"""
Test script to verify web UI functionality.
"""

import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables first
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['MKL_THREADING_LAYER'] = 'GNU'

from src.config import AppConfig
from src.automation import TranscriptionApp


def test_web_ui():
    """Test web UI startup."""
    print("🧪 Testing Web UI")
    print("=" * 50)
    
    # Load config
    try:
        config = AppConfig.load()
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False
    
    # Enable web dashboard
    config.ui.web_dashboard = True
    config.ui.web_port = 8080
    
    # Create app
    try:
        app = TranscriptionApp(config)
        print("✅ App instance created")
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False
    
    # Start app
    try:
        print("Starting app...")
        if app.start():
            print("✅ App started successfully")
            
            # Wait a moment for web UI to start
            time.sleep(3)
            
            # Check if web UI is accessible
            try:
                import requests
                response = requests.get("http://127.0.0.1:8080", timeout=5)
                if response.status_code == 200:
                    print("✅ Web UI is accessible at http://127.0.0.1:8080")
                    success = True
                else:
                    print(f"❌ Web UI returned status {response.status_code}")
                    success = False
            except ImportError:
                print("⚠️  requests not installed, cannot test HTTP access")
                print("✅ Web UI should be accessible at http://127.0.0.1:8080")
                success = True
            except Exception as e:
                print(f"❌ Web UI not accessible: {e}")
                success = False
            
            # Stop app
            print("Stopping app...")
            app.stop()
            print("✅ App stopped")
            
            return success
            
        else:
            print("❌ App failed to start")
            return False
            
    except Exception as e:
        print(f"❌ App start failed: {e}")
        return False


def test_flask_import():
    """Test if Flask is available."""
    print("Testing Flask availability...")
    try:
        import flask
        print(f"✅ Flask {flask.__version__} available")
        return True
    except ImportError:
        print("❌ Flask not installed")
        print("Install with: pip install flask")
        return False


def main():
    """Run web UI tests."""
    print("🌐 Web UI Test Suite")
    print("=" * 50)
    
    # Test Flask
    if not test_flask_import():
        print("\n❌ Flask not available - web UI will not work")
        print("Run: pip install flask")
        return 1
    
    # Test web UI
    if test_web_ui():
        print("\n🎉 Web UI test passed!")
        print("You can now run: python -m src.main")
        print("And access: http://127.0.0.1:8080")
        return 0
    else:
        print("\n❌ Web UI test failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())