# Setup Guide

## Prerequisites

### System Requirements
- Python 3.9 or higher
- 4GB+ RAM (for Whisper models)
- Microphone access
- Internet connection (for AI summaries and Google Docs sync)

### Operating System Support
- macOS (recommended for the user's use case)
- Linux
- Windows

## Installation

### 1. Install System Dependencies

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python3 ffmpeg portaudio
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv ffmpeg portaudio19-dev libasound2-dev build-essential
```

#### Windows
1. Install Python 3.9+ from [python.org](https://python.org)
2. Install FFmpeg from [ffmpeg.org](https://ffmpeg.org)
3. Install Microsoft Visual C++ Build Tools

### 2. Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/abnew123/transcription-and-summary.git
cd transcription-and-summary

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configuration

#### Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your API keys
nano .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key for summarization
- `GOOGLE_CREDENTIALS_PATH`: Path to Google Cloud credentials file (optional)

#### Google Docs Setup (Optional)

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one

2. **Enable APIs**
   - Enable Google Docs API
   - Enable Google Drive API

3. **Create Credentials**
   - Go to "Credentials" in the sidebar
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file as `credentials.json`
   - Place in project root directory

4. **First Run Authentication**
   - On first run, a browser window will open for OAuth consent
   - Grant permissions to access Google Docs and Drive
   - Token will be saved for future use

### 4. Test Installation

```bash
# Test basic functionality
python test_sample.py

# Test individual components
python -m src.cli test audio
python -m src.cli test transcription path/to/audio.wav
python -m src.cli test google-docs
```

## Usage

### Basic Usage

#### Start the Application
```bash
# Run with default settings
python -m src.main

# Or use the CLI
python -m src.cli run
```

#### Control the Application
- **Pause/Resume**: The application will include system tray controls
- **Stop**: Press Ctrl+C in the terminal
- **Status**: `python -m src.cli status`

### Advanced Usage

#### Generate Manual Summary
```bash
# Generate summary for yesterday
python -m src.cli generate-summary

# Generate summary for specific date
python -m src.cli generate-summary --date 2024-01-15
```

#### Configuration Customization

Edit `config.yaml` (created on first run) to customize:

```yaml
audio:
  sample_rate: 16000
  chunk_duration: 300  # 5 minutes
  silence_threshold: 0.01
  device_id: null  # null for default device

transcription:
  model_size: "base"  # tiny, base, small, medium, large
  language: "en"
  device: "auto"  # auto, cpu, cuda

summary:
  provider: "openai"
  model: "gpt-3.5-turbo"
  daily_summary: true
  summary_time: "23:00"

google_docs:
  enabled: true
  folder_name: "Transcription Summaries"
  document_template: "Daily Transcript - {date}"

storage:
  base_dir: "transcripts"
  max_audio_age_days: 7
  max_transcript_age_days: 365
```

## Troubleshooting

### Common Issues

#### Audio Device Problems
```bash
# List available audio devices
python -m src.cli test audio

# Test specific device
# Edit config.yaml and set audio.device_id to the desired device ID
```

#### Transcription Model Issues
- **Out of Memory**: Use smaller model (`tiny` or `base`)
- **Slow Performance**: Use GPU if available, or smaller model
- **Language Issues**: Set specific language in config instead of "auto"

#### Google Docs Authentication
- Ensure `credentials.json` is in the project root
- Check that Google Docs and Drive APIs are enabled
- Verify OAuth consent screen is configured

#### Permission Issues (macOS)
- Grant microphone access in System Preferences → Security & Privacy
- Allow terminal/application to access microphone

### Performance Optimization

#### For Better Performance
- Use GPU for transcription if available
- Increase `chunk_duration` for less frequent processing
- Use smaller Whisper model for faster processing
- Adjust `silence_threshold` to avoid processing empty audio

#### For Better Accuracy
- Use larger Whisper model (`medium` or `large`)
- Set specific language instead of auto-detection
- Ensure good microphone quality and positioning

## File Structure

```
transcripts/
├── audio/           # Temporary audio files (auto-cleaned)
├── transcripts/     # Daily transcript files
│   └── 2024-01-15/
│       ├── transcript_090000.txt
│       └── transcript_143000.txt
├── summaries/       # Generated summaries
│   └── summary_2024-01-15.json
└── backups/         # Backup files
```

## Security and Privacy

### Local-First Design
- All audio processing happens on your device
- Raw audio files are automatically deleted after transcription
- Transcripts stored locally before optional cloud sync

### Data Handling
- Audio files are temporary and cleaned up automatically
- Transcripts contain timestamps but no other metadata
- Summaries are generated from text only, not audio

### API Usage
- OpenAI API: Only text is sent for summarization (no audio)
- Google Docs API: Only final transcripts and summaries are uploaded
- No data is shared with third parties beyond chosen services

## Support

For issues and questions:
1. Check this documentation
2. Review the logs in `transcription_app.log`
3. Test individual components using the CLI
4. Check GitHub issues for similar problems