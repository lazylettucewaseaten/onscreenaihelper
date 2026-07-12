"""Claude On-Screen Helper — hold Ctrl and draw around anything on screen.

Flow:
  1. Hold Ctrl, press left mouse button, drag around the region (circle it).
  2. A red path follows your cursor. Release the mouse button to finish.
  3. The circled region is cropped from a screenshot frozen at drag start.
  4. A dialog opens: type your question; the answer streams from Claude.

Ubuntu / X11 only. Run:  python3 main.py
"""

import signal
import sys

from pynput import keyboard, mouse
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

import capture
import ollama_client
from ask_dialog import AskDialog
from overlay import DrawOverlay

MIN_PATH_POINTS = 8  # ignore plain Ctrl+clicks — require an actual drag


class Bridge(QObject):
    """Marshals pynput (background threads) events onto the Qt main thread."""

    drag_started = pyqtSignal()
    drag_moved = pyqtSignal(int, int)
    drag_ended = pyqtSignal()


class App:
    def __init__(self):
        self.qt = QApplication(sys.argv)
        self.qt.setQuitOnLastWindowClosed(False)
        self.overlay = DrawOverlay()
        self.bridge = Bridge()
        self.bridge.drag_started.connect(self._on_drag_started)
        self.bridge.drag_moved.connect(self._on_drag_moved)
        self.bridge.drag_ended.connect(self._on_drag_ended)

        # Global input state (touched only from pynput threads)
        self._ctrl_down = False
        self._dragging = False
        self._points: list[tuple[int, int]] = []
        self._frozen_img = None
        self._dialog = None

        self._kb = keyboard.Listener(on_press=self._on_key, on_release=self._on_key_up)
        self._ms = mouse.Listener(on_click=self._on_click, on_move=self._on_move)
        self._kb.start()
        self._ms.start()

    # ---- pynput callbacks (background threads) ----

    def _on_key(self, key):
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_down = True

    def _on_key_up(self, key):
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_down = False

    def _on_click(self, x, y, button, pressed):
        if button != mouse.Button.left:
            return
        if pressed and self._ctrl_down and not self._dragging:
            self._dragging = True
            self._points = [(x, y)]
            self.bridge.drag_started.emit()
        elif not pressed and self._dragging:
            self._dragging = False
            self.bridge.drag_ended.emit()

    def _on_move(self, x, y):
        if self._dragging:
            self._points.append((x, y))
            self.bridge.drag_moved.emit(x, y)

    # ---- Qt main-thread handlers ----

    def _on_drag_started(self):
        # Freeze the screen BEFORE the overlay shows, so the red path
        # never appears in the captured image.
        self._frozen_img = capture.grab_fullscreen()
        self.overlay.start_path()

    def _on_drag_moved(self, x, y):
        self.overlay.add_point(x, y)

    def _on_drag_ended(self):
        self.overlay.end_path()
        points, self._points = self._points, []
        if self._frozen_img is None or len(points) < MIN_PATH_POINTS:
            return  # was just a Ctrl+click, not a drawn selection
        try:
            cropped = capture.crop_to_path(self._frozen_img, points)
        except ValueError:
            return  # selection too small
        finally:
            self._frozen_img = None

        png = capture.to_png_bytes(cropped)
        self._dialog = AskDialog(png)  # keep reference so it isn't GC'd
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()

    def run(self):
        signal.signal(signal.SIGINT, lambda *_: self.qt.quit())
        print("Claude On-Screen Helper running.")
        print("Hold Ctrl + drag left mouse button around a region. Ctrl+C here to quit.")
        code = self.qt.exec_()
        ollama_client.unload_model()  # free the model from GPU on exit
        return code


if __name__ == "__main__":
    sys.exit(App().run())
