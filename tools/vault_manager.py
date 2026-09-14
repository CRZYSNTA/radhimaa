"""
JARVIS V4 - Obsidian Vault Management Tools (LEO Capabilities)
Provides tool actions to inspect, search, write, and open the persistent Markdown vault:
- Daily note logging (01 - Daily Notes)
- Inbox quick capture (00 - Inbox)
- Active priorities inspection & updates
- Project context retrieval (Polacraft, Canvs, Screenplays, Cyber & Dev, Career, Content, Personal)
- Bi-directional sync with SQLite
"""

from __future__ import annotations

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import config
from memory.vault_sync import (
    ensure_vault_initialized, read_vault_file, append_vault_note,
    sync_memory_to_vault, sync_vault_to_memory, VAULT_DIR,
    get_active_priorities as _get_priorities,
    update_active_priorities as _update_priorities,
    get_vault_index as _get_index,
    log_daily_note as _log_daily,
    capture_inbox_item as _capture_inbox,
    read_project_context as _read_project,
)

logger = logging.getLogger("JARVIS.Tools.VaultManager")


def read_memory_vault(category: str = "all") -> str:
    """
    Reads notes from the Obsidian-compatible Markdown memory vault.
    Args:
        category: 'preferences', 'projects', 'lessons', 'identity', 'priorities', 'index', or 'all'.
    """
    ensure_vault_initialized()
    cat = category.strip().lower()

    if cat in ("preferences", "pref", "profile"):
        return read_vault_file("Preferences.md")
    elif cat in ("projects", "milestones", "todos"):
        return read_vault_file("Projects.md")
    elif cat in ("lessons", "rules", "corrections"):
        return read_vault_file("Lessons.md")
    elif cat in ("identity", "profile", "agent"):
        return read_vault_file("Identity.md")
    elif cat in ("priorities", "active priorities"):
        return _get_priorities()
    elif cat in ("index", "vault index"):
        return _get_index()
    else:
        # Return overview of vault folders and root files
        files = list(VAULT_DIR.glob("*.md"))
        subdirs = [d.name for d in VAULT_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
        lines = [f"### 📂 Obsidian Memory Vault (`{VAULT_DIR}`):\n"]
        if subdirs:
            lines.append("**Folders:** " + ", ".join(sorted(subdirs)) + "\n")
        for f in sorted(files):
            try:
                excerpt = f.read_text(encoding="utf-8")[:300].strip()
                lines.append(f"#### 📄 {f.name}\n{excerpt}...\n")
            except Exception:
                pass
        return "\n".join(lines)


def write_memory_vault_note(category: str, title: str, content: str) -> str:
    """Appends a new note or learned lesson into the memory vault."""
    return append_vault_note(category, title, content)


def sync_memory_vault() -> str:
    """Triggers bi-directional sync between SQLite user memory and Obsidian vault files."""
    export_res = sync_memory_to_vault()
    import_res = sync_vault_to_memory()
    return f"{export_res}\n{import_res}"


def open_obsidian_vault() -> str:
    """Opens the Obsidian vault directory in File Explorer or launches Obsidian URI."""
    ensure_vault_initialized()
    try:
        if os.name == "nt":
            os.startfile(str(VAULT_DIR))
            return f"Opened Obsidian vault at `{VAULT_DIR}`, sir."
        else:
            subprocess.run(["xdg-open", str(VAULT_DIR)], check=True)
            return f"Opened Obsidian vault at `{VAULT_DIR}`, sir."
    except Exception as e:
        return f"Unable to open vault directory: {e}"


def get_active_priorities() -> str:
    """Retrieves Active Priorities.md from Gowtham's vault."""
    return _get_priorities()


def update_active_priorities(content: str) -> str:
    """Overwrites or updates Active Priorities.md in Gowtham's vault."""
    return _update_priorities(content)


def log_daily_note(entry: str) -> str:
    """Appends a dated timestamped entry into today's daily note in 01 - Daily Notes/."""
    return _log_daily(entry)


def capture_inbox_item(text: str) -> str:
    """Captures a quick thought, idea, or raw task into 00 - Inbox/."""
    return _capture_inbox(text)


def read_project_context(project_name: str) -> str:
    """Retrieves project context from vault for Polacraft, Canvs, Screenplays, Cyber/Dev, Career, Content."""
    return _read_project(project_name)
