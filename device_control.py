"""
=============================================================================
JARVIS Device & System Action Controller
=============================================================================
Goal: Execute real system control commands on your laptop when requested by voice:
 - Lock screen (ctypes LockWorkStation)
 - Open apps (Chrome, Spotify, YouTube, Notepad, Calculator)
 - Control volume & mute
 - Launch Air-Gesture Virtual Mouse

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import ctypes
import os
import subprocess
import sys
import webbrowser

def lock_screen():
    """Instantly locks the Windows PC screen."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked successfully, sir."
    except Exception as e:
        return f"Could not lock screen: {e}"

def open_app_or_website(target: str) -> str:
    """Opens popular applications or websites."""
    t = target.lower()

    if "youtube" in t:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube, sir."
    elif "spotify" in t:
        webbrowser.open("https://open.spotify.com")
        return "Opening Spotify, sir."
    elif "google" in t or "chrome" in t:
        webbrowser.open("https://www.google.com")
        return "Opening Google, sir."
    elif "calculator" in t:
        os.system("calc")
        return "Opening Calculator, sir."
    elif "notepad" in t:
        os.system("notepad")
        return "Opening Notepad, sir."
    else:
        # Fallback: search Google for the target
        webbrowser.open(f"https://www.google.com/search?q={target}")
        return f"Searching Google for {target}, sir."

def execute_device_command(user_query: str) -> str:
    """Parses voice query for device control commands."""
    q = user_query.lower()

    if "lock" in q and ("screen" in q or "laptop" in q or "pc" in q or "computer" in q):
        return lock_screen()

    if "open" in q:
        # Extract target after 'open'
        parts = q.split("open", 1)
        if len(parts) > 1:
            target = parts[1].strip()
            return open_app_or_website(target)

    if "gesture" in q or "camera mouse" in q or "virtual mouse" in q:
        try:
            gesture_script = os.path.join(os.path.dirname(__file__), "gesture_mouse.py")
            subprocess.Popen([sys.executable, gesture_script])
            return "Launching Air-Gesture Virtual Mouse now, sir."
        except Exception as e:
            return f"Failed to launch gesture control: {e}"

    return None

if __name__ == "__main__":
    print("Testing device lock check...")
    # Uncomment to test locking PC:
    # print(lock_screen())
