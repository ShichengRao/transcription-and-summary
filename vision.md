# VISION: Always-On Local Transcriber & Summarizer

## Overview
This project provides a **cross-platform, open-source tool** that continuously transcribes microphone input on a user’s computer, summarizes transcripts daily, and syncs the results to cloud storage (Google Docs, Drive, or local).

Key values:
- **Local-first**: speech-to-text runs on-device for privacy.
- **Always-on**: designed to run in the background with minimal user interaction.
- **Extensible**: summaries can be exported to multiple platforms.

---

## Goals
- Continuous **24/7 transcription** of microphone input.
- **Local-first design** (raw audio + text stay on machine, cloud is optional).
- **Daily summaries** (digest of the day’s transcripts, with optional hourly summaries).
- **Flexible exports** (Google Docs, local Markdown, JSON).
- **Pause/resume controls** for user privacy.

---

## System Architecture

### 1. Audio Capture
- Tool: `ffmpeg` or `sounddevice` (Python).
- Method: rolling segments (e.g. 5 minutes per file).
- Each file is immediately queued for transcription.

### 2. Transcription Engine
- Default: [Whisper](https://github.com/openai/whisper) (or [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for efficiency).
- Configurable: allow other ASR backends (e.g. Vosk).
- Output: plain text, appended to a daily log file at:  
