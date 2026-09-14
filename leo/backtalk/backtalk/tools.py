"""LEO Automation Tools (The Hands).

Provides native system control, hardware telemetry, application launching,
media control, web navigation, and Obsidian vault operations.
"""
import os
import json
import time
import ctypes
import webbrowser
import subprocess
from pathlib import Path
import psutil

from backtalk.config import CFG
from backtalk.vlog import log

BUS_DIR = Path(CFG.get("signals_dir") or "d:/agent/backtalk")
VAULT_DIR = Path(r"C:\Users\gowth\das and co")

# Windows Virtual Key Codes for Media & Volume Control
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3


def _send_key(vk_code: int):
    """Press and release a virtual key using Windows user32."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(vk_code, 0, 2, 0)  # KEYEVENTF_KEYUP = 2
        return True
    except Exception as e:
        log(f"[tools] keybd_event error: {e}")
        return False


def get_system_telemetry() -> str:
    """Gets real-time hardware telemetry: CPU usage %, RAM usage %, and disk usage %.
    Also updates the HUD telemetry bus for the holographic interface.
    """
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("C:").percent

        # Write to HUD telemetry signal bus
        try:
            telemetry_path = BUS_DIR / ".voice_telemetry"
            telemetry_path.write_text(json.dumps({
                "cpu": round(cpu),
                "ram": round(mem),
                "disk": round(disk),
                "ts": time.time()
            }))
        except Exception:
            pass

        return f"Current hardware status: CPU is at {cpu}%, RAM utilization is at {mem}%, and primary disk is at {disk}% capacity."
    except Exception as e:
        return f"Error retrieving telemetry: {e}"


def media_control(action: str) -> str:
    """Controls Windows media playback and system volume.
    
    Args:
        action: One of:
            - 'volume_up' / 'louder': Increases system volume.
            - 'volume_down' / 'softer': Decreases system volume.
            - 'mute' / 'unmute': Toggles mute.
            - 'play' / 'pause' / 'toggle': Toggles play/pause for active media (Spotify, YouTube).
            - 'next' / 'skip': Skips to next track.
            - 'previous' / 'prev': Jumps to previous track.
    """
    act = action.lower().strip()
    log(f"[tools] Executing media_control: {act}")

    if "up" in act or "louder" in act:
        for _ in range(5):
            _send_key(VK_VOLUME_UP)
        return "Increased system volume."
    elif "down" in act or "softer" in act or "lower" in act:
        for _ in range(5):
            _send_key(VK_VOLUME_DOWN)
        return "Decreased system volume."
    elif "mute" in act:
        _send_key(VK_VOLUME_MUTE)
        return "Toggled master volume mute."
    elif "next" in act or "skip" in act:
        _send_key(VK_MEDIA_NEXT_TRACK)
        return "Skipped to the next track."
    elif "prev" in act or "back" in act:
        _send_key(VK_MEDIA_PREV_TRACK)
        return "Returned to the previous track."
    elif "play" in act or "pause" in act or "stop" in act or "toggle" in act:
        _send_key(VK_MEDIA_PLAY_PAUSE)
        return "Toggled media playback."
    else:
        return f"Unrecognized media action: '{action}'."


def open_application(app_name: str) -> str:
    """Opens or launches an application on Windows.
    
    Args:
        app_name: The common name of the application, e.g. 'notepad', 'calculator',
                  'chrome', 'spotify', 'obsidian', 'code', 'terminal', 'explorer',
                  or 'task manager'.
    """
    name = app_name.lower().strip()
    log(f"[tools] Opening application: {name}")

    APP_MAP = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "chrome": "start chrome",
        "browser": "start chrome",
        "edge": "start msedge",
        "spotify": "start spotify:",
        "obsidian": "start obsidian://",
        "terminal": "wt.exe",
        "cmd": "cmd.exe",
        "code": "code",
        "vscode": "code",
        "vs code": "code",
        "explorer": "explorer.exe",
        "files": "explorer.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
    }

    cmd = APP_MAP.get(name, name)
    try:
        if cmd.startswith("start "):
            os.system(cmd)
        else:
            subprocess.Popen(cmd, shell=True)
        return f"Opened {app_name}."
    except Exception as e:
        return f"Failed to launch {app_name}: {e}"


def open_url_or_search(query_or_url: str) -> str:
    """Opens a website in the default browser, or searches Google if a query is provided.
    
    Args:
        query_or_url: A web address (e.g. 'https://github.com') or a search query (e.g. 'latest AI news').
    """
    target = query_or_url.strip()
    log(f"[tools] Web navigation: {target}")

    if target.startswith("http://") or target.startswith("https://") or ("." in target and " " not in target):
        url = target if target.startswith("http") else "https://" + target
        webbrowser.open(url)
        return f"Opened {url} in browser."
    else:
        import urllib.parse
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(target)}"
        webbrowser.open(search_url)
        return f"Searching Google for: '{target}'."


def manage_obsidian_note(action: str, title: str, content: str = "") -> str:
    """Manages markdown notes in Gowtham's personal Obsidian vault ('das and co').
    
    Args:
        action: 'create', 'append', 'read', or 'list'.
        title: The note title or filename (e.g. 'Project Idea', 'Daily Log').
        content: The text content to write or append (required for 'create' or 'append').
    """
    try:
        VAULT_DIR.mkdir(parents=True, exist_ok=True)

        if action.lower() == "list":
            files = [f.stem for f in VAULT_DIR.glob("*.md") if not f.name.startswith(".")]
            return f"Vault notes in 'das and co': {', '.join(files[:15]) or 'No notes found'}."

        safe_title = title.replace("/", "_").replace("\\", "_")
        if not safe_title.endswith(".md"):
            safe_title += ".md"
        note_path = VAULT_DIR / safe_title

        if action.lower() == "read":
            if not note_path.exists():
                return f"Note '{title}' does not exist in the vault."
            return note_path.read_text(encoding="utf-8")

        elif action.lower() == "create":
            note_path.write_text(content, encoding="utf-8")
            return f"Created note '{title}' in your Obsidian vault."

        elif action.lower() == "append":
            with open(note_path, "a", encoding="utf-8") as f:
                f.write(("\n\n" if note_path.exists() else "") + content)
            return f"Appended content to note '{title}'."

        else:
            return f"Unknown vault action: '{action}'."
    except Exception as e:
        return f"Obsidian vault error: {e}"


# List of tools to register with Gemini
SYSTEM_TOOLS = [
    get_system_telemetry,
    media_control,
    open_application,
    open_url_or_search,
    manage_obsidian_note
]
