# Styled captions in Premiere (MOGRT) — 30-second setup

Whisper Studio can drop each subtitle into Premiere as an **editable Essential
Graphics text clip** (like AutoCut / FireCut), not just a plain caption track.
For that it needs one **.mogrt template** that carries your style. You make it
once, then reuse it forever.

## Create the template (once)

1. In Premiere, switch to the **Graphics** workspace (Window → Workspaces → Graphics).
2. With a sequence open, grab the **Type tool (T)** and click on the Program
   monitor. Type any placeholder, e.g. `Subtitle`.
3. Select that text layer and style it in **Essential Graphics → Edit**:
   - Font, size, colour
   - Stroke / outline
   - Background box (optional)
   - Position (bottom-center is typical for subtitles)
   - A drop shadow if you like
4. With the graphic clip selected on the timeline, open **Essential Graphics →
   Export** (or right-click the clip → *Export As Motion Graphics Template*).
5. Save it somewhere you'll remember, e.g. `~/Documents/whisper-caption.mogrt`.

## Use it

1. Whisper Studio → **Settings → Send to Premiere**
2. Set **"Send subtitles as" → Styled graphics (MOGRT)**
3. Click **Choose .mogrt…** and pick the file you exported.
4. Transcribe, then hit **Send to Premiere** — each line is placed as a styled,
   fully-editable graphic on a new top video track.

## Notes

- The style is whatever you designed in the template. Want a different look?
  Export another `.mogrt` and switch between them.
- Premiere parameter names differ between versions. The first send logs a
  *diagnostic* (the template's parameter names) to the console — if the text
  doesn't fill in, send that diagnostic so the text-parameter mapping can be tuned.
- **Karaoke** (5 words on screen, the spoken word changing colour) needs a
  template with a built-in highlight control, or per-word placement — this is the
  next step we tune once the basic styled-graphics flow works in your Premiere.
