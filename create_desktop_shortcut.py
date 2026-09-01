"""
=============================================================================
JARVIS Desktop Shortcut Creator (Instant Desktop Launcher)
=============================================================================
Goal: Creates 1-click desktop launchers on your Desktop that instantly pop up
      JARVIS Siri Orb Overlay + Voice Engine + Server on screen!

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
    app_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "jarvis_app.py"))
    pythonw_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "pythonw.exe"))
    python_path = os.path.abspath(sys.executable)

    # 1. Create Launch_JARVIS.vbs (Silent launcher that pops up Siri Orb)
    vbs_path = os.path.join(desktop_folder, "Launch_JARVIS.vbs")
    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.Run """{pythonw_path}"" ""{app_script_path}""", 0, False\n'
    )
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    # 2. Create Launch_JARVIS.bat (1-Click Batch launcher for Desktop)
    bat_path = os.path.join(desktop_folder, "Launch_JARVIS.bat")
    bat_content = (
        f'@echo off\n'
        f'start "" "{pythonw_path}" "{app_script_path}"\n'
    )
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    print("==========================================================")
    print("[OK] DESKTOP LAUNCHERS CREATED SUCCESSFULLY!")
    print(f" - VBS Launcher : {vbs_path}")
    print(f" - BAT Launcher : {bat_path}")
    print(" - Usage: Double-click either icon on your Desktop to launch JARVIS!")
    print("==========================================================")

if __name__ == "__main__":
    create_shortcut()
