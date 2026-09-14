"""
JARVIS V3.0 - Full-Screen Sci-Fi Optical Scanning Overlay
A full-screen transparent HUD overlay with animated laser scanline,
corner targeting brackets, reticle crosshairs, and live analysis telemetry.
Triggered automatically during screen observation or vision tasks.
"""

from __future__ import annotations

import math
import logging
from typing import Optional, List, Dict

logger = logging.getLogger("JARVIS.UI.Scanning")

try:
    from PySide6.QtWidgets import QWidget, QApplication
    from PySide6.QtCore import Qt, QTimer, QPoint, Signal
    from PySide6.QtGui import (
        QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QFont
    )
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object
    Signal = lambda *args: None


class JarvisScanningOverlay(QWidget):
    """
    Full-screen sci-fi laser scanning overlay for JARVIS screen analysis.
    Mouse clicks pass right through (WA_TransparentForMouseEvents).
    """
    if PYSIDE_AVAILABLE:
        scan_completed = Signal()

    def __init__(self, parent=None):
        if not PYSIDE_AVAILABLE:
            return
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self._scan_y = 0.0
        self._speed = 18.0
        self._opacity = 1.0
        self._is_finishing = False
        self._text = "JARVIS OPTICAL SCANNING"
        self._subtext = "Analyzing visual display and active workspace context..."

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._setup_geometry()

    def _setup_geometry(self):
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

    def start_scan(self, duration_ms: int = 2500, title: str = "JARVIS OPTICAL SCANNING", subtitle: str = "Analyzing display..."):
        """Activates full-screen scanline and HUD telemetry."""
        if not PYSIDE_AVAILABLE:
            return
        self._setup_geometry()
        self._scan_y = 0.0
        self._opacity = 1.0
        self._is_finishing = False
        self._text = title
        self._subtext = subtitle

        self.show()
        self.raise_()
        self._timer.start(16)  # 60 FPS

        # Auto-finish after duration
        QTimer.singleShot(duration_ms, self._finish_scan)

    def _finish_scan(self):
        self._is_finishing = True

    def _tick(self):
        h = self.height()
        if h <= 0:
            return

        # Advance laser scan line
        self._scan_y += self._speed
        if self._scan_y > h:
            self._scan_y = 0.0

        # Fade out when finishing
        if self._is_finishing:
            self._opacity -= 0.05
            if self._opacity <= 0.0:
                self._opacity = 0.0
                self._timer.stop()
                self.hide()
                self.scan_completed.emit()
                return

        self.update()

    def paintEvent(self, event):
        if not PYSIDE_AVAILABLE:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        alpha = int(255 * self._opacity)

        # 1. Subtle cyan grid vignette
        vignette = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 1.5)
        vignette.setColorAt(0.0, QColor(6, 182, 212, int(15 * self._opacity)))
        vignette.setColorAt(0.85, QColor(2, 6, 23, int(40 * self._opacity)))
        vignette.setColorAt(1.0, QColor(0, 0, 0, int(80 * self._opacity)))
        painter.fillRect(0, 0, w, h, QBrush(vignette))

        # 2. Moving Laser Line with Vertical Gradient Tail
        laser_y = int(self._scan_y)
        tail_h = 90
        laser_grad = QLinearGradient(0, laser_y - tail_h, 0, laser_y)
        laser_grad.setColorAt(0.0, QColor(56, 189, 248, 0))
        laser_grad.setColorAt(0.7, QColor(56, 189, 248, int(35 * self._opacity)))
        laser_grad.setColorAt(1.0, QColor(56, 189, 248, int(120 * self._opacity)))

        painter.fillRect(0, max(0, laser_y - tail_h), w, tail_h, QBrush(laser_grad))

        # Sharp laser core line
        pen_laser = QPen(QColor(186, 230, 253, int(220 * self._opacity)), 2.0)
        painter.setPen(pen_laser)
        painter.drawLine(0, laser_y, w, laser_y)

        # 3. Sci-Fi Corner Targeting Brackets
        bracket_len = 45
        bracket_pen = QPen(QColor(56, 189, 248, int(180 * self._opacity)), 2.5)
        painter.setPen(bracket_pen)
        margin = 32

        # Top-Left
        painter.drawLine(margin, margin, margin + bracket_len, margin)
        painter.drawLine(margin, margin, margin, margin + bracket_len)
        # Top-Right
        painter.drawLine(w - margin, margin, w - margin - bracket_len, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + bracket_len)
        # Bottom-Left
        painter.drawLine(margin, h - margin, margin + bracket_len, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - bracket_len)
        # Bottom-Right
        painter.drawLine(w - margin, h - margin, w - margin - bracket_len, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - bracket_len)

        # 4. Central HUD Reticle Crosshair
        cx, cy = w / 2.0, h / 2.0
        reticle_pen = QPen(QColor(6, 182, 212, int(90 * self._opacity)), 1.2)
        painter.setPen(reticle_pen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), 50, 50)
        painter.drawLine(int(cx - 65), int(cy), int(cx - 20), int(cy))
        painter.drawLine(int(cx + 20), int(cy), int(cx + 65), int(cy))
        painter.drawLine(int(cx), int(cy - 65), int(cx), int(cy - 20))
        painter.drawLine(int(cx), int(cy + 20), int(cx), int(cy + 65))

        # 5. Telemetry Banner Text
        painter.setPen(QColor(241, 245, 249, int(230 * self._opacity)))
        font_title = QFont("Segoe UI", 13, QFont.Weight.Bold)
        font_title.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(font_title)
        painter.drawText(0, int(cy + 85), w, 30, Qt.AlignmentFlag.AlignCenter, self._text)

        painter.setPen(QColor(148, 163, 184, int(190 * self._opacity)))
        font_sub = QFont("Segoe UI", 10)
        painter.setFont(font_sub)
        painter.drawText(0, int(cy + 115), w, 24, Qt.AlignmentFlag.AlignCenter, self._subtext)
