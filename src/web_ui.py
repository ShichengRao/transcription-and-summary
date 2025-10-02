"""Simple web UI for the transcription application."""

import json
import threading
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from flask import Flask, render_template_string, jsonify, request, redirect, url_for
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None

try:
    from waitress import serve
    WAITRESS_AVAILABLE = True
except ImportError:
    WAITRESS_AVAILABLE = False
    serve = None

from .logger import LoggerMixin


class WebUI(LoggerMixin):
    """Simple web interface for monitoring and controlling the transcription app."""
    
    def __init__(self, app_instance, host: str = "127.0.0.1", port: int = 8080):
        if not FLASK_AVAILABLE:
            self.logger.error("Flask not available. Install with: pip install flask")
            self.flask_app = None
            return
            
        self.app_instance = app_instance
        self.host = host
        self.port = port
        
        # Flask app
        self.flask_app = Flask(__name__)
        self.flask_app.secret_key = "transcription_app_secret"
        
        # Status tracking
        self.last_heartbeat = datetime.now()
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info(f"Web UI initialized on {host}:{port}")
    
    def start(self) -> None:
        """Start the web UI server."""
        if not FLASK_AVAILABLE or not self.flask_app:
            self.logger.error("Cannot start web UI - Flask not available")
            return
            
        if self.running:
            return
        
        try:
            self.running = True
            
            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            # Start web server in a separate thread
            if WAITRESS_AVAILABLE:
                # Use production WSGI server
                server_thread = threading.Thread(
                    target=lambda: serve(
                        self.flask_app,
                        host=self.host,
                        port=self.port,
                        threads=4
                    ),
                    daemon=True
                )
                self.logger.info(f"Starting production web server on {self.host}:{self.port}")
            else:
                # Fallback to Flask development server
                server_thread = threading.Thread(
                    target=lambda: self.flask_app.run(
                        host=self.host, 
                        port=self.port, 
                        debug=False, 
                        use_reloader=False,
                        threaded=True
                    ),
                    daemon=True
                )
                self.logger.warning("Using Flask development server (install waitress for production)")
            
            server_thread.start()
            
            # Give Flask a moment to start
            time.sleep(1)
            
            self.logger.info(f"Web UI started at http://{self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start web UI: {e}")
            self.running = False
    
    def stop(self) -> None:
        """Stop the web UI server."""
        self.running = False
        self.logger.info("Web UI stopped")
    
    def _heartbeat_loop(self) -> None:
        """Update heartbeat every minute."""
        while self.running:
            try:
                if hasattr(self.app_instance, 'is_recording') and self.app_instance.is_recording():
                    self.last_heartbeat = datetime.now()
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
            time.sleep(60)  # Update every minute
    
    def _setup_routes(self) -> None:
        """Setup Flask routes."""
        
        @self.flask_app.route('/')
        def index():
            """Main dashboard."""
            return render_template_string(self._get_main_template())
        
        @self.flask_app.route('/api/status')
        def api_status():
            """Get current status as JSON."""
            status = self.app_instance.get_status()
            
            # Add UI-specific status
            status.update({
                'last_heartbeat': self.last_heartbeat.isoformat(),
                'heartbeat_ago': (datetime.now() - self.last_heartbeat).total_seconds(),
                'current_time': datetime.now().isoformat(),
                'uptime': self._get_uptime()
            })
            
            return jsonify(status)
        
        @self.flask_app.route('/api/control/<action>', methods=['POST'])
        def api_control(action):
            """Control the application."""
            try:
                if action == 'pause':
                    self.app_instance.pause()
                    return jsonify({'success': True, 'message': 'Recording paused'})
                
                elif action == 'resume':
                    self.app_instance.resume()
                    return jsonify({'success': True, 'message': 'Recording resumed'})
                
                elif action == 'force_transcribe':
                    # Force process any pending audio
                    self._force_transcribe()
                    return jsonify({'success': True, 'message': 'Transcription triggered'})
                
                elif action == 'force_summary':
                    # Force generate daily summary
                    target_date = request.json.get('date') if request.json else None
                    if target_date:
                        target_date = datetime.fromisoformat(target_date).date()
                    else:
                        target_date = date.today()
                    
                    success = self.app_instance.force_daily_summary(target_date)
                    if success:
                        return jsonify({'success': True, 'message': f'Summary generated for {target_date}'})
                    else:
                        return jsonify({'success': False, 'message': 'Summary generation failed'})
                
                elif action == 'upload_docs':
                    # Force upload to Google Docs
                    target_date = request.json.get('date') if request.json else None
                    if target_date:
                        target_date = datetime.fromisoformat(target_date).date()
                    else:
                        target_date = date.today()
                    
                    success = self._force_upload_docs_for_date(target_date)
                    if success:
                        return jsonify({'success': True, 'message': f'Google Docs upload completed for {target_date}'})
                    else:
                        return jsonify({'success': False, 'message': f'Google Docs upload failed for {target_date}'})
                
                elif action == 'generate_daily_transcript':
                    # Generate daily consolidated transcript
                    target_date = request.json.get('date') if request.json else None
                    if target_date:
                        target_date = datetime.fromisoformat(target_date).date()
                    else:
                        target_date = date.today()
                    
                    success = self.app_instance.generate_daily_transcript_file(target_date)
                    if success:
                        return jsonify({'success': True, 'message': f'Daily transcript generated for {target_date}'})
                    else:
                        return jsonify({'success': False, 'message': 'Daily transcript generation failed'})
                
                else:
                    return jsonify({'success': False, 'message': f'Unknown action: {action}'})
                    
            except Exception as e:
                self.logger.error(f"Control action {action} failed: {e}")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.flask_app.route('/api/logs')
        def api_logs():
            """Get recent log entries."""
            try:
                # Try to read recent log entries
                log_file = Path("transcription_app.log")
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Get last 50 lines
                        recent_lines = lines[-50:] if len(lines) > 50 else lines
                        return jsonify({'logs': recent_lines})
                else:
                    return jsonify({'logs': ['No log file found']})
            except Exception as e:
                return jsonify({'logs': [f'Error reading logs: {e}']})
        
        @self.flask_app.route('/api/upload', methods=['POST'])
        def api_upload():
            """Handle audio file uploads."""
            try:
                if 'audio_file' not in request.files:
                    return jsonify({'success': False, 'message': 'No audio file provided'})
                
                file = request.files['audio_file']
                if file.filename == '':
                    return jsonify({'success': False, 'message': 'No file selected'})
                
                # Process the uploaded file
                result = self._process_uploaded_audio(file)
                
                if result['success']:
                    return jsonify({
                        'success': True, 
                        'message': f"Audio file processed successfully: {result['transcript_preview']}",
                        'transcript_length': result['transcript_length']
                    })
                else:
                    return jsonify({'success': False, 'message': result['error']})
                    
            except Exception as e:
                self.logger.error(f"Error processing uploaded file: {e}")
                return jsonify({'success': False, 'message': str(e)})
    
    def _force_transcribe(self) -> None:
        """Force transcription of any pending audio."""
        try:
            # Get any completed audio segments
            segments = self.app_instance.audio_capture.get_completed_segments()
            for segment in segments:
                self.app_instance.transcription_service.queue_audio_segment(segment)
            
            self.logger.info(f"Queued {len(segments)} segments for transcription")
        except Exception as e:
            self.logger.error(f"Error forcing transcription: {e}")
    
    def _force_upload_docs(self) -> None:
        """Force upload recent summaries to Google Docs."""
        try:
            self.logger.info("Google Docs upload triggered manually")
            
            if not self.app_instance.config.google_docs.enabled:
                self.logger.warning("Google Docs integration is disabled")
                return
            
            # Try to upload recent summaries
            summary_dir = self.app_instance.config.get_storage_paths()['summaries']
            if not summary_dir.exists():
                self.logger.warning("No summaries directory found")
                return
            
            # Find recent summary files
            summary_files = list(summary_dir.glob("summary_*.json"))
            if not summary_files:
                self.logger.warning("No summary files found to upload")
                return
            
            # Upload the most recent summaries
            uploaded_count = 0
            for summary_file in sorted(summary_files)[-5:]:  # Last 5 summaries
                try:
                    # Load summary
                    with open(summary_file, 'r') as f:
                        summary_data = json.loads(f.read())
                    
                    # Extract date from filename
                    date_str = summary_file.stem.replace('summary_', '')
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Get transcript text
                    daily_text = self.app_instance._get_daily_transcript(target_date)
                    
                    # Create DailySummary object
                    from .summarization import DailySummary
                    
                    # Convert string dates back to proper objects
                    summary_data['date'] = datetime.fromisoformat(summary_data['date']).date()
                    summary_data['created_at'] = datetime.fromisoformat(summary_data['created_at'])
                    
                    summary = DailySummary(**summary_data)
                    
                    # Upload to Google Docs
                    self.app_instance._upload_to_google_docs(target_date, daily_text, summary)
                    uploaded_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error uploading {summary_file}: {e}")
            
            self.logger.info(f"Uploaded {uploaded_count} summaries to Google Docs")
            
        except Exception as e:
            self.logger.error(f"Error forcing Google Docs upload: {e}")
    
    def _force_upload_docs_for_date(self, target_date: date) -> bool:
        """Force upload summary and transcript for a specific date to Google Docs."""
        try:
            self.logger.info(f"Google Docs upload triggered for {target_date}")
            
            if not self.app_instance.config.google_docs.enabled:
                self.logger.warning("Google Docs integration is disabled")
                return False
            
            # Check if summary exists for this date
            summary_dir = self.app_instance.config.get_storage_paths()['summaries']
            summary_file = summary_dir / f"summary_{target_date.strftime('%Y-%m-%d')}.json"
            
            summary = None
            if summary_file.exists():
                try:
                    # Load existing summary
                    with open(summary_file, 'r') as f:
                        summary_data = json.loads(f.read())
                    
                    # Create DailySummary object
                    from .summarization import DailySummary
                    
                    # Convert string dates back to proper objects
                    summary_data['date'] = datetime.fromisoformat(summary_data['date']).date()
                    summary_data['created_at'] = datetime.fromisoformat(summary_data['created_at'])
                    
                    summary = DailySummary(**summary_data)
                    self.logger.info(f"Found existing summary for {target_date}")
                    
                except Exception as e:
                    self.logger.error(f"Error loading summary for {target_date}: {e}")
            else:
                # Try to generate summary if it doesn't exist
                self.logger.info(f"No summary found for {target_date}, attempting to generate one")
                success = self.app_instance.force_daily_summary(target_date)
                if success:
                    # Try to load the newly generated summary
                    if summary_file.exists():
                        with open(summary_file, 'r') as f:
                            summary_data = json.loads(f.read())
                        
                        from .summarization import DailySummary
                        summary_data['date'] = datetime.fromisoformat(summary_data['date']).date()
                        summary_data['created_at'] = datetime.fromisoformat(summary_data['created_at'])
                        summary = DailySummary(**summary_data)
                    else:
                        self.logger.warning(f"Summary generation claimed success but file not found for {target_date}")
                else:
                    self.logger.warning(f"Could not generate summary for {target_date}")
            
            # Get transcript text
            daily_text = self.app_instance._get_daily_transcript(target_date)
            
            if not daily_text.strip():
                self.logger.warning(f"No transcript data found for {target_date}")
                return False
            
            # Upload to Google Docs
            self.app_instance._upload_to_google_docs(target_date, daily_text, summary)
            self.logger.info(f"Successfully uploaded to Google Docs for {target_date}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error uploading to Google Docs for {target_date}: {e}")
            return False
    
    def _get_uptime(self) -> str:
        """Get application uptime."""
        # This is a simple implementation - you might want to track start time
        return "Running"
    
    def _get_main_template(self) -> str:
        """Get the main HTML template."""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcription App Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #007bff;
        }
        .status-card.recording {
            border-left-color: #28a745;
        }
        .status-card.paused {
            border-left-color: #ffc107;
        }
        .status-card.error {
            border-left-color: #dc3545;
        }
        .status-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .status-value {
            font-size: 1.2em;
            color: #666;
        }
        .heartbeat {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #28a745;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        .heartbeat.stale {
            background: #dc3545;
            animation: none;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .btn-primary { background: #007bff; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        
        .upload-section {
            border: 2px dashed #ccc;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 10px 0;
        }
        
        .upload-section:hover {
            border-color: #007bff;
            background-color: #f8f9fa;
        }
        
        .upload-info {
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
            text-align: left;
        }
        
        .date-controls {
            display: flex;
            flex-direction: column;
            gap: 15px;
            align-items: flex-start;
        }
        
        .date-controls label {
            font-weight: bold;
            color: #333;
        }
        
        .date-input {
            padding: 8px 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
            width: 200px;
        }
        
        .date-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        #audioFileInput {
            margin: 10px 0;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            width: 100%;
            max-width: 400px;
        }
        .btn-danger { background: #dc3545; color: white; }
        .logs {
            background: #1e1e1e;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        .message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            display: none;
        }
        .message.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .message.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎤 Transcription App Dashboard</h1>
            <p>Monitor and control your always-on transcription service</p>
        </div>
        
        <div id="message" class="message"></div>
        
        <div class="status-grid">
            <div class="status-card" id="recording-status">
                <div class="status-title">
                    <span class="heartbeat" id="heartbeat"></span>
                    Recording Status
                </div>
                <div class="status-value" id="recording-value">Loading...</div>
            </div>
            
            <div class="status-card">
                <div class="status-title">Last Activity</div>
                <div class="status-value" id="last-activity">Loading...</div>
            </div>
            
            <div class="status-card">
                <div class="status-title">Transcription Queue</div>
                <div class="status-value" id="queue-size">Loading...</div>
            </div>
            
            <div class="status-card">
                <div class="status-title">Total Transcribed</div>
                <div class="status-value" id="total-transcribed">Loading...</div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-warning" onclick="pauseRecording()">⏸️ Pause Recording</button>
            <button class="btn btn-success" onclick="resumeRecording()">▶️ Resume Recording</button>
            <button class="btn btn-primary" onclick="forceTranscribe()">🔄 Process Audio Now</button>
            <button class="btn btn-primary" onclick="forceSummary()">📝 Generate Summary</button>
            <button class="btn btn-primary" onclick="generateDailyTranscript()">📋 Generate Daily Transcript</button>
            <button class="btn btn-primary" onclick="uploadDocs()">☁️ Upload to Google Docs</button>
        </div>
        
        <div class="card">
            <h3>📅 Historical Processing</h3>
            <p>Generate summaries and upload transcripts for previous dates</p>
            <div class="date-controls">
                <label for="targetDate">Select Date:</label>
                <input type="date" id="targetDate" class="date-input">
                <div class="date-buttons">
                    <button class="btn btn-primary" onclick="generateSummaryForDate()">📝 Generate Summary</button>
                    <button class="btn btn-primary" onclick="uploadDocsForDate()">☁️ Upload to Google Docs</button>
                    <button class="btn btn-secondary" onclick="generateTranscriptForDate()">📋 Generate Transcript</button>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>📁 Import Audio Files</h3>
            <p>Upload audio recordings from your phone or other devices</p>
            <div class="upload-section">
                <input type="file" id="audioFileInput" accept=".wav,.mp3,.m4a,.mp4,.flac,.ogg,.webm" multiple style="margin-bottom: 10px;">
                <br>
                <button class="btn btn-secondary" onclick="uploadAudioFiles()">🎤 Upload Audio Files</button>
                <div id="uploadStatus" style="margin-top: 10px;"></div>
            </div>
            <div class="upload-info">
                <small>
                    <strong>Supported formats:</strong> WAV, MP3, M4A, MP4, FLAC, OGG, WebM<br>
                    <strong>Filename parsing:</strong> Dates/times will be extracted from filenames when possible<br>
                    <strong>Examples:</strong> "Recording 2024-09-30 14:30.m4a", "20240930_143015.wav"
                </small>
            </div>
        </div>
        
        <div>
            <h3>Recent Logs</h3>
            <div class="logs" id="logs">Loading logs...</div>
        </div>
    </div>

    <script>
        let statusInterval;
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update recording status
                    const recordingCard = document.getElementById('recording-status');
                    const recordingValue = document.getElementById('recording-value');
                    const heartbeat = document.getElementById('heartbeat');
                    
                    if (data.recording && !data.paused) {
                        recordingCard.className = 'status-card recording';
                        recordingValue.textContent = 'Recording';
                        heartbeat.className = 'heartbeat';
                    } else if (data.paused) {
                        recordingCard.className = 'status-card paused';
                        recordingValue.textContent = 'Paused';
                        heartbeat.className = 'heartbeat stale';
                    } else {
                        recordingCard.className = 'status-card error';
                        recordingValue.textContent = 'Stopped';
                        heartbeat.className = 'heartbeat stale';
                    }
                    
                    // Update other status
                    const heartbeatAgo = Math.floor(data.heartbeat_ago / 60);
                    document.getElementById('last-activity').textContent = 
                        heartbeatAgo < 1 ? 'Just now' : `${heartbeatAgo} min ago`;
                    
                    document.getElementById('queue-size').textContent = 
                        data.transcription_queue_size || 0;
                    
                    document.getElementById('total-transcribed').textContent = 
                        data.total_transcribed || 0;
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                    showMessage('Error fetching status', 'error');
                });
        }
        
        function updateLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const logsElement = document.getElementById('logs');
                    logsElement.textContent = data.logs.join('');
                    logsElement.scrollTop = logsElement.scrollHeight;
                })
                .catch(error => {
                    console.error('Error fetching logs:', error);
                });
        }
        
        function showMessage(text, type) {
            const messageEl = document.getElementById('message');
            messageEl.textContent = text;
            messageEl.className = `message ${type}`;
            messageEl.style.display = 'block';
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 3000);
        }
        
        function controlAction(action, data = {}) {
            fetch(`/api/control/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(data.message, 'success');
                    updateStatus(); // Refresh status
                } else {
                    showMessage(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('Action failed', 'error');
            });
        }
        
        function pauseRecording() {
            controlAction('pause');
        }
        
        function resumeRecording() {
            controlAction('resume');
        }
        
        function forceTranscribe() {
            controlAction('force_transcribe');
        }
        
        function forceSummary() {
            const today = new Date().toISOString().split('T')[0];
            controlAction('force_summary', { date: today });
        }
        
        function generateDailyTranscript() {
            const today = new Date().toISOString().split('T')[0];
            controlAction('generate_daily_transcript', { date: today });
        }
        
        function uploadDocs() {
            controlAction('upload_docs');
        }
        
        // Date-specific functions
        function generateSummaryForDate() {
            const dateInput = document.getElementById('targetDate');
            if (!dateInput.value) {
                showMessage('Please select a date first', 'error');
                return;
            }
            controlAction('force_summary', { date: dateInput.value });
        }
        
        function uploadDocsForDate() {
            const dateInput = document.getElementById('targetDate');
            if (!dateInput.value) {
                showMessage('Please select a date first', 'error');
                return;
            }
            controlAction('upload_docs', { date: dateInput.value });
        }
        
        function generateTranscriptForDate() {
            const dateInput = document.getElementById('targetDate');
            if (!dateInput.value) {
                showMessage('Please select a date first', 'error');
                return;
            }
            controlAction('generate_daily_transcript', { date: dateInput.value });
        }
        
        function uploadAudioFiles() {
            const fileInput = document.getElementById('audioFileInput');
            const statusDiv = document.getElementById('uploadStatus');
            
            if (fileInput.files.length === 0) {
                statusDiv.innerHTML = '<span style="color: red;">Please select audio files to upload</span>';
                return;
            }
            
            statusDiv.innerHTML = '<span style="color: blue;">Uploading files...</span>';
            
            // Upload files one by one
            uploadFileSequentially(fileInput.files, 0, statusDiv);
        }
        
        function uploadFileSequentially(files, index, statusDiv) {
            if (index >= files.length) {
                statusDiv.innerHTML = '<span style="color: green;">✅ All files uploaded successfully!</span>';
                // Clear the file input
                document.getElementById('audioFileInput').value = '';
                return;
            }
            
            const file = files[index];
            const formData = new FormData();
            formData.append('audio_file', file);
            
            statusDiv.innerHTML = `<span style="color: blue;">Uploading ${file.name} (${index + 1}/${files.length})...</span>`;
            
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    statusDiv.innerHTML = `<span style="color: green;">✅ ${file.name}: ${data.message}</span>`;
                    // Continue with next file after a short delay
                    setTimeout(() => uploadFileSequentially(files, index + 1, statusDiv), 1000);
                } else {
                    statusDiv.innerHTML = `<span style="color: red;">❌ ${file.name}: ${data.message}</span>`;
                    // Continue with next file even if this one failed
                    setTimeout(() => uploadFileSequentially(files, index + 1, statusDiv), 2000);
                }
            })
            .catch(error => {
                statusDiv.innerHTML = `<span style="color: red;">❌ ${file.name}: Upload failed - ${error}</span>`;
                // Continue with next file even if this one failed
                setTimeout(() => uploadFileSequentially(files, index + 1, statusDiv), 2000);
            });
        }
        
        // Set default date to yesterday
        function setDefaultDate() {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const dateString = yesterday.toISOString().split('T')[0];
            document.getElementById('targetDate').value = dateString;
        }
        
        // Start updating status and logs
        updateStatus();
        updateLogs();
        setDefaultDate();
        statusInterval = setInterval(updateStatus, 30000); // Update every 30 seconds
        setInterval(updateLogs, 60000); // Update logs every 60 seconds
    </script>
</body>
</html>
        '''
    
    def _process_uploaded_audio(self, file) -> Dict[str, Any]:
        """Process an uploaded audio file."""
        try:
            import tempfile
            import os
            from datetime import datetime
            from pathlib import Path
            
            # Validate file type
            allowed_extensions = {'.wav', '.mp3', '.m4a', '.mp4', '.flac', '.ogg', '.webm'}
            file_ext = Path(file.filename).suffix.lower()
            
            if file_ext not in allowed_extensions:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_ext}. Supported: {", ".join(allowed_extensions)}'
                }
            
            # Extract date/time from filename or use current time
            timestamp = self._extract_timestamp_from_filename(file.filename)
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                file.save(temp_file.name)
                temp_path = Path(temp_file.name)
            
            try:
                # Convert to WAV if needed and create AudioSegment
                audio_segment = self._create_audio_segment_from_file(temp_path, timestamp)
                
                if not audio_segment:
                    return {'success': False, 'error': 'Failed to process audio file'}
                
                # Queue for transcription
                self.app_instance.transcription_service.queue_audio_segment(audio_segment)
                
                # Get file info for response
                file_size = temp_path.stat().st_size
                duration_estimate = file_size / 32000  # Rough estimate
                
                return {
                    'success': True,
                    'transcript_preview': f'Queued for transcription ({duration_estimate:.1f}s estimated)',
                    'transcript_length': 0,
                    'timestamp': timestamp.isoformat(),
                    'filename': file.filename
                }
                
            finally:
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
                    
        except Exception as e:
            self.logger.error(f"Error processing uploaded audio: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_timestamp_from_filename(self, filename: str) -> datetime:
        """Extract timestamp from filename or return current time."""
        import re
        from datetime import datetime
        
        # Try various filename patterns
        patterns = [
            # Voice memos: \"Recording 2024-09-30 14:30:15.m4a\"
            r'(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):(\d{2})',
            # Voice memos: \"Recording 2024-09-30 14:30.m4a\"
            r'(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2})',
            # Date only: \"2024-09-30.wav\"
            r'(\d{4}-\d{2}-\d{2})',
            # Timestamp: \"20240930_143015.wav\"
            r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})',
            # Timestamp: \"20240930_1430.wav\"
            r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 4:  # Date + hour:minute
                        date_str, hour, minute = groups[0], groups[1], groups[2]
                        return datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
                    elif len(groups) == 5:  # Date + hour:minute:second
                        date_str, hour, minute, second = groups[0], groups[1], groups[2], groups[3]
                        return datetime.strptime(f"{date_str} {hour}:{minute}:{second}", "%Y-%m-%d %H:%M:%S")
                    elif len(groups) == 1:  # Date only
                        date_str = groups[0]
                        return datetime.strptime(f"{date_str} 12:00:00", "%Y-%m-%d %H:%M:%S")
                    elif len(groups) == 6:  # YYYYMMDD_HHMMSS
                        year, month, day, hour, minute, second = groups
                        return datetime.strptime(f"{year}-{month}-{day} {hour}:{minute}:{second}", "%Y-%m-%d %H:%M:%S")
                    elif len(groups) == 5:  # YYYYMMDD_HHMM
                        year, month, day, hour, minute = groups
                        return datetime.strptime(f"{year}-{month}-{day} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
        
        # If no pattern matches, use current time
        self.logger.info(f"Could not extract timestamp from filename '{filename}', using current time")
        return datetime.now()
    
    def _create_audio_segment_from_file(self, file_path: Path, timestamp: datetime) -> Optional['AudioSegment']:
        """Create an AudioSegment from an uploaded file."""
        try:
            from .audio_capture import AudioSegment
            import subprocess
            import tempfile
            
            # Convert to WAV format if needed
            if file_path.suffix.lower() != '.wav':
                # Use ffmpeg to convert to WAV
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_file:
                    wav_path = Path(wav_file.name)
                
                # Convert using ffmpeg
                cmd = [
                    'ffmpeg', '-i', str(file_path),
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',      # Mono
                    '-y',            # Overwrite output
                    str(wav_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"FFmpeg conversion failed: {result.stderr}")
                    return None
                
                source_path = wav_path
            else:
                source_path = file_path
            
            # Get audio duration
            duration = self._get_audio_duration(source_path)
            
            # Move to audio directory
            audio_dir = self.app_instance.config.get_storage_paths()['audio']
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"uploaded_{timestamp.strftime('%Y%m%d_%H%M%S')}.wav"
            final_path = audio_dir / filename
            
            # Move file to audio directory
            import shutil
            shutil.move(str(source_path), str(final_path))
            
            # Create AudioSegment
            audio_segment = AudioSegment(
                file_path=final_path,
                start_time=timestamp,
                end_time=timestamp,  # Will be updated after processing
                duration=duration,
                sample_rate=16000
            )
            
            self.logger.info(f"Created audio segment from uploaded file: {filename} ({duration:.1f}s)")
            return audio_segment
            
        except Exception as e:
            self.logger.error(f"Error creating audio segment from file: {e}")
            return None
    
    def _get_audio_duration(self, file_path: Path) -> float:
        """Get audio file duration in seconds."""
        try:
            import subprocess
            
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                # Fallback: estimate from file size
                file_size = file_path.stat().st_size
                return file_size / 32000  # Rough estimate for 16kHz mono
                
        except Exception as e:
            self.logger.error(f"Error getting audio duration: {e}")
            # Fallback: estimate from file size
            file_size = file_path.stat().st_size
            return file_size / 32000