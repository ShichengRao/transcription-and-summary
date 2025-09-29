# Installation Troubleshooting Guide

## Quick Fixes for Common Issues

### 1. PyTorch Installation Issues

**Error:** `Could not find a version that satisfies the requirement torch>=2.0.0`
**Error:** `ERROR: Could not find a version that satisfies the requirement torch (from versions: none)`

**Solutions by Platform:**

**macOS (your issue):**
```bash
# The CPU index URL doesn't work on macOS - use standard installation
pip install torch torchaudio
pip install -r requirements-cpu.txt

# If that fails, try specific versions:
pip install torch==2.0.1 torchaudio==2.0.2
pip install -r requirements-cpu.txt

# Or use the macOS-specific installer:
python install_macos.py
```

**Linux/Windows:**
```bash
# CPU-only PyTorch (works on Linux/Windows)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-cpu.txt
```

**Any Platform:**
```bash
# Minimal installation (no PyTorch)
pip install -r requirements-minimal.txt
pip install openai-whisper

# Smart installer
python install.py
```

### 2. Python Version Issues

**Error:** `Requires-Python >=3.8,<3.12`

**Check your Python version:**
```bash
python --version
```

**Solutions:**
- **Python 3.7 or older:** Upgrade to Python 3.8+
- **Python 3.12+:** Use `requirements-minimal.txt` or `requirements-cpu.txt`
- **Python 3.8-3.11:** Use standard `requirements.txt`

### 3. Platform-Specific Issues

#### macOS (Intel and Apple Silicon M1/M2/M3)
```bash
# Install system dependencies
brew install ffmpeg portaudio

# Method 1: Standard PyTorch (recommended for macOS)
pip install torch torchaudio
pip install -r requirements-cpu.txt

# Method 2: If Method 1 fails, try specific versions
pip install torch==2.0.1 torchaudio==2.0.2
pip install -r requirements-cpu.txt

# Method 3: Minimal installation (no PyTorch)
pip install -r requirements-minimal.txt
pip install openai-whisper

# Method 4: Use conda instead of pip
conda install pytorch torchaudio -c pytorch
pip install -r requirements-cpu.txt
```

#### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-dev build-essential ffmpeg portaudio19-dev libasound2-dev

# Then install Python packages
pip install -r requirements.txt
```

#### Windows
```bash
# Install Visual C++ Build Tools first
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Use CPU-only installation
pip install -r requirements-cpu.txt
```

### 4. Virtual Environment Issues

**Start fresh:**
```bash
# Remove old environment
rm -rf venv

# Create new environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
python install.py
```

### 5. Dependency Conflicts

**Clean installation:**
```bash
# Uninstall conflicting packages
pip uninstall torch torchaudio faster-whisper

# Install step by step
pip install -r requirements-minimal.txt
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install faster-whisper
```

## Installation Options Explained

### Option 1: Full Installation (`requirements.txt`)
- **Best for:** Python 3.8-3.11, good internet, powerful machine
- **Includes:** All features, latest versions
- **Size:** ~2-3GB download

### Option 2: CPU-Only (`requirements-cpu.txt`)
- **Best for:** Any system, no GPU needed
- **Includes:** All features, CPU-optimized
- **Size:** ~1-2GB download

### Option 3: Minimal (`requirements-minimal.txt`)
- **Best for:** Older Python, limited resources, quick setup
- **Includes:** AI summarization only, no local transcription
- **Size:** ~100MB download

### Option 4: Smart Installer (`install.py`)
- **Best for:** Automatic detection and installation
- **Includes:** Detects best option for your system
- **Size:** Varies based on detection

## Testing Your Installation

```bash
# Test what's working
python test_installation.py

# Test specific components
python -m src.cli test audio
python -m src.cli status
```

## Minimal Working Setup

If all else fails, here's the absolute minimum:

```bash
pip install openai anthropic PyYAML python-dotenv rich
```

Then configure for AI-only mode:
```yaml
# config.yaml
transcription:
  model_size: "disabled"

summary:
  provider: "openai"  # or "claude"
```

## Getting Help

1. **Check the logs:** Look for specific error messages
2. **Test components:** Use `python test_installation.py`
3. **Try minimal setup:** Start with `requirements-minimal.txt`
4. **Check Python version:** Ensure 3.8-3.11 for best compatibility
5. **Update pip:** `pip install --upgrade pip`

## Alternative Transcription Methods

If you can't install faster-whisper:

### Option A: OpenAI Whisper
```bash
pip install openai-whisper
```

### Option B: Cloud-based transcription
Use OpenAI's Whisper API instead of local processing:
```yaml
# config.yaml
transcription:
  provider: "openai_api"  # Use cloud instead of local
```

### Option C: External tools
Use external transcription tools and import the text files.

## Success Indicators

You'll know the installation worked when:
- ✅ `python test_installation.py` shows mostly green checkmarks
- ✅ `python -m src.cli status` shows configuration details
- ✅ No import errors when running `python -m src.main --help`

## Still Having Issues?

Create a GitHub issue with:
1. Your Python version (`python --version`)
2. Your operating system
3. The exact error message
4. Output of `python test_installation.py`