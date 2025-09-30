# Desktop App Architecture for Mac App Store

## Overview
Transform the current Python-based transcription tool into a native macOS desktop application suitable for Mac App Store distribution.

## Architecture Options

### Option 1: Electron + Python Backend (Recommended)
**Structure:**
```
TranscriptionApp.app/
├── Contents/
│   ├── MacOS/
│   │   └── TranscriptionApp           # Electron main executable
│   ├── Resources/
│   │   ├── app/                       # Electron renderer
│   │   │   ├── index.html
│   │   │   ├── main.js
│   │   │   └── renderer.js
│   │   ├── backend/                   # Python backend (bundled)
│   │   │   ├── transcription-app      # PyInstaller executable
│   │   │   ├── models/                # Whisper models
│   │   │   └── lib/                   # Python libraries
│   │   └── icon.icns
│   ├── Info.plist
│   └── embedded.provisionprofile
```

**Pros:**
- Native macOS appearance and behavior
- Can leverage existing web UI
- Good performance for UI
- Easier to implement file drag-and-drop
- Better system integration (notifications, menu bar)

**Cons:**
- Larger app size (~200-300MB)
- Two separate processes to manage
- More complex build process

### Option 2: Tauri + Python Backend
**Lighter alternative to Electron using Rust**

**Pros:**
- Smaller app size (~50-100MB)
- Better performance
- Native system integration

**Cons:**
- Less mature ecosystem
- Steeper learning curve
- Still requires Python backend bundling

### Option 3: Native Swift App + Python Backend
**Pure native macOS application**

**Pros:**
- Best performance and integration
- Smallest app size
- True native experience

**Cons:**
- Complete UI rewrite required
- Longer development time
- Need Swift/macOS development expertise

## Recommended Approach: Electron + Python

### Phase 1: Basic Desktop App (2-3 weeks)

#### 1.1 Setup Electron Project
```bash
npm init
npm install electron electron-builder
npm install electron-store  # For settings persistence
```

#### 1.2 Main Process (main.js)
```javascript
const { app, BrowserWindow, Menu, Tray, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

class TranscriptionApp {
  constructor() {
    this.mainWindow = null;
    this.tray = null;
    this.pythonProcess = null;
  }

  createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js')
      },
      titleBarStyle: 'hiddenInset',  // macOS style
      icon: path.join(__dirname, 'assets/icon.png')
    });
  }

  startPythonBackend() {
    const backendPath = path.join(__dirname, 'backend/transcription-app');
    this.pythonProcess = spawn(backendPath, ['--port', '8080']);
  }

  createTray() {
    this.tray = new Tray(path.join(__dirname, 'assets/tray-icon.png'));
    // Tray menu implementation
  }
}
```

#### 1.3 Renderer Process (renderer.js)
- Load existing web UI
- Add native file dialogs
- Implement drag-and-drop for audio files
- Add native notifications

#### 1.4 Python Backend Bundling
```bash
# Use PyInstaller to create standalone executable
pyinstaller --onefile --windowed \
  --add-data "models:models" \
  --add-data "config:config" \
  src/main.py
```

### Phase 2: Mac App Store Preparation (1-2 weeks)

#### 2.1 App Store Requirements
- **Sandboxing**: Enable App Sandbox
- **Entitlements**: Configure required permissions
- **Code Signing**: Apple Developer certificate
- **Notarization**: Apple notarization process

#### 2.2 Required Entitlements
```xml
<!-- entitlements.plist -->
<key>com.apple.security.app-sandbox</key>
<true/>
<key>com.apple.security.device.microphone</key>
<true/>
<key>com.apple.security.network.client</key>
<true/>
<key>com.apple.security.files.user-selected.read-write</key>
<true/>
```

#### 2.3 Info.plist Configuration
```xml
<key>CFBundleIdentifier</key>
<string>com.yourcompany.transcription-app</string>
<key>CFBundleName</key>
<string>Transcription & Summary</string>
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access to transcribe audio recordings.</string>
```

### Phase 3: Enhanced Features (2-3 weeks)

#### 3.1 Native macOS Integration
- **Menu Bar App**: Always accessible from menu bar
- **Quick Actions**: Spotlight integration
- **Share Extensions**: Accept audio files from other apps
- **Shortcuts**: Siri Shortcuts integration

