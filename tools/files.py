"""
JARVIS V3.0 - Sandboxed File Tools
Provides secure, path-restricted file system operations.
Directory traversal and unauthorized system paths are strictly blocked.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from core.permissions import is_path_safe, is_sensitive_path

def list_directory(path: str = ".") -> str:
    """Lists files and folders in a safe directory, filtering out sensitive secrets and configs."""
    target = Path(path).resolve()
    if is_sensitive_path(str(target)) or not is_path_safe(str(target)):
        return "Access Denied: I'm afraid I cannot access that directory, sir."
    if not target.exists():
        return f"Error: Directory '{path}' does not exist."
    if not target.is_dir():
        return f"Error: '{path}' is not a directory."

    try:
        items = []
        for item in target.iterdir():
            # Filter sensitive secrets, config, keys, and git folders
            if is_sensitive_path(str(item)):
                continue
            t = "DIR" if item.is_dir() else "FILE"
            size = item.stat().st_size if item.is_file() else "-"
            items.append(f"[{t}] {item.name} ({size})")
        return "\n".join(items) if items else "(Empty directory)"
    except Exception as e:
        return f"Error reading directory: {e}"

def read_file(path: str, max_bytes: int = 100000) -> str:
    """Reads text content from a safe file path, strictly blocking sensitive credentials."""
    target = Path(path).resolve()
    if is_sensitive_path(str(target)) or not is_path_safe(str(target)):
        return "Access Denied: I'm afraid I cannot access that file, sir."
    if not target.exists() or not target.is_file():
        return f"Error: File '{path}' does not exist."

    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes)
        return content
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str) -> str:
    """Writes content to a file within safe directory boundaries, blocking overwrites of sensitive files."""
    target = Path(path).resolve()
    if is_sensitive_path(str(target)) or not is_path_safe(str(target)):
        return "Access Denied: I'm afraid I cannot access that file, sir."

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File successfully written to '{path}' ({len(content)} chars)."
    except Exception as e:
        return f"Error writing file: {e}"

def delete_file(path: str) -> str:
    """Safely deletes a file within safe directories, blocking deletion of sensitive system files."""
    target = Path(path).resolve()
    if is_sensitive_path(str(target)) or not is_path_safe(str(target)):
        return "Access Denied: I'm afraid I cannot access that file, sir."
    if not target.exists():
        return f"Error: File '{path}' does not exist."

    try:
        if target.is_file():
            target.unlink()
            return f"File '{path}' deleted successfully."
        else:
            return f"Error: '{path}' is a directory, not a file."
    except Exception as e:
        return f"Error deleting file: {e}"
