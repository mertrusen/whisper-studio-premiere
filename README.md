# Whisper Studio — Premiere Pro Extension

Local AI subtitles, audio cleanup, silence cutting & auto-zoom for **Adobe Premiere
Pro**. 100% offline & free (no paid APIs). EN / TR interface.

A standalone desktop version (for CapCut / non-Premiere users) lives at
**[whisper-studio-desktop](https://github.com/mertrusen/whisper-studio-desktop)**.

## Features
- 🎬 Transcribe the In/Out selection → editable subtitle segments (WhisperX / mlx / openai-whisper)
- ✂️ Auto-format, smart split, karaoke (.ass), custom dictionary, filler removal, profanity filter
- ✂️ **Edit**: mark/cut silences (ripple), Auto Zoom (Motion push-in)
- 🔊 **Audio**: denoise + EBU R128 loudness normalize
- ⬇ Export SRT / VTT / ASS / TXT, send captions to the timeline (caption track or styled MOGRT graphics)
- 🌍 English / Turkish UI + hover tooltips

## Install
1. Copy this folder to the Adobe CEP extensions folder:
   - **macOS:** `~/Library/Application Support/Adobe/CEP/extensions/com.whisper.studio`
   - **Windows:** `%APPDATA%\Adobe\CEP\extensions\com.whisper.studio`
2. Enable unsigned extensions (one time):
   - **macOS:** `defaults write com.adobe.CSXS.11 PlayerDebugMode 1` (also try CSXS.10/12)
   - **Windows:** registry `HKEY_CURRENT_USER\Software\Adobe\CSXS.11` → `PlayerDebugMode` = `1` (string)
3. Restart Premiere → **Window → Extensions → Whisper Studio**.

## Requirements (installed once, guided by the Setup tab)
```
# macOS
brew install python3 ffmpeg
pip3 install openai-whisper       # or: pip3 install whisperx

# Windows
winget install Gyan.FFmpeg
pip install openai-whisper
```
The **Setup** tab checks everything and offers one-click installs.

## Usage
Set In (I) / Out (O) on the timeline → **Transcribe** → edit segments → **Send to Premiere**.
