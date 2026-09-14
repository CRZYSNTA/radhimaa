"""
JARVIS V3.0 - Application Management Tools
Handles launching, closing, and querying Windows desktop applications.
"""

import os
import sys
import subprocess
import webbrowser
import psutil
from typing import List, Dict, Optional

import json

APP_ALIASES = {
    "whatsapp": "whatsapp:",
    "whatsapp desktop": "whatsapp:",
    "chrome": "chrome",
    "google chrome": "chrome",
    "browser": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "taskmgr": "taskmgr",
    "settings": "ms-settings:",
    "explorer": "explorer",
    "files": "explorer",
    "file explorer": "explorer",
    "spotify": "spotify:",
    "telegram": "tg:",
    "discord": "discord:",
    "camera": "microsoft.windows.camera:",
    "photos": "ms-photos:",
    "paint": "mspaint",
    "clock": "ms-clock:",
    "alarms": "ms-clock:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    "vscode": "code",
    "vs code": "code",
    "code": "code",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
}

_start_apps_cache = None

def _get_start_apps() -> List[Dict[str, str]]:
    """Caches and returns list of installed Windows Start Apps."""
    global _start_apps_cache
    if _start_apps_cache is not None:
        return _start_apps_cache
    if sys.platform != "win32":
        return []
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json"]
        out = subprocess.check_output(cmd, text=True, timeout=3.0)
        _start_apps_cache = json.loads(out)
    except Exception:
        _start_apps_cache = []
    return _start_apps_cache

def find_installed_windows_app(name: str) -> Optional[str]:
    """Finds AppID for an installed Windows app matching name."""
    clean = name.strip().lower()
    apps = _get_start_apps()
    for app in apps:
        if clean == app.get("Name", "").lower():
            return app.get("AppID")
    for app in apps:
        if clean in app.get("Name", "").lower():
            return app.get("AppID")
    return None

def open_app(name: str) -> str:
    """Launches a desktop application natively by name or alias."""
    clean = name.strip().lower()

    # Direct URL check
    if clean.startswith("http://") or clean.startswith("https://"):
        webbrowser.open(clean)
        return f"Opening URL: {clean}, sir."

    # Known web targets
    if "youtube" in clean:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube, sir."
    if clean in ("google", "search"):
        webbrowser.open("https://www.google.com")
        return "Opening Google, sir."

    # Look up known alias / protocol
    cmd = APP_ALIASES.get(clean, clean)
    try:
        if sys.platform == "win32":
            # Protocol URI (e.g. whatsapp:, spotify:, ms-settings:)
            if ":" in cmd and not cmd.startswith("c:"):
                os.system(f'start "" "{cmd}"')
                return f"Launching {name} app, sir."
            
            # Dynamic Windows Start App lookup (UWP / Store / Installed desktop apps)
            app_id = find_installed_windows_app(clean)
            if app_id:
                os.system(f'start explorer.exe "shell:AppsFolder\\{app_id}"')
                return f"Launching {name} app, sir."

            # Standard Win32 executable
            subprocess.Popen(f'start "" "{cmd}"', shell=True)
            return f"Launching {name}, sir."
        else:
            subprocess.Popen([cmd])
            return f"Launching {name}, sir."
    except Exception as e:
        return f"Could not launch {name} locally ({e}), sir."

launch_application = open_app

def close_app(name: str) -> str:
    """Closes matching application process."""
    clean = name.strip().lower()
    closed_count = 0

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pname = proc.info['name'].lower()
            if clean in pname or pname.startswith(clean):
                proc.terminate()
                closed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if closed_count > 0:
        return f"Closed {closed_count} instances of {name}, sir."

    # Fallback to taskkill on Windows
    if sys.platform == "win32":
        try:
            res = subprocess.run(["taskkill", "/f", "/im", f"{clean}.exe"], capture_output=True, text=True)
            if "SUCCESS" in res.stdout:
                return f"Closed {name}, sir."
        except Exception:
            pass

    return f"No running application found matching '{name}', sir."

def list_running_apps() -> List[str]:
    """Returns unique names of actively running GUI applications."""
    apps = set()
    for proc in psutil.process_iter(['name']):
        try:
            pname = proc.info['name']
            if pname.endswith(".exe"):
                apps.add(pname[:-4])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(list(apps))
