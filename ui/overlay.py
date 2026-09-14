"""
JARVIS V3.0 UI: Futuristic Arc Reactor Overlay
Features dynamic state transitions, smooth pulsing and rotating core,
real-time hardware monitors (CPU, RAM, Battery), frameless draggable window,
and seamless fallback to Tkinter for maximum portability.
"""

import os
import sys
import math
import time
import psutil
import logging
import threading
from typing import Optional, Dict

import config
from ui.system_monitor import SystemMonitorThread

logger = logging.getLogger("JARVIS.UI")

# Color Palettes by Assistant State
STATE_COLORS = {
    "IDLE": {"primary": "#38bdf8", "glow": "#0284c7", "text": "◉ JARVIS IDLE"},
    "LISTENING": {"primary": "#4ade80", "glow": "#16a34a", "text": "🎤 LISTENING..."},
    "THINKING": {"primary": "#c084fc", "glow": "#9333ea", "text": "🧠 THINKING..."},
    "PLANNING": {"primary": "#818cf8", "glow": "#4f46e5", "text": "📋 PLANNING..."},
    "OBSERVING": {"primary": "#38bdf8", "glow": "#0369a1", "text": "👁️ OBSERVING SCREEN"},
    "EXECUTING": {"primary": "#fbbf24", "glow": "#d97706", "text": "⚡ EXECUTING..."},
    "VERIFYING": {"primary": "#2dd4bf", "glow": "#0d9488", "text": "🔍 VERIFYING STATE"},
    "REPLANNING": {"primary": "#fb923c", "glow": "#ea580c", "text": "🔄 REPLANNING..."},
    "SPEAKING": {"primary": "#60a5fa", "glow": "#2563eb", "text": "🗣️ SPEAKING..."},
    "CONFIRMATION_REQUIRED": {"primary": "#facc15", "glow": "#ca8a04", "text": "⚠️ CONFIRMATION"},
    "ERROR": {"primary": "#f87171", "glow": "#dc2626", "text": "⚠️ ALERT"},
}

_global_ui_instance = None

try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
    )
    from PySide6.QtCore import Qt, QTimer, QPoint, QObject, Signal
    from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont
    PYSIDE_AVAILABLE = True

    from ui.floating_orb import JarvisFloatingOrb
    from ui.command_bar import JarvisCommandBar
    from ui.scanning_overlay import JarvisScanningOverlay
    from ui.task_hud import JarvisTaskHUD
except ImportError:
    PYSIDE_AVAILABLE = False
    JarvisFloatingOrb = None
    JarvisCommandBar = None
    JarvisScanningOverlay = None
    JarvisTaskHUD = None


