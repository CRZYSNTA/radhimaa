"""
=============================================================================
JARVIS Native Windows Auto-Start Installer
=============================================================================
Goal: Configures Windows to silently start native JARVIS on boot.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import sys

def install_autostart():
    pythonw_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "pythonw.exe"))
    tray_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tray_app.py"))

    appdata = os.environ.get("APPDATA")
    if not appdata:
        print("[ERROR] Could not determine APPDATA directory.")
        return

    startup_folder = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    vbs_path = os.path.join(startup_folder, "JARVIS_AutoStart.vbs")

    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.Run """{pythonw_path}"" ""{tray_script_path}""", 0, False\n'
    )

    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        print("==========================================================")
        print("[OK] WINDOWS NATIVE AUTO-START RESTORED SUCCESSFULLY!")
        print(f" - Startup File: {vbs_path}")
        print("==========================================================")
    except Exception as e:
        print(f"[ERROR] Error creating startup script: {e}")

if __name__ == "__main__":
    install_autostart()
