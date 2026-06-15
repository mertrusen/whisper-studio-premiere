#!/usr/bin/env python3
"""
extract_audio.py
Usage: python3 extract_audio.py <clips_json_string> <output_wav_path>
"""

import sys, json, os, subprocess, tempfile, shutil, urllib.parse

FFMPEG_CANDIDATES = [
    "/opt/homebrew/bin/ffmpeg",
    "/opt/homebrew/sbin/ffmpeg",
    "/usr/local/bin/ffmpeg",
    "/usr/bin/ffmpeg",
]

# Homebrew is not in PATH when Premiere launches from Dock — search explicitly
FFMPEG_SEARCH_PATH = (
    "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin"
    ":/usr/bin:/bin:/usr/sbin:/sbin"
)

def find_ffmpeg():
    # 1. Absolute path check (works regardless of PATH)
    for p in FFMPEG_CANDIDATES:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    # 2. shutil.which with an extended search path
    found = shutil.which("ffmpeg", path=FFMPEG_SEARCH_PATH)
    if found:
        return found
    # 3. Last resort: let the OS try (will fail if PATH is minimal)
    return None

def normalize_path(p):
    """Decode file:// URLs and %20-style encoding that Premiere sometimes returns."""
    if not p:
        return p
    # Strip file:// prefix variants
    if p.startswith("file:///"):
        p = p[7:]
    elif p.startswith("file://"):
        p = p[6:]
    elif p.startswith("file:/"):
        p = p[5:]
    # URL-decode (handles %20 spaces etc.)
    try:
        p = urllib.parse.unquote(p)
    except Exception:
        pass
    return p

def extract_single(ffmpeg, clip, output_path):
    src_start = max(0.0, float(clip.get("srcStart", 0)))
    duration  = float(clip.get("duration", 0))

    if duration < 0.01:
        return False, f"duration={duration:.6f}s is too small for {clip.get('path','?')} — check In/Out points"

    cmd = [
        ffmpeg, "-y",
        "-ss", str(src_start),
        "-i",  clip["path"],
        "-t",  str(duration),
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        output_path,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300)
    except FileNotFoundError:
        return False, (
            f"ffmpeg not found at: {ffmpeg}\n"
            "Premiere may have launched without /opt/homebrew/bin in PATH.\n"
            "Fix: open Premiere from Terminal:  open -a 'Adobe Premiere Pro'\n"
            "Or install ffmpeg:  brew install ffmpeg"
        )
    if r.returncode != 0:
        err = r.stderr.decode(errors="replace")
        short = next((l for l in err.splitlines() if "No such file" in l or "Invalid" in l
                      or "Error" in l or "error" in l or "Unable" in l), err[-300:] if err else "unknown error")
        return False, short
    return True, None

def mix_clips(ffmpeg, clip_files, output_path, total_duration):
    inputs, delay_filters = [], []
    for i, (wav, offset) in enumerate(clip_files):
        inputs += ["-i", wav]
        delay_ms = max(0, int(offset * 1000))
        delay_filters.append(f"[{i}]adelay={delay_ms}|{delay_ms}[d{i}]")
    mix_map  = "".join(f"[d{i}]" for i in range(len(clip_files)))
    n        = len(clip_files)
    flt      = ";".join(delay_filters) + f";{mix_map}amix=inputs={n}:duration=longest:normalize=0[out]"
    cmd = [ffmpeg, "-y", *inputs,
           "-filter_complex", flt,
           "-map", "[out]",
           "-t", str(total_duration),
           "-ar", "16000", "-ac", "1",
           output_path]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300)
    except FileNotFoundError:
        return False, f"ffmpeg not found at: {ffmpeg}"
    return r.returncode == 0, r.stderr.decode(errors="replace")[-300:]

def run(clips_json_str, output_path):
    try:
        data     = json.loads(clips_json_str)
        clips    = data.get("clips", [])
        duration = float(data.get("duration", 0))
    except Exception as e:
        return {"success": False, "error": f"Bad input JSON: {e}"}

    if not clips:
        return {"success": False, "error": "No clips found in the selected In/Out range.\nMake sure your In/Out points overlap a clip on the timeline."}

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return {"success": False, "error": "ffmpeg not found.\nInstall with: brew install ffmpeg"}

    # Normalize all paths
    for c in clips:
        c["path"] = normalize_path(c.get("path", ""))

    # Check files actually exist
    missing = [c["path"] for c in clips if not os.path.exists(c["path"])]
    if missing:
        return {
            "success": False,
            "error":   f"Source media file not found on disk:\n{missing[0]}\n\nThe clip may have been moved or is offline. Re-link it in Premiere and try again."
        }

    tmpdir = tempfile.mkdtemp(prefix="whisper_ext_")
    try:
        if len(clips) == 1:
            ok, err = extract_single(ffmpeg, clips[0], output_path)
            if not ok:
                return {"success": False, "error": f"ffmpeg failed on:\n{clips[0]['path']}\n\n{err}"}
            return {"success": True}

        extracted = []
        errors    = []
        for i, clip in enumerate(clips):
            tmp_out = os.path.join(tmpdir, f"seg_{i}.wav")
            ok, err = extract_single(ffmpeg, clip, tmp_out)
            if ok:
                extracted.append((tmp_out, clip["timelineStart"]))
            else:
                errors.append(f"  [{i+1}] {os.path.basename(clip['path'])}: {err}")

        if not extracted:
            detail = "\n".join(errors) if errors else "All clips failed with no error output."
            return {"success": False, "error": f"All audio extractions failed.\n\n{detail}"}

        if len(extracted) == 1:
            shutil.move(extracted[0][0], output_path)
            return {"success": True}

        ok, err = mix_clips(ffmpeg, extracted, output_path, duration)
        if not ok:
            return {"success": False, "error": f"Audio mix failed:\n{err}"}
        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"success": False, "error": "Usage: extract_audio.py <clips_json> <output_path>"}))
        sys.exit(1)
    print(json.dumps(run(sys.argv[1], sys.argv[2]), ensure_ascii=False))