#### 3.2 Enhanced UI Features
- **Native File Picker**: Replace web file input
- **Drag & Drop**: Drop audio files anywhere on app
- **Progress Indicators**: Native progress bars
- **Notifications**: Native macOS notifications

#### 3.3 Settings Management
```javascript
// Using electron-store
const Store = require('electron-store');
const store = new Store({
  defaults: {
    apiKey: '',
    transcriptionModel: 'base',
    autoStart: true,
    notifications: true
  }
});
```

## File Structure

```
transcription-desktop/
├── package.json
├── main.js                    # Electron main process
├── preload.js                 # Preload script
├── renderer/                  # UI files
│   ├── index.html
│   ├── styles.css
│   └── renderer.js
├── assets/                    # Icons and resources
│   ├── icon.icns
│   ├── tray-icon.png
│   └── tray-icon@2x.png
├── backend/                   # Python backend (bundled)
│   └── transcription-app      # PyInstaller output
├── build/                     # Build configuration
│   ├── entitlements.plist
│   └── notarize.js
└── dist/                      # Built app output
```

## Build Process

### Development Build
```bash
npm run dev  # Start Electron in development mode
```

### Production Build
```bash
# 1. Bundle Python backend
pyinstaller transcription.spec

# 2. Build Electron app
npm run build

# 3. Code sign
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/TranscriptionApp.app

# 4. Create installer
npm run dist

# 5. Notarize
xcrun notarytool submit dist/TranscriptionApp.dmg --keychain-profile "notarytool-password"
```

## Mac App Store Submission

### 1. App Store Connect Setup
- Create app record
- Configure metadata
- Upload screenshots
- Set pricing

### 2. Build for App Store
```bash
# Use Mac App Store provisioning profile
electron-builder --mac --publish=never
```

### 3. Upload to App Store
```bash
xcrun altool --upload-app --type osx --file "dist/TranscriptionApp.pkg" --username "your@email.com" --password "@keychain:altool-password"
```

## User Experience Flow

### Installation
1. Download from Mac App Store
2. App appears in Applications folder
3. First launch triggers setup wizard

### Setup Wizard
1. Welcome screen
2. Microphone permission request
3. API key configuration
4. Basic settings (model size, etc.)
5. Optional Google Docs setup

### Daily Usage
1. App runs in menu bar
2. Click to open main window
3. Drag audio files to import
4. View transcripts and summaries
5. Export or share results

## Technical Considerations

### Performance
- Python backend runs as subprocess
- IPC communication between Electron and Python
- Efficient memory management for large audio files

### Security
- Sandboxed environment
- Secure API key storage (Keychain)
- No network access except for AI APIs

### Updates
- Auto-updater for non-App Store version
- App Store handles updates for store version

### Error Handling
- Graceful Python process management
- User-friendly error messages
- Automatic crash reporting (with user consent)

## Timeline & Milestones

### Week 1-2: Foundation
- [ ] Electron project setup
- [ ] Python backend bundling
- [ ] Basic window and tray
- [ ] IPC communication

### Week 3-4: Core Features
- [ ] Audio file import
- [ ] Transcription integration
- [ ] Settings management
- [ ] Basic UI polish

### Week 5-6: Mac Integration
- [ ] Sandboxing implementation
- [ ] Code signing setup
- [ ] Native notifications
- [ ] Menu bar integration

### Week 7-8: App Store Prep
- [ ] Entitlements configuration
- [ ] Notarization process
- [ ] App Store metadata
- [ ] Beta testing

### Week 9-10: Polish & Submit
- [ ] Final testing
- [ ] Documentation
- [ ] App Store submission
- [ ] Marketing materials

## Cost Considerations

### Development
- Apple Developer Program: $99/year
- Code signing certificate: Included in developer program
- Development time: ~10 weeks

### Ongoing
- App Store commission: 30% (15% for small developers)
- Maintenance and updates
- Customer support

## Success Metrics

### Technical
- App size < 300MB
- Launch time < 3 seconds
- Memory usage < 200MB idle
- 99%+ crash-free sessions

### User Experience
- 4.5+ App Store rating
- < 5% refund rate
- Positive user reviews
- Growing user base

This architecture provides a clear path from the current Python application to a professional Mac App Store application while maintaining all existing functionality and adding native macOS features.