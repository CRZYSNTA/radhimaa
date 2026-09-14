"""
JARVIS V3.0 - Floating Task & Notification HUD
A floating glassmorphic notification banner / heads-up display.
Displays active operations, background task progress, alerts, and meeting status
with smooth entrance animations and auto-dismissal.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("JARVIS.UI.TaskHUD")

try:
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
        QApplication, QGraphicsDropShadowEffect
    )
    from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, QPoint
    from PySide6.QtGui import QColor, QFont
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object
    Signal = lambda *args: None


class JarvisTaskHUD(QWidget):
    """
    Compact floating heads-up display for ongoing tasks, alerts, or meeting notes.
    Positions top-center of the screen.
    """
    if PYSIDE_AVAILABLE:
        action_clicked = Signal(str)
        dismissed = Signal()

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
        self.setFixedSize(420, 68)
        self.setObjectName("JarvisTaskHUD")

        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide_hud)

        self._build_ui()
        self._position_top_center()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(0)

        self._frame = QFrame(self)
        self._frame.setObjectName("TaskHUDFrame")
        self._frame.setStyleSheet("""
            QFrame#TaskHUDFrame {
                background: rgba(10, 15, 26, 0.94);
                border: 1.5px solid rgba(56, 189, 248, 0.45);
                border-radius: 18px;
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self._frame)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 3)
        self._frame.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self._frame)
        layout.setContentsMargins(14, 6, 12, 6)
        layout.setSpacing(10)

        # Status icon / badge
        self._icon_label = QLabel("⚡")
        self._icon_label.setStyleSheet("font-size: 20px; background: transparent; color: #38bdf8;")
        layout.addWidget(self._icon_label)

        # Text column (Title + Subtitle)
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)

        self._title_label = QLabel("JARVIS HUD")
        self._title_label.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 13px; background: transparent;")
        text_col.addWidget(self._title_label)

        self._sub_label = QLabel("Task operational")
        self._sub_label.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        text_col.addWidget(self._sub_label)

        layout.addLayout(text_col, 1)

        # Close button
        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedSize(24, 24)
        self._btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 12px;
                border-radius: 12px;
            }
            QPushButton:hover {
                color: #f1f5f9;
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        self._btn_close.clicked.connect(self.hide_hud)
        layout.addWidget(self._btn_close)

        root.addWidget(self._frame)

    def _position_top_center(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = 24
            self.move(x, y)

    def show_notification(self, title: str, subtitle: str = "", icon: str = "⚡", duration_ms: int = 5000, alert_type: str = "info"):
        """Displays a notification banner with automatic dismissal."""
        if not PYSIDE_AVAILABLE:
            return
        self._title_label.setText(title)
        self._sub_label.setText(subtitle)
        self._icon_label.setText(icon)

        # Accent border color by alert type
        border_colors = {
            "info": "rgba(56, 189, 248, 0.55)",
            "success": "rgba(74, 222, 128, 0.65)",
            "warning": "rgba(250, 204, 21, 0.65)",
            "alert": "rgba(248, 113, 113, 0.75)",
        }
        border = border_colors.get(alert_type, border_colors["info"])
        self._frame.setStyleSheet(f"""
            QFrame#TaskHUDFrame {{
                background: rgba(10, 15, 26, 0.95);
                border: 1.5px solid {border};
                border-radius: 18px;
            }}
        """)

        self._position_top_center()
        self.show()
        self.raise_()

        if duration_ms > 0:
            self._auto_hide_timer.start(duration_ms)

    def hide_hud(self):
        self.hide()
        self.dismissed.emit()
