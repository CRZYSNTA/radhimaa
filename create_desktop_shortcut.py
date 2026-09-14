"""
=============================================================================
JARVIS Pure Voice Assistant Desktop Launcher Creator
=============================================================================
Goal: Desktop shortcut that launches Pure Iron Man Voice Assistant!

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import sys

def get_desktop_path():
    possible_paths = [
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
        os.path.join(os.path.expanduser("~"), "Desktop")
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return os.path.expanduser("~")

def create_shortcut():
    desktop_folder = get_desktop_path()
    project_dir = os.path.abspath(os.path.dirname(__file__))
    app_script_path = os.path.abspath(os.path.join(project_dir, "jarvis_voice_assistant.py"))
    python_path = os.path.abspath(sys.executable)

    # 1. Create Launch_JARVIS.bat (Pure Voice Launcher)
    bat_path = os.path.join(desktop_folder, "Launch_JARVIS.bat")
    bat_content = (
        f'@echo off\n'
        f'cd /d "{project_dir}"\n'
        f'"{python_path}" "{app_script_path}"\n'
        f'pause\n'
    )
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    print("==========================================================")
    print("[OK] PURE VOICE DESKTOP LAUNCHER CREATED SUCCESSFULLY!")
    print(f" - Working Directory: {project_dir}")
    print(f" - BAT Launcher     : {bat_path}")
    print("==========================================================")

if __name__ == "__main__":
    create_shortcut()
