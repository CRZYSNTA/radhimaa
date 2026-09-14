"""
JARVIS V3.0 - Floating Spotlight Command Bar
A floating search & command bar (580x48 px) centered on screen.
Provides instant typed commands, voice mic toggle, and quick actions
with sleek dark glassmorphism and cyan neon glow.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("JARVIS.UI.CommandBar")

try:
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel,
        QFrame, QApplication, QGraphicsDropShadowEffect
    )
    from PySide6.QtCore import Qt, Signal, QPoint
    from PySide6.QtGui import QColor, QFont, QIcon, QKeyEvent
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object
    Signal = lambda *args: None


class JarvisCommandBar(QWidget):
    """
    Spotlight-style floating input HUD for JARVIS.
    Triggered via shortcut or clicking the floating orb.
    """
    if PYSIDE_AVAILABLE:
        command_submitted = Signal(str)
        mic_clicked = Signal()
        dismissed = Signal()

    def __init__(self, parent=None):
        if not PYSIDE_AVAILABLE:
            return
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(580, 56)
        self.setObjectName("JarvisCommandBar")

        self._build_ui()
        self._center_on_screen()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(0)

        self._frame = QFrame(self)
        self._frame.setObjectName("CommandBarFrame")
        self._frame.setStyleSheet("""
            QFrame#CommandBarFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(8, 14, 26, 248),
                    stop:0.5 rgba(13, 22, 40, 248),
                    stop:1 rgba(8, 14, 26, 248));
                border: 1.5px solid rgba(56, 189, 248, 0.6);
                border-radius: 22px;
            }
        """)

        # Drop shadow glow effect
        shadow = QGraphicsDropShadowEffect(self._frame)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(2, 132, 199, 120))
        shadow.setOffset(0, 2)
        self._frame.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self._frame)
        layout.setContentsMargins(14, 4, 10, 4)
        layout.setSpacing(8)

        # JARVIS Mini Core Icon / Badge
        self._badge = QLabel("⚡")
        self._badge.setStyleSheet("color: #38bdf8; font-size: 16px; background: transparent;")
        layout.addWidget(self._badge)

        # Text input field
        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask JARVIS anything or enter a command...")
        self._input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f1f5f9;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 13.5px;
                selection-background-color: #0284c7;
            }
            QLineEdit:focus {
                outline: none;
            }
        """)
        self._input.returnPressed.connect(self._handle_submit)
        layout.addWidget(self._input, 1)

        # Mic voice button
        self._btn_mic = QPushButton("🎤")
        self._btn_mic.setFixedSize(32, 32)
        self._btn_mic.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_mic.setToolTip("Toggle Voice Listening")
        self._btn_mic.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.12);
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 16px;
                color: #38bdf8;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.28);
                border: 1px solid #38bdf8;
            }
            QPushButton:pressed {
                background: rgba(56, 189, 248, 0.45);
            }
        """)
        self._btn_mic.clicked.connect(lambda: self.mic_clicked.emit())
        layout.addWidget(self._btn_mic)

        # Submit arrow button
        self._btn_send = QPushButton("➔")
        self._btn_send.setFixedSize(32, 32)
        self._btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_send.setToolTip("Execute Command (Enter)")
        self._btn_send.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                border: none;
                border-radius: 16px;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #040d1a;
            }
            QPushButton:pressed {
                background: #0369a1;
            }
        """)
        self._btn_send.clicked.connect(self._handle_submit)
        layout.addWidget(self._btn_send)

        root_layout.addWidget(self._frame)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = int(geo.height() * 0.25)  # Position comfortably in upper-third
            self.move(x, y)

    def _handle_submit(self):
        text = self._input.text().strip()
        if text:
            self._input.clear()
            self.command_submitted.emit(text)
            self.hide()

    def show_command_bar(self):
        self._center_on_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.dismissed.emit()
        else:
            super().keyPressEvent(event)
