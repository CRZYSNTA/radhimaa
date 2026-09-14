"""
JARVIS V4 - Remote Desktop Controller (Mobile Companion Integration)
Translates touch gestures, relative motion, clicks, and keyboard events from the mobile
companion app into native OS actions, and captures low-latency compressed screen frames.
Extracted and modernized from D:\\agent\\transfer_bundle\\mobile_integration\\desktop_controller.py.
"""

from __future__ import annotations

import io
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("JARVIS.Mobile.DesktopController")

try:
    import pyautogui
    from PIL import Image
    pyautogui.PAUSE = 0.001
    pyautogui.FAILSAFE = True
    HAS_GUI = True
except ImportError:
    HAS_GUI = False
    logger.warning("[DesktopController] pyautogui or PIL not available; GUI control disabled.")


def handle_touchpad_event(action: str, dx: float = 0, dy: float = 0, button: str = "left") -> Dict[str, Any]:
    """
    Handles relative mouse motion, clicks, drag, and scrolling from mobile trackpad.
    """
    if not HAS_GUI:
        return {"status": "error", "message": "GUI automation not available"}

    try:
        if action == "move":
            pyautogui.moveRel(dx, dy)
        elif action == "click":
            pyautogui.click(button=button)
        elif action == "double_click":
            pyautogui.doubleClick(button=button)
        elif action == "right_click":
            pyautogui.click(button="right")
        elif action == "scroll":
            # Scale scroll intensity appropriately
            pyautogui.scroll(int(dy))
        elif action == "mouse_down":
            pyautogui.mouseDown(button=button)
        elif action == "mouse_up":
            pyautogui.mouseUp(button=button)
        return {"status": "ok", "action": action}
    except Exception as e:
        logger.error(f"[DesktopController] Touchpad event error: {e}")
        return {"status": "error", "error": str(e)}


def handle_keyboard_event(action: str, text: str = "", key: str = "") -> Dict[str, Any]:
    """
    Handles text typing, single key presses, and hotkeys.
    """
    if not HAS_GUI:
        return {"status": "error", "message": "GUI automation not available"}

    try:
        if action == "type" and text:
            pyautogui.write(text, interval=0.01)
        elif action == "key" and key:
            pyautogui.press(key)
        elif action == "hotkey" and text:
            keys = [k.strip() for k in text.split("+") if k.strip()]
            if keys:
                pyautogui.hotkey(*keys)
        return {"status": "ok", "action": action}
    except Exception as e:
        logger.error(f"[DesktopController] Keyboard event error: {e}")
        return {"status": "error", "error": str(e)}


def capture_screen_jpeg(quality: int = 40, scale: float = 0.5) -> bytes:
    """
    Captures a screenshot and compresses it as a JPEG byte buffer for low-latency streaming.
    """
    if not HAS_GUI:
        return b""

    try:
        img = pyautogui.screenshot()
        if scale != 1.0:
            new_w = max(1, int(img.width * scale))
            new_h = max(1, int(img.height * scale))
            img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"[DesktopController] Screen capture error: {e}")
        return b""
