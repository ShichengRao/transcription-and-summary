#!/bin/bash

# Transcription & Summary Tool - Easy Installation Script
# For macOS only

set -e  # Exit on any error

echo "🎙️  Transcription & Summary Tool - Easy Installer"
echo "=================================================="
echo ""

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This installer is for macOS only."
    echo "   Please follow the manual installation instructions in README.md"
    exit 1
fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for this session
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew is already installed"
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
brew install python3 ffmpeg portaudio

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python version: $python_version"

if [[ "$python_version" < "3.9" ]] || [[ "$python_version" > "3.12" ]]; then
    echo "⚠️  Warning: Python $python_version detected. Recommended: 3.9-3.12"
    echo "   You may encounter compatibility issues."
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    echo ""
    echo "🔑 IMPORTANT: You need to add your Claude API key to the .env file"
    echo "   1. Get an API key from: https://console.anthropic.com/"
    echo "   2. Edit .env file and replace 'your_claude_api_key_here' with your actual key"
    echo ""
else
    echo "✅ Environment file already exists"
fi

# Check microphone permissions
echo "🎤 Checking microphone permissions..."
echo "   Please grant microphone access when prompted"
echo "   Go to: System Preferences → Security & Privacy → Privacy → Microphone"
echo "   Check the box next to Terminal (or your terminal app)"

# Create launch script
echo "🚀 Creating launch script..."
cat > launch.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main
EOF

chmod +x launch.sh

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "   1. Add your Claude API key to the .env file"
echo "   2. Grant microphone permissions in System Preferences"
echo "   3. Run: ./launch.sh"
echo ""
echo "🌐 The web interface will be available at: http://127.0.0.1:8080"
echo ""
echo "💡 For help, see README.md or run: python diagnose_audio.py"