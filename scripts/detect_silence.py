#!/usr/bin/env python3
"""
detect_silence.py
Usage: python3 detect_silence.py <wav_path> [noise_db] [min_dur]
  noise_db : silence threshold in dB (default -30)
  min_dur  : minimum silence length in seconds (default 0.6)

Output: { "success": bool, "silences": [{"start","end","dur"}], "error": str|null }
Times are relative to the start of the given audio file.
"""

import sys
import os
import json
import re
import subprocess
import shutil

FFMPEG_CANDIDATES = [
    "/opt/homebrew/bin/ffmpeg", "/opt/homebrew/sbin/ffmpeg",
    "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg",
]
FFMPEG_SEARCH_PATH = (
    "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin"
    ":/usr/bin:/bin:/usr/sbin:/sbin"
)


def find_ffmpeg():
    for p in FFMPEG_CANDIDATES:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    found = shutil.which("ffmpeg", path=FFMPEG_SEARCH_PATH)
    return found


def run(wav_path, noise_db, min_dur):
    if not os.path.exists(wav_path):
        return {"success": False, "error": f"Audio file not found: {wav_path}"}

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return {"success": False, "error": "ffmpeg not found. Install with: brew install ffmpeg"}

    cmd = [
        ffmpeg, "-i", wav_path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}",
        "-f", "null", "-",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300)
    except FileNotFoundError:
        return {"success": False, "error": f"ffmpeg not found at: {ffmpeg}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Silence detection timed out"}

    err = r.stderr.decode(errors="replace")
    silences = []
    start = None
    for line in err.splitlines():
        m1 = re.search(r"silence_start:\s*(-?[0-9.]+)", line)
        m2 = re.search(r"silence_end:\s*(-?[0-9.]+)", line)
        if m1:
            start = max(0.0, float(m1.group(1)))
        if m2 and start is not None:
            end = float(m2.group(1))
            if end > start:
                silences.append({
                    "start": round(start, 3),
                    "end":   round(end, 3),
                    "dur":   round(end - start, 3),
                })
            start = None

    return {"success": True, "silences": silences}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: detect_silence.py <wav_path> [noise_db] [min_dur]"}))
        sys.exit(1)

    wav   = sys.argv[1]
    noise = sys.argv[2] if len(sys.argv) > 2 else "-30"
    mind  = sys.argv[3] if len(sys.argv) > 3 else "0.6"
    print(json.dumps(run(wav, noise, mind), ensure_ascii=False))
