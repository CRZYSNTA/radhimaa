"""
=============================================================================
JARVIS Safe Executable Desktop Installer
=============================================================================
Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import shutil

def get_desktop_path():
    possible_paths = [
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
        os.path.join(os.path.expanduser("~"), "Desktop")
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return os.path.expanduser("~")

def copy_exe_to_desktop():
    desktop_folder = get_desktop_path()
    project_dir = os.path.abspath(os.path.dirname(__file__))
    
    # 1. Copy JARVIS.exe (Pure Voice)
    dist_exe = os.path.join(project_dir, "dist", "JARVIS.exe")
    if os.path.exists(dist_exe):
        try:
            shutil.copy2(dist_exe, os.path.join(desktop_folder, "JARVIS.exe"))
            print(f"[OK] JARVIS.exe copied to Desktop")
        except Exception as e:
            print(f"[Note JARVIS.exe]: {e}")

    # 2. Copy JARVIS_Widget.exe (Visual Siri Overlay)
    dist_widget_exe = os.path.join(project_dir, "dist", "JARVIS_Widget.exe")
    if os.path.exists(dist_widget_exe):
        try:
            shutil.copy2(dist_widget_exe, os.path.join(desktop_folder, "JARVIS_Widget.exe"))
            print(f"[OK] JARVIS_Widget.exe copied to Desktop")
        except Exception as e:
            print(f"[Note JARVIS_Widget.exe]: {e}")

if __name__ == "__main__":
    copy_exe_to_desktop()
