#!/usr/bin/env python3
"""
enhance_audio.py
Usage: python3 enhance_audio.py <input_wav> <output_wav> [denoise] [normalize]
  denoise   : 0 | 1   (high-pass + FFT denoise)          default 1
  normalize : 0 | 1   (EBU R128 loudness normalization)  default 1

Output: { "success": bool, "output": str, "error": str|null }

All processing is local via ffmpeg (free). Safe for ffmpeg-only scripts to print
to stdout because we capture subprocess output and only emit our JSON at the end.
"""

import sys
import os
import json
import subprocess
import shutil

FFMPEG_CANDIDATES = [
    "/opt/homebrew/bin/ffmpeg", "/opt/homebrew/sbin/ffmpeg",
    "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg",
    # Windows common locations (desktop build / WinGet / choco)
    "C:/ffmpeg/bin/ffmpeg.exe",
    "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
]
FFMPEG_SEARCH_PATH = (
    "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin"
    ":/usr/bin:/bin:/usr/sbin:/sbin"
)


def find_ffmpeg():
    for p in FFMPEG_CANDIDATES:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    # PATH lookup (also covers Windows where ffmpeg is on PATH)
    found = shutil.which("ffmpeg")
    if found:
        return found
    return shutil.which("ffmpeg", path=FFMPEG_SEARCH_PATH)


def run(inp, outp, denoise, normalize):
    if not os.path.exists(inp):
        return {"success": False, "error": f"Input audio not found: {inp}"}

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return {"success": False, "error": "ffmpeg not found. Install with: brew install ffmpeg (mac) / winget install ffmpeg (win)"}

    filters = []
    if denoise:
        # Roll off rumble below 80 Hz, then FFT noise reduction.
        filters.append("highpass=f=80")
        filters.append("afftdn=nf=-25")
    if normalize:
        # EBU R128: -16 LUFS integrated, -1.5 dB true peak (good for web/social)
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

    af = ",".join(filters) if filters else "anull"

    cmd = [
        ffmpeg, "-y", "-i", inp,
        "-af", af,
        "-ar", "48000", "-ac", "2",
        outp,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=900)
    except FileNotFoundError:
        return {"success": False, "error": f"ffmpeg not found at: {ffmpeg}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Audio enhancement timed out"}

    if r.returncode != 0 or not os.path.exists(outp):
        err = r.stderr.decode(errors="replace")
        return {"success": False, "error": err[-500:] if err else "ffmpeg failed"}

    return {"success": True, "output": outp}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"success": False, "error": "Usage: enhance_audio.py <input_wav> <output_wav> [denoise] [normalize]"}))
        sys.exit(1)

    inp  = sys.argv[1]
    outp = sys.argv[2]
    den  = (len(sys.argv) <= 3) or sys.argv[3] in ("1", "true", "yes")
    nrm  = (len(sys.argv) <= 4) or sys.argv[4] in ("1", "true", "yes")

    print(json.dumps(run(inp, outp, den, nrm), ensure_ascii=False))