if PYSIDE_AVAILABLE:
    class ArcReactorCanvas(QWidget):
        """Custom animated Arc Reactor component painted with QPainter."""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setFixedSize(240, 160)
            self.angle = 0
            self.pulse_phase = 0.0
            self.current_state = "IDLE"
            self.colors = STATE_COLORS["IDLE"]

            # 30 FPS animation loop
            self.anim_timer = QTimer(self)
            self.anim_timer.timeout.connect(self._animate_step)
            self.anim_timer.start(33)

        def set_state(self, state: str):
            st = state.upper()
            self.current_state = st
            self.colors = STATE_COLORS.get(st, STATE_COLORS["IDLE"])
            self.update()

        def _animate_step(self):
            self.angle = (self.angle + 2) % 360
            self.pulse_phase = (self.pulse_phase + 0.08) % (2 * math.pi)
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            cx = self.width() / 2.0
            cy = self.height() / 2.0
            base_color = QColor(self.colors["primary"])
            glow_color = QColor(self.colors["glow"])

            # Outer subtle glow ring
            pulse_radius = 56 + math.sin(self.pulse_phase) * 3
            gradient = QRadialGradient(cx, cy, pulse_radius + 20)
            gradient.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 60))
            gradient.setColorAt(1.0, QColor(15, 23, 42, 0))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(cx), int(cy)), int(pulse_radius + 15), int(pulse_radius + 15))

            # Outer primary ring
            pen_outer = QPen(base_color, 3)
            painter.setPen(pen_outer)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPoint(int(cx), int(cy)), int(pulse_radius), int(pulse_radius))

            # Segmented rotating arc ring
            pen_arc = QPen(glow_color, 4)
            painter.setPen(pen_arc)
            rect_arc = [cx - 42, cy - 42, 84, 84]
            for i in range(4):
                start_angle = (self.angle + i * 90) * 16
                span_angle = 50 * 16
                painter.drawArc(int(rect_arc[0]), int(rect_arc[1]), int(rect_arc[2]), int(rect_arc[3]), start_angle, span_angle)

            # Inner Core Reactor
            core_gradient = QRadialGradient(cx, cy, 26)
            core_gradient.setColorAt(0.0, QColor("#ffffff"))
            core_gradient.setColorAt(0.5, base_color)
            core_gradient.setColorAt(1.0, glow_color)
            painter.setBrush(QBrush(core_gradient))
            painter.setPen(QPen(base_color, 2))
            painter.drawEllipse(QPoint(int(cx), int(cy)), 24, 24)

            # Center Dot
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(cx), int(cy)), 7, 7)
            painter.end()


    class UIBridge(QObject):
        state_signal = Signal(str, str)
        stats_signal = Signal(float, float, str)
        task_signal = Signal(str, int, int)

    class PySideJarvisOverlay(QWidget):
        """Frameless, translucent floating Arc Reactor HUD."""
        def __init__(self):
            super().__init__()
            self.drag_position = QPoint()
            self.bridge = UIBridge()
            self.bridge.state_signal.connect(self._apply_state)
            self.bridge.stats_signal.connect(self._apply_stats)
            self.bridge.task_signal.connect(self._apply_task)
            self._init_ui()
            self._init_monitor()
            self._init_event_bus()

        def _init_event_bus(self):
            from ui.events import get_event_bus, AgentStateEvent
            def _on_event(evt: AgentStateEvent):
                self.set_state(evt.state, evt.details)
                if evt.task_step:
                    self.set_task_progress(evt.task_step.step_description, evt.task_step.step_index, evt.task_step.total_steps)
            get_event_bus().subscribe(_on_event)

        def _init_ui(self):
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool
            )
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.resize(260, 330)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)

            # Container card with dark sleek background
            self.card = QWidget(self)
            self.card.setObjectName("card")
            self.card.setStyleSheet("""
                QWidget {
                    background-color: #0f172a;
                    border: 2px solid #38bdf8;
                    border-radius: 12px;
                }
            """)
            card_layout = QVBoxLayout(self.card)
            card_layout.setContentsMargins(10, 10, 10, 10)
            card_layout.setSpacing(6)

            # Arc Reactor Canvas
            self.reactor = ArcReactorCanvas(self.card)
            card_layout.addWidget(self.reactor, alignment=Qt.AlignCenter)

            # Title / State Label
            self.lbl_title = QLabel("◉ JARVIS V3.1", self.card)
            self.lbl_title.setAlignment(Qt.AlignCenter)
            self.lbl_title.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: bold; border: none;")
            card_layout.addWidget(self.lbl_title)

            # Subtitle / Details Label
            self.lbl_status = QLabel("State: IDLE", self.card)
            self.lbl_status.setAlignment(Qt.AlignCenter)
            self.lbl_status.setStyleSheet("color: #94a3b8; font-size: 10px; border: none;")
            card_layout.addWidget(self.lbl_status)

            # Live Task Progress Label
            self.lbl_task = QLabel("", self.card)
            self.lbl_task.setAlignment(Qt.AlignCenter)
            self.lbl_task.setStyleSheet("color: #fbbf24; font-size: 9px; font-weight: bold; border: none;")
            self.lbl_task.setVisible(False)
            card_layout.addWidget(self.lbl_task)

            # System Monitor Bar
            self.lbl_sys = QLabel("CPU 0% | RAM 0% | BAT --", self.card)
            self.lbl_sys.setAlignment(Qt.AlignCenter)
            self.lbl_sys.setStyleSheet("""
                background-color: #1e293b;
                color: #38bdf8;
                font-size: 9px;
                font-weight: bold;
                padding: 4px;
                border-radius: 6px;
                border: 1px solid #334155;
            """)
            card_layout.addWidget(self.lbl_sys)

            layout.addWidget(self.card)

            # Position on bottom-right or center-right
            screen = QApplication.primaryScreen().geometry()
            self.move(screen.width() - 290, screen.height() - 360)

        def _init_monitor(self):
            def _on_stats(cpu, ram, bat):
                self.bridge.stats_signal.emit(cpu, ram, bat)
                try:
                    from communication.broadcaster import get_broadcaster
                    get_broadcaster().broadcast_system_status(cpu, ram)
                except Exception:
                    pass
            self.monitor = SystemMonitorThread(update_callback=_on_stats, interval=1.5)
            self.monitor.start()

        def _apply_stats(self, cpu: float, ram: float, bat: str):
            self.lbl_sys.setText(f"CPU {int(cpu)}% | RAM {int(ram)}% | {bat}")

        def set_state(self, state: str, details: str = ""):
            self.bridge.state_signal.emit(state, details)

        def _apply_state(self, state: str, details: str = ""):
            st = state.upper()
            info = STATE_COLORS.get(st, STATE_COLORS["IDLE"])
            self.reactor.set_state(st)
            self.lbl_title.setText(info["text"])
            self.lbl_title.setStyleSheet(f"color: {info['primary']}; font-size: 13px; font-weight: bold; border: none;")
            if details:
                self.lbl_status.setText(details[:35])
            else:
                self.lbl_status.setText(f"State: {st}")
            self.card.setStyleSheet(f"""
                QWidget {{
                    background-color: #0f172a;
                    border: 2px solid {info['primary']};
                    border-radius: 12px;
                }}
            """)

        def set_task_progress(self, description: str, step_index: int, total_steps: int):
            self.bridge.task_signal.emit(description, step_index, total_steps)

        def _apply_task(self, description: str, step_index: int, total_steps: int):
            if description and total_steps > 0:
                self.lbl_task.setText(f"Step {step_index}/{total_steps}: {description[:26]}")
                self.lbl_task.setVisible(True)
            else:
                self.lbl_task.setVisible(False)

        # Mouse Dragging Support
        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event):
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()


