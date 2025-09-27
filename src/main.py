"""Main entry point for the transcription and summary application."""

import sys
import signal
import time
from pathlib import Path

from .config import AppConfig, load_environment_variables
from .logger import setup_logger
from .automation import TranscriptionApp


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutdown signal received. Stopping application...")
    if hasattr(signal_handler, 'app') and signal_handler.app:
        signal_handler.app.stop()
    sys.exit(0)


def main():
    """Main application entry point."""
    # Load environment variables
    load_environment_variables()
    
    # Load configuration
    try:
        config = AppConfig.load()
        print(f"Configuration loaded successfully")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # Setup logging
    logger = setup_logger(
        level=config.log_level,
        log_file="transcription_app.log" if config.debug else None,
        console_output=True
    )
    
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
        
        # Keep the application running
        try:
            while app.is_running():
                time.sleep(1)
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