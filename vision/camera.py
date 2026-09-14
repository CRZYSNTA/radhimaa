"""
JARVIS V4 - Webcam Vision Subsystem
Implements:
- look: Captures one frame and sends to Gemini for visual inspection.
- watch: Captures a sequence of frames over time for motion, gesture, or state-change analysis.
Follows JARVIS persona: concise declarative reporting, no apologies.
"""

import io
import sys
import time
import logging
from typing import Optional, List, Tuple
import cv2
import config

logger = logging.getLogger("JARVIS.Vision.Camera")

def _open_camera(device_index: int = 0) -> cv2.VideoCapture:
    """Opens camera with DirectShow on Windows for instant initialization without MSMF lag."""
    if sys.platform == "win32":
        try:
            cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
            if cap is not None and cap.isOpened():
                return cap
        except Exception:
            pass
    return cv2.VideoCapture(device_index)

def is_camera_available(device_index: int = 0) -> bool:
    """Check if a webcam device is physically accessible."""
    cap = None
    try:
        cap = _open_camera(device_index)
        if cap is None or not cap.isOpened():
            return False
        ret, frame = cap.read()
        return bool(ret and frame is not None)
    except Exception:
        return False
    finally:
        if cap is not None:
            cap.release()

def capture_camera_bytes(device_index: int = 0) -> Optional[bytes]:
    """
    Captures a single frame from the camera, encodes as JPEG bytes,
    and immediately releases the hardware resource.
    """
    cap = None
    try:
        cap = _open_camera(device_index)
        if not cap.isOpened():
            logger.warning(f"[Camera] Could not open video device {device_index}")
            return None

        # Allow camera auto-exposure to settle for 2-3 frames
        ret, frame = False, None
        for _ in range(3):
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)

        if not ret or frame is None:
            logger.warning("[Camera] Failed to grab frame from device")
            return None

        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if ret:
            return buffer.tobytes()
        return None
    except Exception as e:
        logger.error(f"[Camera] Capture error: {e}")
        return None
    finally:
        if cap is not None:
            cap.release()

def capture_frame_sequence(seconds: float = 3.0, interval: float = 1.0, device_index: int = 0) -> List[Tuple[bytes, float]]:
    """
    Captures a series of frames over a time window.
    Returns list of (jpeg_bytes, offset_seconds).
    """
    frames: List[Tuple[bytes, float]] = []
    cap = None
    try:
        cap = _open_camera(device_index)
        if not cap.isOpened():
            logger.warning(f"[Camera] Could not open device {device_index} for frame sequence")
            return []

        start_time = time.time()
        next_capture = start_time

        # Let auto-exposure settle
        for _ in range(2):
            cap.read()

        while (time.time() - start_time) <= seconds:
            now = time.time()
            if now >= next_capture:
                ret, frame = cap.read()
                if ret and frame is not None:
                    offset = now - start_time
                    ret_enc, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    if ret_enc:
                        frames.append((buffer.tobytes(), offset))
                next_capture = now + interval
            time.sleep(0.05)

        return frames
    except Exception as e:
        logger.error(f"[Camera] Error during sequence capture: {e}")
        return frames
    finally:
        if cap is not None:
            cap.release()

def look(prompt: str = "Describe what is in front of the camera.", reason: str = "") -> str:
    """
    Captures one frame through the camera and returns an analysis via Gemini.
    """
    img_bytes = capture_camera_bytes()
    if not img_bytes:
        return "I'm afraid the camera is unreachable, sir."

    try:
        from ai.gemini_provider import GeminiProvider
        provider = GeminiProvider()
        if provider.is_available():
            analysis = provider.analyze_image(img_bytes, prompt)
            if analysis:
                return analysis.strip()
    except Exception as e:
        logger.error(f"[Vision Look Error]: {e}")

    return "I have captured the frame, but cannot analyze it at present, sir."

def watch(seconds: int = 4, prompt: str = "Analyze the movement or change across these frames.", reason: str = "") -> str:
    """
    Watches through the camera over a short window and analyzes movement or action changes via Gemini.
    """
    sec = max(2, min(10, seconds))
    frames = capture_frame_sequence(seconds=sec, interval=1.0)
    if not frames:
        return "I'm afraid the camera is unreachable, sir."

    try:
        from ai.gemini_provider import GeminiProvider
        provider = GeminiProvider()
        if provider.is_available():
            analysis = provider.analyze_frames(frames, prompt)
            if analysis:
                return analysis.strip()
    except Exception as e:
        logger.error(f"[Vision Watch Error]: {e}")

    return f"Watched {len(frames)} frames across {sec} seconds, but could not complete analysis, sir."

def analyze_camera(prompt: str = "Describe what you see in front of the camera.") -> str:
    """Backwards compatibility alias for look()."""
    return look(prompt)

