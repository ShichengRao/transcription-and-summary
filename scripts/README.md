# Scripts

Utility and diagnostic scripts for the transcription application.

## Installation Script

### `install.sh`
Automated installation script for setting up the application.

**Usage:**
```bash
./scripts/install.sh
```

**What it does:**
- Checks for required system dependencies (Python, ffmpeg, portaudio)
- Creates virtual environment
- Installs Python dependencies
- Sets up configuration files
- Guides through API key setup

## Diagnostic Scripts

### `diagnose_audio.py`
Basic audio diagnostics to verify microphone setup.

**Usage:**
```bash
python scripts/diagnose_audio.py
```

**Checks:**
- Module imports (sounddevice, config)
- Available audio devices
- Microphone recording test
- Audio level detection

### `diagnose_audio_detailed.py`
Comprehensive audio diagnostics with detailed analysis.

**Usage:**
```bash
python scripts/diagnose_audio_detailed.py
```

**Checks:**
- All basic checks from `diagnose_audio.py`
- Audio level analysis over time
- Silence threshold recommendations
- Configuration validation
- Real-time audio monitoring

**When to use:**
- Microphone not detecting audio
- Too many/too few audio segments being created
- Need to adjust silence thresholds
- Troubleshooting audio quality issues

## Utility Scripts

### `generate_daily_transcript.py`
Manually generate a consolidated daily transcript.

**Usage:**
```bash
# Generate for today
python scripts/generate_daily_transcript.py

# Generate for specific date (modify script)
python scripts/generate_daily_transcript.py
```

**What it does:**
- Combines all individual transcript files for a day
- Creates a single chronological transcript
- Useful for manual transcript generation outside scheduled times

## Troubleshooting

### Script Won't Run

**Permission denied:**
```bash
chmod +x scripts/install.sh
```

**Module not found:**
```bash
# Make sure you're in the project root
cd /path/to/transcription-and-summary

# Activate virtual environment
source venv/bin/activate

# Run script
python scripts/script_name.py
```

### Audio Diagnostics Show No Devices

1. Check system microphone permissions
2. Verify microphone is connected and working
3. Try running with sudo (not recommended for regular use)
4. Check if another application is using the microphone

### Installation Script Fails

1. Check Python version (3.9-3.12 required)
2. Ensure Homebrew is installed (macOS)
3. Check internet connection for package downloads
4. Review error messages for specific issues

## Development

These scripts are meant to be run from the project root directory. They import from the `src/` package, so the project structure must be maintained.

**Adding new scripts:**
1. Create script in `scripts/` directory
2. Add shebang: `#!/usr/bin/env python3`
3. Add docstring explaining purpose
4. Update this README
5. Make executable if needed: `chmod +x scripts/new_script.sh`
