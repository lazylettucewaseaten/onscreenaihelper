"""Ollama client: send cropped screen region + question to a local vision model."""

import base64
import json
import urllib.request
from collections.abc import Callable

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5vl:7b"


def unload_model() -> None:
    """Ask Ollama to free the model from GPU memory now (keep_alive: 0)."""
    payload = json.dumps({"model": MODEL, "keep_alive": 0}).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10).close()
    except Exception:
        pass  # Ollama already gone / not running — nothing to unload

SYSTEM_PROMPT = (
    "You are an on-screen assistant. The user circled a region of their screen and is "
    "asking for help with it. The image is a screenshot crop of that region — it may "
    "contain code, error messages, diagrams, figures, UI, or plain text. Answer the "
    "user's question about it directly and concretely. If it is code, reference the "
    "actual identifiers you see. If it is an error, explain the cause and give a fix. "
    "Keep the response focused; the user is mid-task."
)


def ask_ollama(
    png_bytes: bytes,
    question: str,
    on_text: Callable[[str], None],
) -> str:
    """Send image + question to local Ollama, streaming text chunks to on_text."""
    image_b64 = base64.standard_b64encode(png_bytes).decode("utf-8")

    payload = json.dumps({
        "model": MODEL,
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question, "images": [image_b64]},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )

    full = []
    with urllib.request.urlopen(req, timeout=300) as resp:
        for line in resp:
            if not line.strip():
                continue
            chunk = json.loads(line)
            if chunk.get("error"):
                raise RuntimeError(chunk["error"])
            text = chunk.get("message", {}).get("content", "")
            if text:
                full.append(text)
                on_text(text)
            if chunk.get("done"):
                break
    return "".join(full)
