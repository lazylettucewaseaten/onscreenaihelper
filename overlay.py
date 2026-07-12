"""Transparent fullscreen overlay that draws the user's lasso path live."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygon
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication, QWidget


class DrawOverlay(QWidget):
    """Click-through transparent window covering the virtual desktop.

    The mouse events themselves are tracked globally by pynput in main.py;
    this widget only renders the path for visual feedback.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # click-through
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Cover the whole virtual desktop (all monitors)
        geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(geo)

        self._points: list[QPoint] = []

    def start_path(self):
        self._points = []
        self.show()
        self.raise_()

    def add_point(self, x: int, y: int):
        # Global pointer coords -> widget-local coords
        self._points.append(QPoint(x - self.x(), y - self.y()))
        self.update()

    def end_path(self):
        self._points = []
        self.hide()

    def paintEvent(self, event):
        if len(self._points) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 60, 60, 230), 3)
        painter.setPen(pen)
        painter.drawPolyline(QPolygon(self._points))