# Fallback Tkinter implementation
class TkinterJarvisOverlay:
    """Tkinter-based fallback Arc Reactor UI."""
    def __init__(self):
        import tkinter as tk
        self.root = tk.Tk()
        self.root.title("JARVIS V3.0")
        self.root.geometry("260x300+100+100")
        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass

        self.root.config(bg="#38bdf8", bd=2)
        self.card = tk.Frame(self.root, bg="#0f172a")
        self.card.pack(fill="both", expand=True, padx=2, pady=2)

        self.canvas = tk.Canvas(self.card, width=240, height=150, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(fill="x")
        self.outer_ring = self.canvas.create_oval(60, 15, 180, 135, outline="#38bdf8", width=4)
        self.inner_core = self.canvas.create_oval(90, 45, 150, 105, fill="#0284c7", outline="")
        self.center_dot = self.canvas.create_oval(112, 67, 128, 83, fill="#ffffff", outline="")

        self.title_label = tk.Label(self.card, text="◉ JARVIS AGENT", bg="#0f172a", fg="#38bdf8", font=("Segoe UI", 11, "bold"))
        self.title_label.pack(pady=2)

        self.status_label = tk.Label(self.card, text="State: IDLE", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 8))
        self.status_label.pack(pady=2)

        self.sys_label = tk.Label(self.card, text="CPU 0% | RAM 0%", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 8, "bold"), padx=4, pady=2)
        self.sys_label.pack(fill="x", padx=6, pady=4)

        self.monitor = SystemMonitorThread(self._on_stats, interval=1.5)
        self.monitor.start()

    def _on_stats(self, cpu, ram, bat):
        try:
            self.sys_label.config(text=f"CPU {int(cpu)}% | RAM {int(ram)}% | {bat}")
        except Exception:
            pass

    def set_state(self, state: str, details: str = ""):
        try:
            self.root.after(0, lambda: self._apply_state(state, details))
        except Exception:
            pass

    def _apply_state(self, state: str, details: str = ""):
        st = state.upper()
        info = STATE_COLORS.get(st, STATE_COLORS["IDLE"])
        try:
            self.title_label.config(text=info["text"], fg=info["primary"])
            self.status_label.config(text=details if details else f"State: {st}")
            self.canvas.itemconfig(self.outer_ring, outline=info["primary"])
            self.canvas.itemconfig(self.inner_core, fill=info["glow"])
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


