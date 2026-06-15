#!/usr/bin/env python3
"""
transcribe.py
Usage: python3 transcribe.py <audio_path> [model] [language] [engine] [diarize]
  model    : turbo | large | large-v3 | medium | small | base   (default: turbo)
  language : tr | en | de | ... | auto                          (default: auto)
  engine   : auto | whisperx | mlx | openai                     (default: auto)
  diarize  : 0 | 1   (speaker labels, WhisperX only, needs HF token)  (default: 0)

Output: JSON { success, segments, text, language, engine, error }
  Each segment: { id, start, end, text, words:[{word,start,end,speaker?}], speaker? }

"auto" engine order: whisperx -> mlx-whisper -> openai-whisper.
All engines emit word-level timestamps so the UI can do karaoke + smart splitting.
"""

import sys
import json
import os


MODEL_ALIASES = {
    "turbo":    "large-v3-turbo",
    "large":    "large-v3",
    "large-v3": "large-v3",
    "medium":   "medium",
    "small":    "small",
    "base":     "base",
    "tiny":     "tiny",
}

MLX_REPOS = {
    "turbo":    "mlx-community/whisper-large-v3-turbo",
    "large-v3": "mlx-community/whisper-large-v3",
    "large":    "mlx-community/whisper-large-v3",
    "medium":   "mlx-community/whisper-medium",
    "small":    "mlx-community/whisper-small",
    "base":     "mlx-community/whisper-base",
    "tiny":     "mlx-community/whisper-tiny",
}

# WhisperX uses faster-whisper model names
WHISPERX_MODELS = {
    "turbo":    "large-v3",   # faster-whisper has no turbo; use large-v3
    "large":    "large-v3",
    "large-v3": "large-v3",
    "medium":   "medium",
    "small":    "small",
    "base":     "base",
    "tiny":     "tiny",
}


def _words_from(seg):
    """Normalize a segment's word list to [{word,start,end,speaker?}]."""
    words = []
    for w in seg.get("words", []) or []:
        try:
            ws = w.get("start")
            we = w.get("end")
            if ws is None or we is None:
                continue
            entry = {
                "word":  (w.get("word") or w.get("text") or "").strip(),
                "start": round(float(ws), 3),
                "end":   round(float(we), 3),
            }
            if w.get("speaker"):
                entry["speaker"] = w["speaker"]
            words.append(entry)
        except Exception:
            continue
    return words


def format_segments(raw_segments):
    out = []
    for seg in raw_segments:
        item = {
            "id":    seg.get("id", len(out)),
            "start": round(float(seg.get("start", 0) or 0), 3),
            "end":   round(float(seg.get("end",   0) or 0), 3),
            "text":  (seg.get("text", "") or "").strip(),
            "words": _words_from(seg),
        }
        if seg.get("speaker"):
            item["speaker"] = seg["speaker"]
        out.append(item)
    return out


# ── Engines ──────────────────────────────────────────────────────────────────

def transcribe_whisperx(audio_path, model_key, language, do_diarize=False):
    import whisperx
    device = "cpu"            # MPS support in whisperx is unreliable; CPU int8 is safe
    compute_type = "int8"
    model_name = WHISPERX_MODELS.get(model_key, "large-v3")
    notes = []

    model = whisperx.load_model(
        model_name, device, compute_type=compute_type,
        language=(language if language else None),
    )
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=16,
                              language=(language if language else None))
    lang = result.get("language", language or "")

    # Word-level alignment (no token needed). Best-effort: on failure we keep
    # segment-level timing so the run still succeeds.
    try:
        align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)
        result = whisperx.align(result["segments"], align_model, metadata,
                                audio, device, return_char_alignments=False)
    except Exception as e:
        notes.append("word alignment skipped: %s" % str(e)[:80])

    # Optional speaker diarization (needs a free HuggingFace token + accepted
    # pyannote model licenses). Fully isolated so it can never break the run.
    if do_diarize:
        token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
        if not token:
            notes.append("speaker labels need HUGGINGFACE_TOKEN env var")
        else:
            try:
                DiarizationPipeline = getattr(whisperx, "DiarizationPipeline", None)
                if DiarizationPipeline is None:
                    from whisperx.diarize import DiarizationPipeline
                diarize_model = DiarizationPipeline(use_auth_token=token, device=device)
                diarize_segments = diarize_model(audio)
                result = whisperx.assign_word_speakers(diarize_segments, result)
            except Exception as e:
                notes.append("diarization failed: %s" % str(e)[:80])

    segments = result.get("segments", []) or []
    text = " ".join((s.get("text", "") or "").strip() for s in segments).strip()
    return {"segments": segments, "text": text, "language": lang, "notes": notes}


