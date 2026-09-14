"""
JARVIS Vision Subsystem
Multimodal screen analysis, air-gesture virtual mouse, and webcam vision.
"""

from vision.screen import analyze_screen, capture_screen, capture_screen_bytes
from vision.gestures import GestureMouse, start_gesture_mouse, stop_gesture_mouse
from vision.camera import analyze_camera, capture_camera_bytes, is_camera_available

__all__ = [
    "analyze_screen",
    "capture_screen",
    "capture_screen_bytes",
    "GestureMouse",
    "start_gesture_mouse",
    "stop_gesture_mouse",
    "analyze_camera",
    "capture_camera_bytes",
    "is_camera_available",
]