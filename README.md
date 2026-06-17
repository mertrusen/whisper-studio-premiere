# Subsper — Premiere Pro Extension

By **zipheron**. Local AI subtitles, audio cleanup, silence cutting & auto-zoom for
**Adobe Premiere Pro**. 100% offline & free. EN / TR interface.

> Prefer a standalone app (CapCut / no Premiere)? Get **Subsper Desktop**:
> https://github.com/mertrusen/subsper/releases (Windows `.exe` + macOS `.dmg`).

## Features
- 🎬 **Transcribe** — built-in engine (whisper.cpp). No In/Out needed → captions the
  whole timeline; set In/Out to limit to a range. Editable subtitle segments.
- ✂️ Smart split, karaoke (.ass), custom dictionary, filler removal, profanity filter
- ✂️ **Edit** — mark / cut silences (ripple), Auto Zoom (Motion push-in)
- 🔊 **Audio** — denoise + EBU R128 loudness normalize
- ⬇ Export SRT / VTT / ASS / TXT, send captions to the timeline (caption track or
  styled MOGRT graphics)
- 🌍 English / Turkish UI + hover tooltips
- ⭐ **Pro (optional):** speaker labels (WhisperX) — needs Python + a free HuggingFace token

## The engine (no terminal)
Transcription runs on **whisper.cpp + ffmpeg** — no Python needed for normal use.
Easiest way to provide it: **install Subsper Desktop** (it bundles the engine) and the
extension automatically reuses it. The speech model downloads itself once on first use.

> Already have `whisper-cli` + `ffmpeg` on PATH (e.g. `brew install whisper-cpp ffmpeg`)?
> Those work too. Only the optional **Pro** speaker-labels feature needs Python.

## Install
1. **Engine:** install **[Subsper Desktop](https://github.com/mertrusen/subsper/releases)**
   (provides whisper.cpp + ffmpeg). One install covers both apps.
2. **Enable unsigned extensions** (one time):
   - **macOS:** `defaults write com.adobe.CSXS.12 PlayerDebugMode 1` (also try CSXS.11)
   - **Windows:** registry `HKEY_CURRENT_USER\Software\Adobe\CSXS.12` → `PlayerDebugMode` = `1` (string)
3. **Copy this folder** to the Adobe CEP extensions folder:
   - **macOS:** `~/Library/Application Support/Adobe/CEP/extensions/com.whisper.studio`
   - **Windows:** `%APPDATA%\Adobe\CEP\extensions\com.whisper.studio`
4. Restart Premiere → **Window → Extensions → Subsper**.

## Usage
Open a sequence → **Transcribe** (whole timeline, or an In/Out range) → edit segments →
**Send to Premiere** (caption track or styled graphics) or **Export** SRT/VTT/ASS/TXT.

The **Setup** tab is optional — it's only for the Pro speaker-labels engine.
