# Examples

Example configurations and usage patterns for the transcription application.

## Configuration Examples

### `config.yaml`
Example configuration file with common settings.

**Usage:**
```bash
# Copy to project root and customize
cp examples/config.yaml config.yaml
```

**Key sections:**

**Audio Configuration:**
```yaml
audio:
  sample_rate: 16000
  channels: 1
  chunk_duration: 30  # seconds
  silence_threshold: 0.02
  silence_duration: 5.0  # seconds before creating new file
  min_audio_duration: 3.0  # minimum clip length
```

**Transcription Settings:**
```yaml
transcription:
  provider: "local"  # or "openai_api"
  model_size: "tiny"  # tiny, base, small, medium, large
  language: "en"
```

**Summary Settings:**
```yaml
summary:
  provider: "claude"  # or "openai"
  model: "claude-3-haiku-20240307"
  daily_summary: true
  summary_time: "23:00"
```

## Configuration Tips

### For Testing
- Use `chunk_duration: 30` for faster testing
- Use `model_size: "tiny"` for speed
- Disable Google Docs: `enabled: false`

### For Production
- Use `chunk_duration: 300` (5 minutes)
- Use `model_size: "base"` or higher for accuracy
- Enable daily summaries
- Configure Google Docs integration

### For Low-Resource Systems
- Use `model_size: "tiny"`
- Increase `chunk_duration` to reduce processing frequency
- Disable hourly summaries
- Use `device: "cpu"`

### For High Accuracy
- Use `model_size: "large"`
- Lower `silence_threshold` to capture more audio
- Use `device: "cuda"` if GPU available
- Use Claude Opus for summaries

## Audio Sensitivity Tuning

### Too Many Files Created
Increase these values:
```yaml
silence_duration: 7.0  # Wait longer before splitting
min_audio_duration: 5.0  # Require longer clips
```

### Missing Audio
Decrease these values:
```yaml
silence_threshold: 0.01  # More sensitive
silence_duration: 3.0  # Split sooner
min_audio_duration: 1.0  # Allow shorter clips
```

### Background Noise Issues
```yaml
silence_threshold: 0.03  # Less sensitive
noise_gate_threshold: 0.02  # Higher noise gate
```

## Model Selection

### Whisper Models
- **tiny**: Fastest, least accurate, ~1GB RAM
- **base**: Good balance, ~1GB RAM (recommended)
- **small**: Better accuracy, ~2GB RAM
- **medium**: High accuracy, ~5GB RAM
- **large**: Best accuracy, ~10GB RAM

### Claude Models
- **haiku**: Fastest, cheapest, good quality (recommended)
- **sonnet**: Balanced performance
- **opus**: Highest quality, most expensive

## Environment Variables

Create a `.env` file:
```bash
# Required
CLAUDE_API_KEY=your_key_here

# Optional
OPENAI_API_KEY=your_key_here
GOOGLE_CREDENTIALS_PATH=credentials.json
```

## Common Configurations

### Minimal Setup (Testing)
```yaml
audio:
  chunk_duration: 30
transcription:
  model_size: "tiny"
summary:
  provider: "claude"
  model: "claude-3-haiku-20240307"
google_docs:
  enabled: false
```

### Production Setup (Balanced)
```yaml
audio:
  chunk_duration: 300
  silence_duration: 5.0
  min_audio_duration: 3.0
transcription:
  model_size: "base"
summary:
  provider: "claude"
  model: "claude-3-haiku-20240307"
  daily_summary: true
google_docs:
  enabled: true
```

### High-Quality Setup
```yaml
audio:
  chunk_duration: 300
  silence_threshold: 0.01
transcription:
  model_size: "medium"
summary:
  provider: "claude"
  model: "claude-3-sonnet-20240229"
  daily_summary: true
  hourly_summary: true
```
