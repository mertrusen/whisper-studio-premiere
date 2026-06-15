#!/usr/bin/env python3
"""
punctuate.py
Usage: python3 punctuate.py '<json>'
  input  : { "segments": [{"text": "..."}], "language": "tr" }
  output : { "success": bool, "segments": [{"text": "..."}], "error": str|null }

Restores missing punctuation + sentence casing using deepmultilingualpunctuation
(oliverguhr/fullstop multilingual model — fully offline after first download).
Works per-segment so subtitle timing is preserved.
"""

import sys
import os
import json
import re


def capitalize_sentences(text):
    """Capitalize the first letter and the first letter after . ! ? :"""
    if not text:
        return text
    out = []
    cap_next = True
    for ch in text:
        if cap_next and ch.isalpha():
            out.append(ch.upper())
            cap_next = False
        else:
            out.append(ch)
        if ch in ".!?":
            cap_next = True
    return "".join(out)


def run(payload):
    try:
        data = json.loads(payload)
    except Exception as e:
        return {"success": False, "error": f"Bad input JSON: {e}"}

    segments = data.get("segments", [])

    try:
        from deepmultilingualpunctuation import PunctuationModel
    except ImportError:
        return {"success": False, "error": "deepmultilingualpunctuation not installed"}

    try:
        model = PunctuationModel()
    except Exception as e:
        return {"success": False, "error": f"Could not load punctuation model: {e}"}

    out = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            out.append({"text": text})
            continue
        try:
            restored = model.restore_punctuation(text)
            restored = re.sub(r"\s+([,.!?;:])", r"\1", restored)  # tidy spaces before punctuation
            restored = capitalize_sentences(restored.strip())
        except Exception:
            restored = text
        out.append({"text": restored})

    return {"success": True, "segments": out}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: punctuate.py <json>"}))
        sys.exit(1)

    # transformers / HuggingFace can print to stdout — keep our JSON clean
    _real_stdout = os.dup(1)
    os.dup2(2, 1)
    try:
        result = run(sys.argv[1])
    finally:
        sys.stdout.flush()
        os.dup2(_real_stdout, 1)
        os.close(_real_stdout)

    sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    sys.stdout.flush()
