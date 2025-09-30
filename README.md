# Local Transcription & Summary Tool

A privacy-focused macOS application that continuously transcribes microphone input and generates AI-powered daily summaries using Claude.

## ⚠️ Platform Support

**This tool is designed and tested exclusively for macOS.** Windows and Linux support is not provided or maintained.

## Features

- 🎤 **Continuous Recording**: 24/7 background audio capture
- 🔒 **Privacy-First**: All processing happens locally on your Mac
- 📝 **Smart Transcription**: Powered by OpenAI Whisper
- 🤖 **AI Summaries**: Daily summaries generated using Claude
- ☁️ **Google Docs Sync**: Optional automatic upload to Google Docs
- ⏸️ **Privacy Controls**: Easy pause/resume functionality

## Prerequisites

- **macOS** (Intel or Apple Silicon)
- **Python 3.9-3.12** (Python 3.13+ not yet supported)
- **Claude API Key** (get one at [console.anthropic.com](https://console.anthropic.com/))
- **Homebrew** (install at [brew.sh](https://brew.sh))

## Installation

### 1. Install System Dependencies

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python3 ffmpeg portaudio
```

### 2. Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/abnew123/transcription-and-summary.git
cd transcription-and-summary

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit the file with your Claude API key
nano .env
```

Add your Claude API key to the `.env` file:
```
CLAUDE_API_KEY=your_claude_api_key_here
```

### 4. Grant Microphone Permissions

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Microphone** from the left sidebar
3. Check the box next to **Terminal** (or your terminal app)
4. If prompted, restart your terminal

## Usage

### Start the Application

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run the application
python -m src.main
```

The application will:
1. Start recording audio in the background
2. Transcribe audio chunks every 5 minutes
3. Generate daily summaries at 11 PM
4. Save all data locally in the `transcripts/` folder

### Control the Application

- **Stop**: Press `Ctrl+C` in the terminal
- **Pause/Resume**: Use the system tray icon (when available)

### Generate Manual Summary

```bash
# Generate summary for yesterday
python -m src.cli generate-summary

# Generate summary for specific date
python -m src.cli generate-summary --date 2024-01-15
```

## Configuration

The application creates a `config.yaml` file on first run. Key settings:

```yaml
audio:
  sample_rate: 16000
  chunk_duration: 300  # 5 minutes
  silence_threshold: 0.01

transcription:
  model_size: "base"  # tiny, base, small, medium, large
  language: "en"
  device: "auto"  # auto, cpu, mps (Apple Silicon)

summary:
  provider: "claude"
  model: "claude-3-haiku-20240307"  # fastest, most cost-effective
  daily_summary: true
  summary_time: "23:00"

storage:
  base_dir: "transcripts"
  max_audio_age_days: 7
  max_transcript_age_days: 365
```

### Available Claude Models

- `claude-3-haiku-20240307` - Fastest and most cost-effective (recommended)
- `claude-3-sonnet-20240229` - Balanced performance and capability
- `claude-3-opus-20240229` - Highest capability (most expensive)

## Optional: Google Docs Integration

To automatically upload summaries to Google Docs:

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project

2. **Enable APIs**
   - Enable Google Docs API
   - Enable Google Drive API

3. **Create Credentials**
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download as `credentials.json` and place in project root

4. **Update Configuration**
   ```yaml
   google_docs:
     enabled: true
     folder_name: "Transcription Summaries"
   ```

5. **First Run Authentication**
   - Browser will open for OAuth consent
   - Grant permissions to access Google Docs and Drive

## File Structure

```
transcripts/
├── audio/           # Temporary audio files (auto-deleted)
├── transcripts/     # Daily transcript files
│   └── 2024-01-15/
│       ├── transcript_090000.txt
│       └── transcript_143000.txt
├── summaries/       # Generated summaries
│   └── summary_2024-01-15.json
└── config.yaml      # Application configuration
```

## Privacy & Security

- **Local Processing**: All audio transcription happens on your Mac
- **Automatic Cleanup**: Raw audio files are deleted after transcription
- **API Usage**: Only text summaries are sent to Claude (never audio)
- **Data Control**: All transcripts stored locally before optional cloud sync

## Troubleshooting

### Installation Issues

**Python Version Problems:**
```bash
# Check Python version
python3 --version

# Should be 3.9-3.12. If not, install correct version:
brew install python@3.11
```

**PyTorch Installation Errors:**
```bash
# For Apple Silicon Macs
pip install torch torchaudio

# For Intel Macs
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**Permission Errors:**
```bash
# Install Xcode command line tools
xcode-select --install

# For Apple Silicon, set architecture
export ARCHFLAGS="-arch arm64"
pip install --no-cache-dir package_name
```

### Runtime Issues

**No Audio Detected:**
- Check microphone permissions in System Preferences
- Verify microphone is working in other applications
- Try adjusting `silence_threshold` in config.yaml

**Transcription Errors:**
- Use smaller model (`tiny` or `base`) if running out of memory
- Check internet connection for model downloads
- Verify audio files are being created in `transcripts/audio/`

**Claude API Errors:**
- Verify API key is correct in `.env` file
- Check API usage limits at [console.anthropic.com](https://console.anthropic.com/)
- Ensure sufficient credits in your Anthropic account

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

This means:
- ✅ You can use, modify, and distribute this software
- ✅ You can use it for commercial purposes
- ⚠️ If you distribute modified versions, you must make the source code available
- ⚠️ If you run a modified version as a web service, you must make the source code available to users

See the [LICENSE](LICENSE) file for full details.

## Support

This is a personal project with limited support. For issues:

1. Check this README for common solutions
2. Review logs in `transcription_app.log`
3. Test components individually using `python -m src.cli test`
4. Search existing GitHub issues

**Note**: Support is provided on a best-effort basis for macOS only.