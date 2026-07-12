"""Dialog: show cropped region, take the user's question, stream Claude's answer."""

import threading

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

import os

BACKEND = os.environ.get("LLM_BACKEND", "ollama").lower()

if BACKEND == "claude":
    from claude_client import ask_claude as ask_llm
else:
    from ollama_client import ask_ollama as ask_llm


class AskDialog(QDialog):
    _text_chunk = pyqtSignal(str)
    _finished = pyqtSignal()
    _errored = pyqtSignal(str)

    def __init__(self, png_bytes: bytes):
        super().__init__()
        self._png_bytes = png_bytes

        self.setWindowTitle("Claude On-Screen Helper")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(720, 560)

        layout = QVBoxLayout(self)

        # Preview of what was circled
        preview = QLabel()
        image = QImage.fromData(png_bytes, "PNG")
        pix = QPixmap.fromImage(image)
        if pix.width() > 680 or pix.height() > 220:
            pix = pix.scaled(680, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        preview.setPixmap(pix)
        preview.setAlignment(Qt.AlignCenter)
        preview.setStyleSheet("border: 1px solid #888; padding: 4px;")
        layout.addWidget(preview)

        # Question row
        row = QHBoxLayout()
        self.question = QLineEdit()
        self.question.setPlaceholderText(
            "What help do you need with this? (explain / debug / answer / anything)"
        )
        self.ask_btn = QPushButton("Ask Claude")
        row.addWidget(self.question, stretch=1)
        row.addWidget(self.ask_btn)
        layout.addLayout(row)

        # Streamed response
        self.answer = QTextEdit()
        self.answer.setReadOnly(True)
        self.answer.setPlaceholderText("Claude's answer will stream here...")
        layout.addWidget(self.answer, stretch=1)

        self.ask_btn.clicked.connect(self._on_ask)
        self.question.returnPressed.connect(self._on_ask)
        self._text_chunk.connect(self._append_text)
        self._finished.connect(self._on_done)
        self._errored.connect(self._on_error)

        self.question.setFocus()

    def _on_ask(self):
        q = self.question.text().strip()
        if not q:
            return
        self.ask_btn.setEnabled(False)
        self.question.setEnabled(False)
        self.answer.clear()

        def worker():
            try:
                ask_llm(self._png_bytes, q, self._text_chunk.emit)
                self._finished.emit()
            except Exception as e:  # surface API/auth errors in the dialog
                self._errored.emit(f"{type(e).__name__}: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _append_text(self, chunk: str):
        cursor = self.answer.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(chunk)
        self.answer.setTextCursor(cursor)

    def _on_done(self):
        self.ask_btn.setEnabled(True)
        self.question.setEnabled(True)

    def _on_error(self, msg: str):
        self.answer.setPlainText(f"Error:\n{msg}")
        self.ask_btn.setEnabled(True)
        self.question.setEnabled(True)
