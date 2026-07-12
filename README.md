# Claude On-Screen Helper

Hold **Ctrl** and drag your mouse around anything on screen (circle it) — the
region is captured as an image and sent to Claude with your question. Works on
code, error messages, diagrams, figures, UI — anything visible. No OCR; Claude
reads the image directly.

**Ubuntu / X11 only** (global input capture via pynput does not work on Wayland).

## Setup

```bash
pip3 install --user -r requirements.txt
```

### LLM backend (pick one)

**Ollama (default — local, free, no API key):**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5vl:7b
```

**Claude (cloud, better quality):**

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or use `ant auth login`
export LLM_BACKEND=claude
```

Check your session type first — must print `x11`:

```bash
echo $XDG_SESSION_TYPE
```

## Run

```bash
python3 main.py
```

Then:

1. Hold **Ctrl**, press and hold the **left mouse button**, and draw around the
   region you want help with. A red line follows your cursor.
2. Release the mouse button. A dialog opens showing the cropped region.
3. Type your question (debug this / explain this / what does this figure show /
   anything) and press Enter. Claude's answer streams into the dialog.

A plain Ctrl+click (no drag) is ignored, so normal Ctrl usage is unaffected.

## Files

| File | Purpose |
|---|---|
| `main.py` | Entry point: global Ctrl+drag listener, orchestration |
| `overlay.py` | Transparent overlay that renders the red drawing path |
| `capture.py` | Screenshot frozen at drag start, cropped to your path |
| `ask_dialog.py` | Question input + streamed answer window |
| `claude_client.py` | Claude vision API call (image + text, streaming) |

## Notes

- Screenshot is frozen the moment you press the mouse button, so the red path
  never appears in the captured image.
- Models: `qwen2.5vl:7b` via Ollama (default) or `claude-opus-4-8` (set
  `LLM_BACKEND=claude`).
- The Ctrl+drag still reaches the app underneath (the overlay is click-through),
  so in some apps it may select text — harmless, but be aware.
- Autostart: add `python3 /home/ashish/claudeonscreenhelper/main.py` to GNOME
  Startup Applications if you want it always on.
