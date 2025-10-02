"""Main entry point for the transcription and summary application."""

import os
import sys
import signal
import time
import atexit
from pathlib import Path

from .config import AppConfig, load_environment_variables
from .logger import setup_logger
from .automation import TranscriptionApp

# Fix OpenMP duplicate library warning
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Suppress Intel MKL warnings
os.environ['MKL_THREADING_LAYER'] = 'GNU'


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutdown signal received. Stopping application...")
    if hasattr(signal_handler, 'app') and signal_handler.app:
        try:
            signal_handler.app.stop()
        except Exception as e:
            print(f"Error during shutdown: {e}")
    
    # Force cleanup
    cleanup_resources()
    sys.exit(0)


def cleanup_resources():
    """Clean up resources on shutdown."""
    try:
        # Clean up any remaining multiprocessing resources
        import multiprocessing
        multiprocessing.active_children()  # This cleans up zombie processes
        
        # Give threads time to cleanup
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Warning during cleanup: {e}")


def setup_cleanup():
    """Setup cleanup handlers."""
    atexit.register(cleanup_resources)


def main():
    """Main application entry point."""
    # Setup cleanup handlers
    setup_cleanup()
    
    # Load environment variables
    load_environment_variables()
    
    # Load configuration
    try:
        config = AppConfig.load()
        print(f"Configuration loaded successfully")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # Setup logging with file output
    log_dir = config.get_storage_paths()['base'] / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'transcription_app.log'
    
    logger = setup_logger(
        level=config.log_level,
        log_file=str(log_file),
        console_output=True
    )
    
    logger.info(f"Logging to file: {log_file}")
    
    logger.info("Starting Transcription and Summary Application")
    
    # Create application
    try:
        app = TranscriptionApp(config)
        signal_handler.app = app  # Store for signal handler
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Add status callback for console output
        def status_callback(status: str):
            logger.info(f"Status: {status}")
        
        app.add_status_callback(status_callback)
        
        # Start the application
        if not app.start():
            logger.error("Failed to start application")
            return 1
        
        logger.info("Application started successfully. Press Ctrl+C to stop.")
        
        # Show web UI URL if enabled
        if config.ui.web_dashboard:
            print(f"\n🌐 Web Dashboard: http://{config.ui.web_host}:{config.ui.web_port}")
            print("   Use the web interface to monitor and control the application")
        
        print("\n📋 Available commands:")
        print("   python -m src.cli status          - Show status")
        print("   python -m src.cli process-audio   - Process pending audio")
        print("   python -m src.cli generate-summary - Generate daily summary")
        
        # Keep the application running
        try:
            logger.info("Application is running. Monitoring status...")
            while app.is_running():
                time.sleep(5)  # Check every 5 seconds instead of 1
                # Periodically log status for debugging
                if hasattr(app, 'diagnose_services'):
                    try:
                        diagnosis = app.diagnose_services()
                        if not diagnosis.get('services', {}).get('transcription', {}).get('processing', False):
                            logger.warning("Transcription service not processing!")
                        if not diagnosis.get('services', {}).get('audio', {}).get('recording', False):
                            logger.warning("Audio capture not recording!")
                    except Exception as diag_error:
                        logger.error(f"Error during diagnosis: {diag_error}")
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        # Stop the application
        app.stop()
        logger.info("Application stopped successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error running application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())