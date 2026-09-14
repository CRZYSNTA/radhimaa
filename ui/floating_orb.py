"""
JARVIS V3.0 - Floating Arc Reactor Orb Widget
A compact, 90x90 frameless, translucent, always-on-top desktop orb.
Features multi-ring counter-rotation, breathing pulsation, particle trails,
state-reactive neon glow, dragging across the desktop, and click-to-activate.
"""

from __future__ import annotations

import math
import logging
from typing import Optional, List, Dict

logger = logging.getLogger("JARVIS.UI.Orb")

try:
    from PySide6.QtWidgets import QWidget, QApplication
    from PySide6.QtCore import Qt, QTimer, QPoint, Signal
    from PySide6.QtGui import (
        QPainter, QColor, QPen, QBrush, QRadialGradient, QLinearGradient, QCursor
    )
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object
    Signal = lambda *args: None

# State color themes
ORB_STATE_COLORS: Dict[str, Dict[str, str]] = {
    "IDLE": {"primary": "#38bdf8", "glow": "#0284c7", "core": "#e0f2fe"},
    "LISTENING": {"primary": "#4ade80", "glow": "#16a34a", "core": "#dcfce7"},
    "THINKING": {"primary": "#c084fc", "glow": "#9333ea", "core": "#f3e8ff"},
    "PLANNING": {"primary": "#818cf8", "glow": "#4f46e5", "core": "#e0e7ff"},
    "EXECUTING": {"primary": "#fbbf24", "glow": "#d97706", "core": "#fef3c7"},
    "OBSERVING": {"primary": "#06b6d4", "glow": "#0891b2", "core": "#cffafe"},
    "ERROR": {"primary": "#f87171", "glow": "#dc2626", "core": "#fee2e2"},
}


class JarvisFloatingOrb(QWidget):
    """
    Floating 90x90 Arc Reactor Orb that can be dragged anywhere on screen.
    Emits signals for single-click, double-click, and position changes.
    """
    if PYSIDE_AVAILABLE:
        clicked = Signal()
        double_clicked = Signal()
        position_changed = Signal(int, int)

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
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(92, 92)

        self._state = "IDLE"
        self._colors = ORB_STATE_COLORS["IDLE"]
        self._hovered = False

        # Animation angles and pulsation
        self._ring1_angle = 0.0
        self._ring2_angle = 0.0
        self._ring3_angle = 0.0
        self._pulse_val = 0.0
        self._pulse_dir = 1.0

        # Particle orbiters (8 nodes)
        self._particles = [i * 45.0 for i in range(8)]

        # Dragging state
        self._dragging = False
        self._drag_start = QPoint(0, 0)

        # Single click delay timer to distinguish double click
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(220)
        self._click_timer.timeout.connect(self._handle_single_click)

        # 40 FPS animation timer
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(25)

        # Default position: bottom-right corner of screen
        self._position_default()

    def _position_default(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.width() - 110, geo.height() - 120)

    def set_state(self, state: str):
        st = state.upper()
        self._state = st
        self._colors = ORB_STATE_COLORS.get(st, ORB_STATE_COLORS["IDLE"])
        self.update()

    def _anim_tick(self):
        # Ring counter rotations
        speed = 2.4 if self._state in ("THINKING", "EXECUTING") else 1.2
        self._ring1_angle = (self._ring1_angle + speed) % 360.0
        self._ring2_angle = (self._ring2_angle - speed * 1.5) % 360.0
        self._ring3_angle = (self._ring3_angle + speed * 0.8) % 360.0

        # Breathing pulsation
        self._pulse_val += 0.04 * self._pulse_dir
        if self._pulse_val >= 1.0:
            self._pulse_val = 1.0
            self._pulse_dir = -1.0
        elif self._pulse_val <= 0.0:
            self._pulse_val = 0.0
            self._pulse_dir = 1.0

        # Rotate orbiting particles
        for i in range(len(self._particles)):
            self._particles[i] = (self._particles[i] + speed * 1.1) % 360.0

        self.update()

    def paintEvent(self, event):
        if not PYSIDE_AVAILABLE:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        primary = QColor(self._colors["primary"])
        glow = QColor(self._colors["glow"])
        core = QColor(self._colors["core"])

        # 1. Outer ambient glow halo
        glow_radius = 42 + self._pulse_val * 3.5
        halo = QRadialGradient(cx, cy, glow_radius)
        halo.setColorAt(0.0, QColor(primary.red(), primary.green(), primary.blue(), 90))
        halo.setColorAt(0.55, QColor(glow.red(), glow.green(), glow.blue(), 35))
        halo.setColorAt(1.0, QColor(10, 15, 26, 0))
        painter.setBrush(QBrush(halo))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(glow_radius), int(glow_radius))

        # 2. Dark reactor glass backing
        glass_grad = QRadialGradient(cx, cy, 34)
        glass_grad.setColorAt(0.0, QColor(15, 23, 42, 230))
        glass_grad.setColorAt(0.85, QColor(8, 12, 22, 245))
        glass_grad.setColorAt(1.0, QColor(3, 7, 18, 255))
        painter.setBrush(QBrush(glass_grad))
        pen_rim = QPen(QColor(primary.red(), primary.green(), primary.blue(), 140), 1.5)
        painter.setPen(pen_rim)
        painter.drawEllipse(QPoint(int(cx), int(cy)), 34, 34)

        # 3. Outer rotating segmented arc ring (Ring 1)
        pen_ring1 = QPen(primary, 2.0)
        painter.setPen(pen_ring1)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(4):
            arc_start = int((self._ring1_angle + i * 90) * 16)
            painter.drawArc(int(cx - 30), int(cy - 30), 60, 60, arc_start, 55 * 16)

        # 4. Middle counter-rotating dashed ring (Ring 2)
        pen_ring2 = QPen(QColor(glow.red(), glow.green(), glow.blue(), 180), 1.5)
        pen_ring2.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen_ring2)
        painter.drawEllipse(QPoint(int(cx), int(cy)), 23, 23)

        # 5. Orbiting energy nodes (8 particles)
        particle_radius = 23.0
        for angle_deg in self._particles:
            rad = math.radians(angle_deg)
            px = cx + particle_radius * math.cos(rad)
            py = cy + particle_radius * math.sin(rad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(core))
            painter.drawEllipse(QPoint(int(px), int(py)), 2, 2)

        # 6. Center glowing reactor core
        core_radius = 12 + self._pulse_val * 2.0
        core_grad = QRadialGradient(cx, cy, core_radius)
        core_grad.setColorAt(0.0, core)
        core_grad.setColorAt(0.5, primary)
        core_grad.setColorAt(1.0, QColor(glow.red(), glow.green(), glow.blue(), 160))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(core, 1.2))
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(core_radius), int(core_radius))

    # Mouse interactions
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_start
            self.move(new_pos)
            self.position_changed.emit(new_pos.x(), new_pos.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            # If moved barely any distance, consider it a click
            if not self._click_timer.isActive():
                self._click_timer.start()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._click_timer.stop()
            self.double_clicked.emit()

    def _handle_single_click(self):
        self.clicked.emit()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
