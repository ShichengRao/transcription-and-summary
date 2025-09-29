# Always-On Local Transcriber & Summarizer

A cross-platform, privacy-focused tool that continuously transcribes microphone input, generates daily summaries, and syncs to Google Docs.

## Features

- **🎤 Continuous Recording**: 24/7 background audio capture with privacy controls
- **🔒 Local-First**: Speech-to-text processing runs entirely on your device
- **📝 Smart Transcription**: Powered by OpenAI Whisper for accurate transcription
- **📊 Daily Summaries**: AI-generated summaries of your daily conversations
- **☁️ Cloud Sync**: Automatic upload to Google Docs with organized folder structure
- **⏸️ Privacy Controls**: Easy pause/resume with system tray integration
- **🔧 Configurable**: Extensive customization options for all features

## Quick Start

1. **Install System Dependencies**
   ```bash
   # macOS
   brew install python3 ffmpeg portaudio
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install python3 python3-pip ffmpeg portaudio19-dev
   ```

2. **Setup Project**
   ```bash
   git clone https://github.com/abnew123/transcription-and-summary.git
   cd transcription-and-summary
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   
   # macOS users (recommended)
   python install_macos.py
   
   # Other platforms - use smart installer
   python install.py
   
   # Or manual installation
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your AI API key (OpenAI or Claude)
   ```

4. **Run the Application**
   ```bash
   python -m src.main
   ```

For detailed setup instructions, see [SETUP.md](SETUP.md).

### 🚨 Installation Issues?

If you encounter dependency errors:

```bash
# Quick fix for macOS PyTorch issues
python quick_fix_macos.py

# Or try diagnostic + PyTorch-free installation
python diagnose_python.py
python install_no_torch.py

# Test what's working
python test_installation.py
```

**Common fixes:**
- **Python 3.13+**: Downgrade to Python 3.12 (PyTorch not yet compatible)
- **NumPy 2.x issues**: Use `pip install "numpy<2.0.0"`
- **PyTorch won't install**: Use `python install_no_torch.py` (cloud transcription)
- **macOS issues**: Use `python quick_fix_macos.py`
- **Any platform**: `pip install -r requirements-no-torch.txt`

## Configuration

The application uses a `config.yaml` file for all settings. On first run, a default configuration will be created. Key settings include:

- **Audio**: Sample rate, chunk duration, silence detection
- **Transcription**: Model size, language, compute device
- **Summary**: AI provider, model selection, scheduling
- **Google Docs**: Folder organization, document templates
- **Storage**: Local file management and cleanup
- **UI**: System tray, notifications, dashboard

## Privacy & Security

- All audio processing happens locally on your device
- Raw audio files are automatically cleaned up after transcription
- Transcripts are stored locally before optional cloud sync
- Pause/resume controls for sensitive conversations
- Configurable keyword filtering for privacy

## System Requirements

- Python 3.9+
- 4GB+ RAM (for Whisper models)
- Microphone access
- Internet connection (for AI summaries and Google Docs sync)

## Development

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed development roadmap and architecture.

## License

MIT License - see LICENSE file for details.