def create_overlay():
    """Factory function creating the appropriate UI instance."""
    use_pyside = PYSIDE_AVAILABLE and getattr(config, "UI_FRAMEWORK", "pyside6").lower() == "pyside6"
    if use_pyside:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        ui = PySideJarvisOverlay()
        ui.show()
        return ui, app
    else:
        logger.info("[UI] Using Tkinter fallback overlay.")
        ui = TkinterJarvisOverlay()
        return ui, None

_global_scanning_overlay = None
_global_command_bar = None
_global_task_hud = None
_global_floating_orb = None

def get_or_create_scanning_overlay():
    global _global_scanning_overlay
    if not PYSIDE_AVAILABLE or not JarvisScanningOverlay or QApplication.instance() is None:
        return None
    if _global_scanning_overlay is None:
        _global_scanning_overlay = JarvisScanningOverlay()
    return _global_scanning_overlay

def show_scanning_overlay(duration_ms: int = 2500, title: str = "JARVIS OPTICAL SCANNING", subtitle: str = "Analyzing display context..."):
    overlay = get_or_create_scanning_overlay()
    if overlay:
        overlay.start_scan(duration_ms=duration_ms, title=title, subtitle=subtitle)

def get_or_create_command_bar():
    global _global_command_bar
    if not PYSIDE_AVAILABLE or not JarvisCommandBar or QApplication.instance() is None:
        return None
    if _global_command_bar is None:
        _global_command_bar = JarvisCommandBar()
    return _global_command_bar

def show_command_bar():
    bar = get_or_create_command_bar()
    if bar:
        bar.show_command_bar()

def get_or_create_task_hud():
    global _global_task_hud
    if not PYSIDE_AVAILABLE or not JarvisTaskHUD or QApplication.instance() is None:
        return None
    if _global_task_hud is None:
        _global_task_hud = JarvisTaskHUD()
    return _global_task_hud

def show_task_hud(title: str, subtitle: str = "", icon: str = "⚡", duration_ms: int = 5000, alert_type: str = "info"):
    hud = get_or_create_task_hud()
    if hud:
        hud.show_notification(title=title, subtitle=subtitle, icon=icon, duration_ms=duration_ms, alert_type=alert_type)

def create_floating_orb():
    global _global_floating_orb
    if not PYSIDE_AVAILABLE or not JarvisFloatingOrb or QApplication.instance() is None:
        return None
    if _global_floating_orb is None:
        _global_floating_orb = JarvisFloatingOrb()
        # Connect single click to toggle command bar
        _global_floating_orb.clicked.connect(show_command_bar)
        _global_floating_orb.show()
    return _global_floating_orb

def set_ui_state(state: str, details: str = ""):
    global _global_ui_instance, _global_floating_orb
    if _global_ui_instance:
        _global_ui_instance.set_state(state, details)
    if _global_floating_orb:
        _global_floating_orb.set_state(state)
    if state.upper() == "OBSERVING":
        show_scanning_overlay(duration_ms=2500)
    try:
        from communication.broadcaster import get_broadcaster
        get_broadcaster().broadcast_state(state, details)
    except Exception:
        pass

if __name__ == "__main__":
    ui, app = create_overlay()
    _global_ui_instance = ui
    ui.set_state("LISTENING", "Listening for wake word...")
    if app:
        sys.exit(app.exec())
    else:
        ui.run()

