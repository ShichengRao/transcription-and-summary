"""Automation and scheduling system for daily transcription and summary tasks."""

import ssl
import time
import threading
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import AppConfig
from .logger import LoggerMixin
from .audio_capture import AudioCapture, AudioSegment
from .transcription import TranscriptionService, TranscriptionResult
from .summarization import SummarizationService, DailySummary
from .google_docs import GoogleDocsService
from .web_ui import WebUI


class TranscriptionApp(LoggerMixin):
    """Main application class that orchestrates all components."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.config.ensure_directories()
        
        # Initialize services
        self.audio_capture = AudioCapture(
            config.audio, 
            config.get_storage_paths()['audio']
        )
        self.transcription_service = TranscriptionService(config.transcription)
        self.summarization_service = SummarizationService(config.summary)
        self.google_docs_service = GoogleDocsService(config.google_docs)
        
        # State management
        self._running = False
        self._paused = False
        self._scheduler: Optional[BackgroundScheduler] = None
        self._web_ui: Optional[WebUI] = None
        
        # Daily transcript accumulation
        self._daily_transcripts: Dict[date, List[str]] = {}
        self._transcript_lock = threading.Lock()
        
        # Callbacks for UI
        self._status_callbacks: List[Callable[[str], None]] = []
        
        # Setup callbacks
        self.audio_capture.set_segment_callback(self._on_audio_segment)
        self.transcription_service.set_transcription_callback(self._on_transcription_complete)
        
        self.logger.info("TranscriptionApp initialized")
    
    def add_status_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for status updates."""
        self._status_callbacks.append(callback)
    
    def _notify_status(self, status: str) -> None:
        """Notify all status callbacks."""
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
    
    def start(self) -> bool:
        """Start the transcription application."""
        if self._running:
            self.logger.warning("Application already running")
            return True
        
        try:
            # Set running flag early so web UI can see it
            self._running = True
            
            # Initialize transcription service
            self.logger.info("Starting transcription service...")
            if not self.transcription_service.start_processing():
                self.logger.error("Failed to start transcription service")
                self._running = False
                return False
            
            # Start audio capture
            self.logger.info("Starting audio capture...")
            self.audio_capture.start_recording()
            
            # Setup scheduler for daily tasks
            self.logger.info("Setting up scheduler...")
            self._setup_scheduler()
            
            # Start web UI if enabled
            if self.config.ui.web_dashboard:
                self.logger.info("Starting web dashboard...")
                try:
                    self._web_ui = WebUI(self, self.config.ui.web_host, self.config.ui.web_port)
                    self._web_ui.start()
                    self.logger.info(f"Web dashboard available at http://{self.config.ui.web_host}:{self.config.ui.web_port}")
                except Exception as e:
                    self.logger.error(f"Failed to start web dashboard: {e}")
                    self._web_ui = None
            
            self._notify_status("Recording and transcribing...")
            
            self.logger.info("Transcription application started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting application: {e}")
            self._running = False
            # Try to clean up any partially started services
            try:
                if hasattr(self, 'audio_capture'):
                    self.audio_capture.stop_recording()
                if hasattr(self, 'transcription_service'):
                    self.transcription_service.stop_processing()
                if hasattr(self, '_scheduler') and self._scheduler:
                    self._scheduler.shutdown()
            except Exception as cleanup_error:
                self.logger.error(f"Error during cleanup: {cleanup_error}")
            return False
    
    def stop(self) -> None:
        """Stop the transcription application."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop audio capture
        self.audio_capture.stop_recording()
        
        # Stop transcription service
        self.transcription_service.stop_processing()
        
        # Stop scheduler
        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None
        
        # Stop web UI
        if self._web_ui:
            self._web_ui.stop()
            self._web_ui = None
        
        # Process any remaining transcripts
        self._process_remaining_transcripts()
        
        self._notify_status("Stopped")
        self.logger.info("Transcription application stopped")
    
    def pause(self) -> None:
        """Pause recording (but keep processing)."""
        self._paused = True
        self.audio_capture.pause_recording()
        self._notify_status("Paused")
        self.logger.info("Recording paused")
    
    def resume(self) -> None:
        """Resume recording."""
        self._paused = False
        self.audio_capture.resume_recording()
        self._notify_status("Recording and transcribing...")
        self.logger.info("Recording resumed")
    
    def is_running(self) -> bool:
        """Check if application is running."""
        return self._running
    
    def is_paused(self) -> bool:
        """Check if application is paused."""
        return self._paused
    
    def is_recording(self) -> bool:
        """Check if application is actively recording."""
        return self._running and not self._paused and self.audio_capture.is_recording()
    
    def _setup_scheduler(self) -> None:
        """Setup scheduled tasks."""
        self._scheduler = BackgroundScheduler()
        
        # Daily summary generation
        if self.config.summary.daily_summary:
            summary_time = self.config.summary.summary_time
            hour, minute = map(int, summary_time.split(':'))
            
            self._scheduler.add_job(
                func=self._generate_daily_summary,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_summary',
                name='Generate Daily Summary'
            )
        
        # Cleanup old files
        self._scheduler.add_job(
            func=self._cleanup_old_files,
            trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
            id='cleanup',
            name='Cleanup Old Files'
        )
        
        # Hourly summaries if enabled
        if self.config.summary.hourly_summary:
            self._scheduler.add_job(
                func=self._generate_hourly_summary,
                trigger=CronTrigger(minute=0),  # Every hour
                id='hourly_summary',
                name='Generate Hourly Summary'
            )
        
        self._scheduler.start()
        self.logger.info("Scheduler started with daily tasks")
    
    def _on_audio_segment(self, segment: AudioSegment) -> None:
        """Handle completed audio segment."""
        self.logger.info(f"Audio segment completed: {segment.file_path.name} ({segment.duration:.1f}s)")
        self.logger.debug(f"Audio segment details: start={segment.start_time}, end={segment.end_time}, sample_rate={segment.sample_rate}")
        
        # Queue for transcription
        self.transcription_service.queue_audio_segment(segment)
    
    def _on_transcription_complete(self, result: TranscriptionResult) -> None:
        """Handle completed transcription."""
        if not result.text.strip():
            self.logger.debug("Empty transcription, skipping")
            self._cleanup_audio_file(result.audio_segment.file_path)
            return
        
        self.logger.info(f"Transcription completed: {len(result.text)} characters")
        
        # Add to daily transcript
        self._add_to_daily_transcript(result)
        
        # Save individual transcript
        self._save_transcript(result)
        
        # Update daily consolidated transcript
        self._update_daily_transcript_file(result)
        
        # Cleanup audio file
        self._cleanup_audio_file(result.audio_segment.file_path)
    
    def _add_to_daily_transcript(self, result: TranscriptionResult) -> None:
        """Add transcription result to daily accumulation."""
        transcript_date = result.timestamp.date()
        
        # Format transcript entry
        timestamp_str = result.timestamp.strftime('%H:%M:%S')
        transcript_entry = f"[{timestamp_str}] {result.text}"
        
        with self._transcript_lock:
            if transcript_date not in self._daily_transcripts:
                self._daily_transcripts[transcript_date] = []
            
            self._daily_transcripts[transcript_date].append(transcript_entry)
    
    def _save_transcript(self, result: TranscriptionResult) -> None:
        """Save individual transcript to file."""
        try:
            transcript_date = result.timestamp.date()
            transcript_dir = self.config.get_storage_paths()['transcripts']
            
            # Create date-specific directory
            date_dir = transcript_dir / transcript_date.strftime('%Y-%m-%d')
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Save transcript file
            timestamp_str = result.timestamp.strftime('%H%M%S')
            transcript_file = date_dir / f"transcript_{timestamp_str}.txt"
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"Timestamp: {result.timestamp.isoformat()}\n")
                f.write(f"Duration: {result.audio_segment.duration:.2f}s\n")
                f.write(f"Language: {result.language}\n")
                f.write(f"Confidence: {result.confidence:.2f}\n")
                f.write(f"Processing Time: {result.processing_time:.2f}s\n")
                f.write("-" * 50 + "\n")
                f.write(result.text)
            
        except Exception as e:
            self.logger.error(f"Error saving transcript: {e}")
    
    def _update_daily_transcript_file(self, result: TranscriptionResult) -> None:
        """Update the daily consolidated transcript file."""
        try:
            transcript_date = result.timestamp.date()
            transcript_dir = self.config.get_storage_paths()['transcripts']
            
            # Create date-specific directory
            date_dir = transcript_dir / transcript_date.strftime('%Y-%m-%d')
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Daily consolidated transcript file
            daily_file = date_dir / f"daily_transcript_{transcript_date.strftime('%Y-%m-%d')}.txt"
            
            # Format the transcript entry
            timestamp_str = result.timestamp.strftime('%H:%M:%S')
            transcript_entry = f"[{timestamp_str}] {result.text}"
            
            # Append to daily file (create if doesn't exist)
            with open(daily_file, 'a', encoding='utf-8') as f:
                if daily_file.stat().st_size == 0:  # New file, add header
                    f.write(f"Daily Transcript - {transcript_date.strftime('%Y-%m-%d')}\\n")
                    f.write("=" * 50 + "\\n\\n")
                
                f.write(f"{transcript_entry}\\n\\n")
            
            self.logger.debug(f"Updated daily transcript file: {daily_file.name}")
            
        except Exception as e:
            self.logger.error(f"Error updating daily transcript file: {e}")
    
    def generate_daily_transcript_file(self, target_date: date) -> bool:
        """Generate consolidated daily transcript file from individual transcripts."""
        try:
            transcript_dir = self.config.get_storage_paths()['transcripts']
            date_dir = transcript_dir / target_date.strftime('%Y-%m-%d')
            
            if not date_dir.exists():
                self.logger.warning(f"No transcript directory for {target_date}")
                return False
            
            # Find all individual transcript files
            transcript_files = sorted(date_dir.glob("transcript_*.txt"))
            
            if not transcript_files:
                self.logger.warning(f"No individual transcript files found for {target_date}")
                return False
            
            # Daily consolidated transcript file
            daily_file = date_dir / f"daily_transcript_{target_date.strftime('%Y-%m-%d')}.txt"
            
            # Create consolidated file
            with open(daily_file, 'w', encoding='utf-8') as daily_f:
                daily_f.write(f"Daily Transcript - {target_date.strftime('%Y-%m-%d')}\\n")
                daily_f.write("=" * 50 + "\\n\\n")
                
                for transcript_file in transcript_files:
                    try:
                        with open(transcript_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        # Extract timestamp and text from individual file
                        timestamp_line = None
                        text_started = False
                        text_lines = []
                        
                        for line in lines:
                            if line.startswith("Timestamp: "):
                                timestamp_str = line.split("Timestamp: ")[1].strip()
                                # Convert to HH:MM:SS format
                                from datetime import datetime
                                timestamp = datetime.fromisoformat(timestamp_str)
                                timestamp_line = timestamp.strftime('%H:%M:%S')
                            elif line.strip() == "-" * 50:
                                text_started = True
                            elif text_started:
                                text_lines.append(line.rstrip())
                        
                        if timestamp_line and text_lines:
                            text = " ".join(text_lines).strip()
                            daily_f.write(f"[{timestamp_line}] {text}\\n\\n")
                    
                    except Exception as e:
                        self.logger.error(f"Error processing {transcript_file}: {e}")
                        continue
            
            self.logger.info(f"Generated daily transcript file: {daily_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating daily transcript file for {target_date}: {e}")
            return False
    
    def _cleanup_audio_file(self, audio_path: Path) -> None:
        """Clean up processed audio file."""
        try:
            if audio_path.exists():
                audio_path.unlink()
                self.logger.debug(f"Cleaned up audio file: {audio_path.name}")
        except Exception as e:
            self.logger.error(f"Error cleaning up audio file {audio_path}: {e}")
    
    def _generate_daily_summary(self) -> None:
        """Generate and save daily summary."""
        try:
            yesterday = date.today() - timedelta(days=1)
            self.logger.info(f"Generating daily summary for {yesterday}")
            
            # Get daily transcript
            daily_text = self._get_daily_transcript(yesterday)
            
            if not daily_text.strip():
                self.logger.info(f"No transcript data for {yesterday}")
                return
            
            # Generate summary
            summary = self.summarization_service.generate_daily_summary(daily_text, yesterday)
            
            if not summary:
                self.logger.error(f"Failed to generate summary for {yesterday}")
                return
            
            # Save summary locally
            summary_dir = self.config.get_storage_paths()['summaries']
            summary_file = summary_dir / f"summary_{yesterday.strftime('%Y-%m-%d')}.json"
            
            if self.summarization_service.save_summary(summary, summary_file):
                self.logger.info(f"Daily summary saved: {summary_file}")
            
            # Upload to Google Docs if enabled
            if self.config.google_docs.enabled:
                self._upload_to_google_docs(yesterday, daily_text, summary)
            
            # Clean up daily transcript from memory
            with self._transcript_lock:
                self._daily_transcripts.pop(yesterday, None)
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
    
    def _get_daily_transcript(self, target_date: date) -> str:
        """Get accumulated transcript for a specific date."""
        with self._transcript_lock:
            transcripts = self._daily_transcripts.get(target_date, [])
        
        if transcripts:
            return "\n".join(transcripts)
        
        # Try to load from saved files
        return self._load_daily_transcript_from_files(target_date)
    
    def _load_daily_transcript_from_files(self, target_date: date) -> str:
        """Load daily transcript from saved files."""
        try:
            transcript_dir = self.config.get_storage_paths()['transcripts']
            date_dir = transcript_dir / target_date.strftime('%Y-%m-%d')
            
            if not date_dir.exists():
                return ""
            
            transcripts = []
            for transcript_file in sorted(date_dir.glob("transcript_*.txt")):
                try:
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract just the transcript text (after the separator)
                        if "-" * 50 in content:
                            text_part = content.split("-" * 50, 1)[1].strip()
                            if text_part:
                                # Extract timestamp from filename
                                timestamp = transcript_file.stem.split('_')[1]
                                formatted_time = f"{timestamp[:2]}:{timestamp[2:4]}:{timestamp[4:6]}"
                                transcripts.append(f"[{formatted_time}] {text_part}")
                except Exception as e:
                    self.logger.error(f"Error reading transcript file {transcript_file}: {e}")
            
            return "\n".join(transcripts)
            
        except Exception as e:
            self.logger.error(f"Error loading daily transcript from files: {e}")
            return ""
    
    def _upload_to_google_docs(self, target_date: date, transcript_text: str, summary: DailySummary) -> None:
        """Upload daily summary and transcript to Google Docs."""
        try:
            if not self.google_docs_service.authenticate():
                self.logger.error("Failed to authenticate with Google Docs")
                return
            
            # Check if document already exists
            existing_doc_id = self.google_docs_service.find_document_by_date(target_date)
            
            if existing_doc_id:
                # Update existing document
                self.logger.info(f"Updating existing Google Doc for {target_date}")
                # For now, we'll create a new document instead of updating
                # to avoid complex content merging
            
            # Create new document
            doc_url = self.google_docs_service.create_daily_document(
                target_date, transcript_text, summary
            )
            
            if doc_url:
                self.logger.info(f"Daily summary uploaded to Google Docs: {doc_url}")
            else:
                self.logger.error("Failed to upload to Google Docs")
                
        except ssl.SSLError as e:
            self.logger.error(f"SSL error uploading to Google Docs: {e}")
            self.logger.info("This may be a network or certificate issue. Try again later or check your connection.")
        except Exception as e:
            self.logger.error(f"Error uploading to Google Docs: {e}")
    
    def _generate_hourly_summary(self) -> None:
        """Generate hourly summary (if enabled)."""
        # This is a placeholder for hourly summary functionality
        # Could be implemented to provide more frequent updates
        pass
    
    def _cleanup_old_files(self) -> None:
        """Clean up old audio and transcript files."""
        try:
            current_date = date.today()
            paths = self.config.get_storage_paths()
            
            # Clean up old audio files
            audio_cutoff = current_date - timedelta(days=self.config.storage.max_audio_age_days)
            self._cleanup_files_older_than(paths['audio'], audio_cutoff, "*.wav")
            
            # Clean up old transcript files
            transcript_cutoff = current_date - timedelta(days=self.config.storage.max_transcript_age_days)
            self._cleanup_files_older_than(paths['transcripts'], transcript_cutoff, "*")
            
            self.logger.info("File cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during file cleanup: {e}")
    
    def _cleanup_files_older_than(self, directory: Path, cutoff_date: date, pattern: str) -> None:
        """Clean up files older than cutoff date."""
        try:
            if not directory.exists():
                return
            
            for file_path in directory.rglob(pattern):
                if file_path.is_file():
                    # Get file modification date
                    file_date = date.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_date < cutoff_date:
                        file_path.unlink()
                        self.logger.debug(f"Cleaned up old file: {file_path}")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up files in {directory}: {e}")
    
    def _process_remaining_transcripts(self) -> None:
        """Process any remaining transcripts before shutdown."""
        try:
            # Wait for transcription queue to empty
            time.sleep(2)
            
            # Process any completed transcriptions
            results = self.transcription_service.get_completed_transcriptions()
            for result in results:
                self._on_transcription_complete(result)
            
        except Exception as e:
            self.logger.error(f"Error processing remaining transcripts: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current application status."""
        try:
            transcription_stats = self.transcription_service.get_statistics() if hasattr(self, 'transcription_service') else {}
            
            # Get audio configuration for debugging
            audio_config = {
                'silence_threshold': float(self.config.audio.silence_threshold),
                'silence_duration': float(self.config.audio.silence_duration),
                'min_audio_duration': float(getattr(self.config.audio, 'min_audio_duration', 2.0)),
                'noise_gate_threshold': float(getattr(self.config.audio, 'noise_gate_threshold', 0.015)),
                'sample_rate': int(self.config.audio.sample_rate),
                'channels': int(self.config.audio.channels)
            }
            
            # Get audio levels for debugging
            audio_levels = {}
            if self._running and hasattr(self, 'audio_capture'):
                try:
                    audio_levels = self.audio_capture.get_audio_levels()
                except Exception as e:
                    self.logger.error(f"Error getting audio levels: {e}")
            
            # Service health check
            services_status = {
                'transcription_service': hasattr(self, 'transcription_service') and self.transcription_service._processing if hasattr(self, 'transcription_service') else False,
                'audio_capture': hasattr(self, 'audio_capture') and self.audio_capture.is_recording() if hasattr(self, 'audio_capture') else False,
                'scheduler': hasattr(self, '_scheduler') and self._scheduler and self._scheduler.running if hasattr(self, '_scheduler') else False,
                'web_ui': hasattr(self, '_web_ui') and self._web_ui and self._web_ui.running if hasattr(self, '_web_ui') else False
            }
            
            return {
                'running': self._running,
                'paused': self._paused,
                'recording': self.audio_capture.is_recording() if hasattr(self, 'audio_capture') else False,
                'transcription_queue_size': transcription_stats.get('queue_size', 0),
                'total_transcribed': transcription_stats.get('total_processed', 0),
                'daily_transcript_dates': [str(d) for d in self._daily_transcripts.keys()],
                'google_docs_enabled': self.config.google_docs.enabled,
                'audio_config': audio_config,
                'audio_levels': audio_levels,
                'log_level': self.config.log_level,
                'services_status': services_status
            }
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {
                'running': False,
                'paused': False,
                'recording': False,
                'error': str(e),
                'services_status': {}
            }
    
    def diagnose_services(self) -> Dict[str, Any]:
        """Diagnose the health of all services."""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'app_running': self._running,
            'services': {}
        }
        
        # Check transcription service
        if hasattr(self, 'transcription_service'):
            try:
                stats = self.transcription_service.get_statistics()
                diagnosis['services']['transcription'] = {
                    'exists': True,
                    'processing': self.transcription_service._processing,
                    'stats': stats,
                    'error': None
                }
            except Exception as e:
                diagnosis['services']['transcription'] = {
                    'exists': True,
                    'processing': False,
                    'error': str(e)
                }
        else:
            diagnosis['services']['transcription'] = {'exists': False}
        
        # Check audio capture
        if hasattr(self, 'audio_capture'):
            try:
                diagnosis['services']['audio'] = {
                    'exists': True,
                    'recording': self.audio_capture.is_recording(),
                    'levels': self.audio_capture.get_audio_levels(),
                    'error': None
                }
            except Exception as e:
                diagnosis['services']['audio'] = {
                    'exists': True,
                    'recording': False,
                    'error': str(e)
                }
        else:
            diagnosis['services']['audio'] = {'exists': False}
        
        # Check web UI
        if hasattr(self, '_web_ui') and self._web_ui:
            diagnosis['services']['web_ui'] = {
                'exists': True,
                'running': self._web_ui.running,
                'host': self._web_ui.host,
                'port': self._web_ui.port
            }
        else:
            diagnosis['services']['web_ui'] = {'exists': False}
        
        return diagnosis
    
    def force_daily_summary(self, target_date: Optional[date] = None) -> bool:
        """Force generation of daily summary for specified date."""
        if target_date is None:
            target_date = date.today()
        
        try:
            self.logger.info(f"Forcing daily summary generation for {target_date}")
            
            # Get daily transcript
            daily_text = self._get_daily_transcript(target_date)
            
            if not daily_text.strip():
                self.logger.info(f"No transcript data for {target_date}")
                return False
            
            # Generate summary
            summary = self.summarization_service.generate_daily_summary(daily_text, target_date)
            
            if not summary:
                self.logger.error(f"Failed to generate summary for {target_date}")
                return False
            
            # Save summary locally
            summary_dir = self.config.get_storage_paths()['summaries']
            summary_dir.mkdir(parents=True, exist_ok=True)
            summary_file = summary_dir / f"summary_{target_date.strftime('%Y-%m-%d')}.json"
            
            if self.summarization_service.save_summary(summary, summary_file):
                self.logger.info(f"Daily summary saved: {summary_file}")
                
                # Upload to Google Docs if enabled
                if self.config.google_docs.enabled:
                    self._upload_to_google_docs(target_date, daily_text, summary)
                
                return True
            else:
                self.logger.error(f"Failed to save summary to {summary_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error forcing daily summary: {e}")
            return False