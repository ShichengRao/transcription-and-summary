# Setup Guide

## Prerequisites

### System Requirements
- **Python 3.9-3.12** (⚠️ Python 3.13+ not yet supported by PyTorch)
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

# Upgrade pip first
pip install --upgrade pip

# Choose installation method (see options below)
```

### 3. Install Dependencies

#### Option 1: Quick Fix for PyTorch Issues (Recommended for your case)
```bash
python quick_fix_macos.py
```
Bypasses PyTorch entirely and uses cloud-based transcription.

#### Option 2: Smart Installer
```bash
python install.py
```
The smart installer will detect your system and choose the best installation method.

#### Option 3: PyTorch-Free Installation
```bash
pip install -r requirements-no-torch.txt
```
Uses cloud-based transcription instead of local processing.

#### Option 4: Manual Installation

**Full Installation (if you have compatible Python 3.8-3.11):**
```bash
pip install -r requirements.txt
```

**CPU-Only Installation (lighter, more compatible):**
```bash
pip install -r requirements-cpu.txt
```

**Minimal Installation (if you have dependency issues):**
```bash
pip install -r requirements-minimal.txt
# Then manually install transcription support:
pip install openai-whisper
```

#### Option 3: Platform-Specific Instructions

**macOS (Intel and Apple Silicon):**
```bash
# Install system dependencies first
brew install ffmpeg portaudio

# For macOS, use standard PyTorch installation (works better than CPU index)
pip install torch torchaudio

# Then install other requirements
pip install -r requirements-cpu.txt

# Alternative if above fails:
pip install torch==2.0.1 torchaudio==2.0.2
pip install -r requirements-cpu.txt
```

**Linux (Ubuntu/Debian):**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-dev build-essential ffmpeg portaudio19-dev

# Install Python packages
pip install -r requirements.txt
```

**Windows:**
```bash
# Install Visual C++ Build Tools first
# Then install packages
pip install -r requirements-cpu.txt
```

### 4. Configuration

#### Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your API keys
nano .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key for summarization (if using OpenAI)
- `CLAUDE_API_KEY`: Your Claude API key for summarization (if using Claude)
- `GOOGLE_CREDENTIALS_PATH`: Path to Google Cloud credentials file (optional)

Note: You only need one AI API key - either OpenAI or Claude, depending on your preference.

#### AI Provider Setup

**Option 1: OpenAI (GPT models)**
1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add to `.env`: `OPENAI_API_KEY=your_key_here`
3. Set in config: `provider: "openai"` and `model: "gpt-3.5-turbo"`

**Option 2: Claude (Anthropic)**
1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Add to `.env`: `CLAUDE_API_KEY=your_key_here`
3. Set in config: `provider: "claude"` and `model: "claude-3-haiku-20240307"`

Available Claude models:
- `claude-3-haiku-20240307` (fastest, most cost-effective)
- `claude-3-sonnet-20240229` (balanced performance)
- `claude-3-opus-20240229` (highest capability)

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

### 5. Test Installation

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
  provider: "openai"  # or "claude"
  model: "gpt-3.5-turbo"  # OpenAI: gpt-3.5-turbo, gpt-4, etc. Claude: claude-3-haiku-20240307, claude-3-sonnet-20240229, claude-3-opus-20240229
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

### Installation Issues

#### Python Version Compatibility
```bash
# Check your Python version
python --version

# Supported versions: 3.8, 3.9, 3.10, 3.11
# Python 3.12+ may have limited package compatibility
```

#### PyTorch Installation Errors
If you get errors about PyTorch versions:

```bash
# Try CPU-only installation
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Or use older compatible versions
pip install torch==1.13.1 torchaudio==0.13.1

# Alternative: Use minimal installation
pip install -r requirements-minimal.txt
pip install openai-whisper
```

#### Package Dependency Conflicts
```bash
# Create fresh virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Try minimal installation first
pip install -r requirements-minimal.txt

# Then add components one by one
pip install faster-whisper  # or openai-whisper
```

#### Platform-Specific Issues

**macOS Issues:**
```bash
# If you get compiler errors
xcode-select --install

# For Apple Silicon compatibility
export ARCHFLAGS="-arch arm64"
pip install --no-cache-dir package_name
```

**Linux Issues:**
```bash
# Missing system libraries
sudo apt-get install python3-dev build-essential
sudo apt-get install portaudio19-dev libasound2-dev

# Permission issues
sudo usermod -a -G audio $USER
```

**Windows Issues:**
```bash
# Install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Use pre-compiled wheels
pip install --only-binary=all package_name
```

### Runtime Issues

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
- **Model Download Fails**: Check internet connection and disk space

#### API Issues
- **OpenAI Errors**: Check API key and billing status
- **Claude Errors**: Verify API key and rate limits
- **Google Docs Errors**: Ensure credentials.json is valid

#### Permission Issues (macOS)
- Grant microphone access in System Preferences → Security & Privacy
- Allow terminal/application to access microphone

### Alternative Configurations

#### AI-Only Mode (No Local Transcription)
If you can't install transcription dependencies:

```yaml
# config.yaml
transcription:
  model_size: "disabled"  # Skip local transcription

summary:
  provider: "openai"  # or "claude"
  model: "gpt-3.5-turbo"
```

#### Lightweight Mode
For older/slower systems:

```yaml
audio:
  chunk_duration: 600  # 10 minutes instead of 5
  sample_rate: 8000    # Lower quality but faster

transcription:
  model_size: "tiny"   # Smallest model
  device: "cpu"        # Force CPU usage
```

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