def transcribe_mlx(audio_path, model_key, language):
    import mlx_whisper
    repo = MLX_REPOS.get(model_key, MLX_REPOS["turbo"])
    kwargs = {"path_or_hf_repo": repo, "word_timestamps": True}
    if language and language != "auto":
        kwargs["language"] = language
    return mlx_whisper.transcribe(audio_path, **kwargs)


def transcribe_openai(audio_path, model_key, language):
    import whisper
    model_name = MODEL_ALIASES.get(model_key, "large-v3-turbo")
    model = whisper.load_model(model_name)
    kwargs = {"word_timestamps": True}
    if language and language != "auto":
        kwargs["language"] = language
    return model.transcribe(audio_path, **kwargs)


# ── Orchestration ────────────────────────────────────────────────────────────

def run(audio_path, model_key="turbo", language=None, engine="auto", diarize=False):
    result = {
        "success": False, "engine": None, "language": "",
        "text": "", "segments": [], "error": None, "notes": [],
    }

    if not os.path.exists(audio_path):
        result["error"] = f"Audio file not found: {audio_path}"
        return result

    if language in ("auto", "", None):
        language = None

    # Build the ordered list of engines to try
    if engine == "whisperx":
        order = ["whisperx"]
    elif engine == "mlx":
        order = ["mlx"]
    elif engine == "openai":
        order = ["openai"]
    else:  # auto
        order = ["whisperx", "mlx", "openai"]

    errors = []
    for eng in order:
        try:
            if eng == "whisperx":
                out = transcribe_whisperx(audio_path, model_key, language, diarize)
            elif eng == "mlx":
                out = transcribe_mlx(audio_path, model_key, language)
            else:
                out = transcribe_openai(audio_path, model_key, language)

            result["engine"]   = {"whisperx": "whisperx", "mlx": "mlx-whisper", "openai": "openai-whisper"}[eng]
            result["success"]  = True
            result["text"]     = (out.get("text", "") or "").strip()
            result["language"] = out.get("language", "") or (language or "")
            result["segments"] = format_segments(out.get("segments", []) or [])
            notes = list(out.get("notes", []) or [])
            if errors:
                notes.extend(errors)
            result["notes"] = notes
            return result
        except ImportError as ie:
            errors.append(f"{eng}: not installed ({ie})")
        except Exception as e:
            errors.append(f"{eng}: {e}")

    result["error"] = "All engines failed:\n" + "\n".join(errors)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: transcribe.py <audio_path> [model] [language] [engine] [diarize]"}))
        sys.exit(1)

    audio   = sys.argv[1]
    model   = sys.argv[2] if len(sys.argv) > 2 else "turbo"
    lang    = sys.argv[3] if len(sys.argv) > 3 else None
    engine  = sys.argv[4] if len(sys.argv) > 4 else "auto"
    diarize = (len(sys.argv) > 5 and sys.argv[5] in ("1", "true", "yes"))

    # WhisperX (and some deps) log to stdout, which would corrupt our JSON.
    # Redirect fd 1 -> fd 2 during processing; restore only for the final JSON.
    _real_stdout = os.dup(1)
    os.dup2(2, 1)
    try:
        res = run(audio, model, lang, engine, diarize)
    finally:
        sys.stdout.flush()
        os.dup2(_real_stdout, 1)
        os.close(_real_stdout)

    sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
    sys.stdout.flush()
