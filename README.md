# On-Screen AI Helper (onscreenaihelper)

Hold **Ctrl** and drag your mouse around anything on your screen (circle it) — the region is captured as an image and sent to a Vision AI (Ollama or Claude) along with your question. Works on code, error messages, diagrams, figures, UI — anything visible. No OCR is needed; the AI reads the image directly.

**Ubuntu / X11 only** (global input capture via pynput does not work on Wayland).

## Features

- **Seamless Interaction:** Hold Ctrl and left-click-drag to draw a region of interest. A red path provides visual feedback.
- **Smart Context:** Capture freezes the exact moment you start dragging, so the UI overlays aren't in your shot.
- **Multiple AI Backends:** Out-of-the-box support for free, local models via **Ollama**, or premium models via **Anthropic Claude**.
- **Interactive Dialog:** A PyQt5-based prompt allows you to type questions and streams back the AI's answer.

## Setup

1. **Install Python Dependencies:**
   ```bash
   pip3 install --user -r requirements.txt
   ```

2. **Choose your LLM backend:**

   **Ollama (default — local, free, no API key):**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull qwen2.5vl:7b
   ```

   **Claude (cloud, higher quality):**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   export LLM_BACKEND=claude
   ```

3. **Check your session type:**
   Must print `x11` for the global capture to work properly.
   ```bash
   echo $XDG_SESSION_TYPE
   ```

## Usage

1. Run the application:
   ```bash
   python3 main.py
   ```
2. Hold **Ctrl**, press and hold the **left mouse button**, and draw around the region you want help with. A red line follows your cursor.
3. Release the mouse button. A dialog opens showing the cropped region.
4. Type your question (e.g., "debug this", "explain this", "what does this figure show") and press Enter. The AI's answer streams into the dialog.

*(Note: A plain Ctrl+click with no drag is ignored, so normal Ctrl usage is unaffected.)*

## Architecture & Files

| File | Purpose |
|---|---|
| `main.py` | Entry point: orchestrates global Ctrl+drag listener, coordinates Qt and background threads. |
| `overlay.py` | Transparent Qt widget that covers the screen to render the red drawing path. |
| `capture.py` | Captures a full desktop screenshot frozen at drag start and crops it to the drawn path. |
| `ask_dialog.py` | Qt Dialog for question input and displaying the streamed answer. |
| `ollama_client.py` | Client for local Ollama API (sends image + text, streams response, unloads model). |
| `claude_client.py` | Client for Anthropic Claude vision API (image + text, streaming). |

## Notes

- The screenshot is frozen the moment you press the mouse button, ensuring the red path never appears in the captured image.
- Models: Uses `qwen2.5vl:7b` via Ollama (default) or `claude-opus-4-8` (when `LLM_BACKEND=claude`).
- The Ctrl+drag interaction is click-through, meaning it still reaches the application underneath. In some apps, it may select text — this is harmless, but be aware.
- Autostart: To keep the helper always on, add `python3 /full/path/to/main.py` to your Startup Applications.
