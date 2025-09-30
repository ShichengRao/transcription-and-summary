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
            
            # Start Flask in a separate thread
            flask_thread = threading.Thread(
                target=lambda: self.flask_app.run(
                    host=self.host, 
                    port=self.port, 
                    debug=False, 
                    use_reloader=False,
                    threaded=True
                ),
                daemon=True
            )
            flask_thread.start()
            
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
                    self._force_upload_docs()
                    return jsonify({'success': True, 'message': 'Google Docs upload triggered'})
                
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
            # This would trigger upload of recent summaries
            # For now, just log the action
            self.logger.info("Google Docs upload triggered manually")
        except Exception as e:
            self.logger.error(f"Error forcing Google Docs upload: {e}")
    
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
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
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
            <button class="btn btn-primary" onclick="uploadDocs()">☁️ Upload to Google Docs</button>
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
        
        function uploadDocs() {
            controlAction('upload_docs');
        }
        
        // Start updating status and logs
        updateStatus();
        updateLogs();
        statusInterval = setInterval(updateStatus, 5000); // Update every 5 seconds
        setInterval(updateLogs, 10000); // Update logs every 10 seconds
    </script>
</body>
</html>
        '''