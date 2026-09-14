"""
=============================================================================
JARVIS Tools: Computer System & PyAutoGUI Automation
=============================================================================
Provides PyAutoGUI computer automation actions:
 - Volume up/down/mute
 - Screenshot capture
 - Window minimize/maximize/close/scroll
 - System lock screen
 - Application launching & closing

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import ctypes
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

def volume_up() -> str:
    pyautogui.FAILSAFE = False
    pyautogui.press("volumeup")
    return "Volume increased, sir."

def volume_down(level: int = 50) -> str:
    pyautogui.FAILSAFE = False
    for _ in range(max(1, level // 10)):
        pyautogui.press("volumedown")
    return "Volume decreased, sir."

def volume_set(level: int = 50) -> str:
    pyautogui.FAILSAFE = False
    level = max(0, min(100, level))
    pyautogui.press("volumemute")
    for _ in range(50):
        pyautogui.press("volumeup")
    for _ in range(50 - level // 2):
        pyautogui.press("volumedown")
    return f"Volume set to {level}%, sir."

def volume_mute() -> str:
    pyautogui.FAILSAFE = False
    pyautogui.press("volumemute")
    return "Volume toggled, sir."

def control_volume(action: str = "up") -> str:
    pyautogui.FAILSAFE = False
    a = action.lower()
    if "up" in a or "increase" in a:
        return volume_up()
    elif "down" in a or "decrease" in a:
        return volume_down()
    elif "mute" in a:
        return volume_mute()
    elif "zero" in a or "min" in a:
        return volume_set(0)
    return volume_up()

def take_screenshot() -> str:
    pyautogui.FAILSAFE = False
    try:
        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
        os.makedirs(pictures_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(pictures_dir, f"JARVIS_{timestamp}.png")
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return f"Screenshot saved to Pictures folder, sir."
    except Exception as e:
        return f"Failed to take screenshot: {e}"

def lock_screen() -> str:
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked successfully, sir."
    except Exception as e:
        return f"Could not lock screen: {e}"

def control_media(action: str) -> str:
    pyautogui.FAILSAFE = False
    a = action.lower()
    if "pause" in a or "play" in a or "stop" in a:
        pyautogui.press("playpause")
        return "Toggling playback, sir."
    elif "next" in a or "skip" in a:
        pyautogui.press("nexttrack")
        return "Skipping to next track, sir."
    elif "previous" in a or "back" in a:
        pyautogui.press("prevtrack")
        return "Playing previous track, sir."
    return "Media updated, sir."

def control_window(action: str) -> str:
    pyautogui.FAILSAFE = False
    a = action.lower()
    if "minimize" in a:
        pyautogui.hotkey("win", "down")
        return "Minimizing window, sir."
    elif "maximize" in a:
        pyautogui.hotkey("win", "up")
        return "Maximizing window, sir."
    elif "close" in a:
        pyautogui.hotkey("alt", "f4")
        return "Closing active window, sir."
    elif "scroll up" in a:
        pyautogui.scroll(600)
        return "Scrolling up, sir."
    elif "scroll down" in a:
        pyautogui.scroll(-600)
        return "Scrolling down, sir."
    return "Window state updated, sir."

def open_app(target: str) -> str:
    """Launches an application natively by delegating to applications manager."""
    from tools.applications import open_app as app_open
    return app_open(target)

def close_app(target: str) -> str:
    t = target.lower()
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/f", "/im", f"{t}.exe"], capture_output=True)
        return f"Closed {target}, sir."
    except Exception as e:
        return f"Could not close {target}: {e}"

def get_time() -> str:
    return f"The current time is {datetime.now().strftime('%I:%M %p')}, sir."

def get_date() -> str:
    return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}, sir."

def tile_window_left() -> str:
    """Snaps the currently active window to the left half of the display."""
    pyautogui.FAILSAFE = False
    pyautogui.hotkey("win", "left")
    return "Tiled active window to the left, sir."

def tile_window_right() -> str:
    """Snaps the currently active window to the right half of the display."""
    pyautogui.FAILSAFE = False
    pyautogui.hotkey("win", "right")
    return "Tiled active window to the right, sir."

def minimize_all_windows() -> str:
    """Minimizes all windows to display the Windows desktop."""
    pyautogui.FAILSAFE = False
    pyautogui.hotkey("win", "d")
    return "Minimizing all windows to show the desktop, sir."

def snap_window(direction: str = "left") -> str:
    """Snaps the active window in a given direction (left, right, up, down)."""
    d = direction.lower().strip()
    pyautogui.FAILSAFE = False
    if d in ("left", "west"):
        pyautogui.hotkey("win", "left")
        return "Snapped window to the left, sir."
    elif d in ("right", "east"):
        pyautogui.hotkey("win", "right")
        return "Snapped window to the right, sir."
    elif d in ("up", "max", "maximize", "top"):
        pyautogui.hotkey("win", "up")
        return "Maximized window, sir."
    elif d in ("down", "min", "minimize", "bottom"):
        pyautogui.hotkey("win", "down")
        return "Minimized window, sir."
    return f"Unknown snap direction '{direction}', sir."


if __name__ == "__main__":
    print("Testing computer tools...")
    print(volume_up())