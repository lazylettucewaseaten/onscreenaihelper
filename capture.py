"""Screen capture: freeze full screenshot at drag start, crop to drawn region."""

import io

import mss
from PIL import Image


def grab_fullscreen() -> Image.Image:
    """Capture the entire virtual desktop (all monitors) as a PIL image."""
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # index 0 = full virtual screen
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        # Remember the virtual-screen origin so pointer coords map correctly
        img.info["origin"] = (monitor["left"], monitor["top"])
        return img


def crop_to_path(img: Image.Image, points: list[tuple[int, int]], padding: int = 12) -> Image.Image:
    """Crop the frozen screenshot to the bounding box of the drawn path."""
    origin_x, origin_y = img.info.get("origin", (0, 0))
    xs = [p[0] - origin_x for p in points]
    ys = [p[1] - origin_y for p in points]
    left = max(min(xs) - padding, 0)
    top = max(min(ys) - padding, 0)
    right = min(max(xs) + padding, img.width)
    bottom = min(max(ys) + padding, img.height)
    if right - left < 8 or bottom - top < 8:
        raise ValueError("Selection too small")
    return img.crop((left, top, right, bottom))


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
