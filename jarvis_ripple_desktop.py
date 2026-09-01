"""
=============================================================================
JARVIS Originkit Ripple-Study Transparent Desktop HUD Overlay
=============================================================================
Goal: Displays the Originkit Ripple Study ASCII Matrix visualizer as a
      borderless, transparent, always-on-top Desktop HUD overlay window!

Replaces static Tkinter circle with a futuristic glowing Matrix Ripple field!

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import sys
import webview

HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "ripple_overlay.html"))

def launch_ripple_overlay():
    """Launches pywebview transparent frameless desktop overlay."""
    print("==========================================================")
    print("[START] LAUNCHING ORIGINKIT RIPPLE STUDY DESKTOP OVERLAY...")
    print("==========================================================")

    # Create frameless, transparent, always-on-top window
    window = webview.create_window(
        title="JARVIS Ripple Overlay",
        url=HTML_PATH,
        width=1000,
        height=700,
        frameless=True,
        easy_drag=True,
        transparent=True,
        on_top=True
    )
    
    webview.start(debug=False)

if __name__ == "__main__":
    launch_ripple_overlay()
