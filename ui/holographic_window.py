"""
JARVIS V4 Holographic Desktop Window (PySide6 + QWebEngineView)
Embeds the WebGL Three.js Holographic AI Interface into a frameless,
hardware-accelerated desktop window with zero external browser dependency.
"""

import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger("JARVIS.HolographicWindow")

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
    from PySide6.QtCore import Qt, QUrl, QTimer
    try:
        from PySide6.QtGui import QKeySequence, QColor, QShortcut
    except ImportError:
        from PySide6.QtGui import QKeySequence, QColor
        from PySide6.QtWidgets import QShortcut
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
    PYSIDE_WEBENGINE_AVAILABLE = True
except ImportError as e:
    PYSIDE_WEBENGINE_AVAILABLE = False
    logger.warning(f"[HologramWindow] PySide6 QtWebEngineWidgets unavailable: {e}")


class JarvisHolographicWindow(QMainWindow):
    """Futuristic desktop window rendering the WebGL holographic core."""

    def __init__(self, parent=None, fullscreen: bool = False):
        super().__init__(parent)
        self.setWindowTitle("JARVIS V4 Holographic AI Operating System")
        self.setMinimumSize(1024, 768)

        # Frameless dark appearance
        self.setStyleSheet("background-color: #000000;")
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Central WebEngine Widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = QWebEngineView(self)
        self.web_view.setStyleSheet("background: #000000;")

        # Enable WebGL & local storage in web settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        layout.addWidget(self.web_view)

        # Determine target URL: server URL or direct local index.html
        html_path = Path(__file__).resolve().parent.parent / "interface" / "index.html"
        self.local_url = QUrl.fromLocalFile(str(html_path))
        self.web_view.load(self.local_url)

        # Keyboard shortcuts
        # F11: Toggle Fullscreen
        self.shortcut_f11 = QShortcut(QKeySequence("F11"), self)
        self.shortcut_f11.activated.connect(self.toggle_fullscreen)

        # Escape: Exit fullscreen or close if desired
        self.shortcut_esc = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_esc.activated.connect(self.on_escape)

        if fullscreen:
            self.showFullScreen()
        else:
            self.resize(1400, 900)
            # Center on primary screen
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - 1400) // 2, (screen.height() - 900) // 2)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def on_escape(self):
        if self.isFullScreen():
            self.showNormal()

    def set_state(self, state: str, details: str = ""):
        """Forward state update to backend broadcaster."""
        try:
            from communication.broadcaster import get_broadcaster
            get_broadcaster().broadcast_state(state, details)
        except Exception:
            pass


def launch_holographic_window(fullscreen: bool = False):
    """Launch holographic window application."""
    if not PYSIDE_WEBENGINE_AVAILABLE:
        print("[ERROR] PySide6 QtWebEngineWidgets is required to launch desktop window.")
        return None, None

    app = QApplication.instance() or QApplication(sys.argv)
    window = JarvisHolographicWindow(fullscreen=fullscreen)
    window.show()
    return window, app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    win, app = launch_holographic_window(fullscreen=False)
    if app:
        sys.exit(app.exec())
