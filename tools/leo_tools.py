"""
LEO Native Tools Adapter for JARVIS V4.
Provides native system control, hardware telemetry, application launching,
and Obsidian vault note management directly integrated into JARVIS.
"""

import os
import time
import subprocess
from pathlib import Path
import psutil

VAULT_DIR = Path(r"C:\Users\gowth\das and co")


def get_system_telemetry() -> str:
    """Gets real-time hardware telemetry: CPU usage %, RAM usage %, and disk usage %."""
    try:
        cpu = psutil.cpu_percent(interval=0.05)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("C:").percent

        try:
            from communication.broadcaster import get_broadcaster
            get_broadcaster().broadcast_system_status(cpu, mem)
        except Exception:
            pass

        return f"Current hardware status: CPU is at {cpu}%, RAM utilization is at {mem}%, and primary disk is at {disk}% capacity."
    except Exception as e:
        return f"Error retrieving telemetry: {e}"


def open_application(app_name: str) -> str:
    """Opens or launches an application on Windows."""
    name = app_name.lower().strip()

    app_map = {
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

    cmd = app_map.get(name, name)
    try:
        if cmd.startswith("start "):
            os.system(cmd)
        else:
            subprocess.Popen(cmd, shell=True)
        return f"Opened {app_name}."
    except Exception as e:
        return f"Failed to launch {app_name}: {e}"


def manage_obsidian_note(action: str, title: str, content: str = "") -> str:
    """Manages markdown notes in Gowtham's personal Obsidian vault ('das and co')."""
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
