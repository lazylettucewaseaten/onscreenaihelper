"""Claude API client: send cropped screen region + user question, stream the answer."""

import base64
from collections.abc import Callable

import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = (
    "You are an on-screen assistant. The user circled a region of their screen and is "
    "asking for help with it. The image is a screenshot crop of that region — it may "
    "contain code, error messages, diagrams, figures, UI, or plain text. Answer the "
    "user's question about it directly and concretely. If it is code, reference the "
    "actual identifiers you see. If it is an error, explain the cause and give a fix. "
    "Keep the response focused; the user is mid-task."
)


def ask_claude(
    png_bytes: bytes,
    question: str,
    on_text: Callable[[str], None],
) -> str:
    """Send image + question to Claude, streaming text chunks to on_text.

    Returns the full response text. Raises anthropic errors to the caller.
    """
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY or `ant auth login` profile
    image_b64 = base64.standard_b64encode(png_bytes).decode("utf-8")

    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": question},
                ],
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            on_text(text)
        final = stream.get_final_message()

    return "".join(b.text for b in final.content if b.type == "text")
