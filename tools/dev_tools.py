"""
JARVIS V3.0 - Developer & Engineering Automation Tools
Provides local Git status inspecting and code snippet explanation tools.
"""

from __future__ import annotations

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("JARVIS.Tools.Dev")

def git_quick_status(repo_path: Optional[str] = None) -> str:
    """
    Summarizes Git status, current branch, uncommitted changes, and latest commit.
    """
    target = Path(repo_path).expanduser().resolve() if repo_path else Path.cwd()
    if not (target / ".git").exists():
        return f"Directory '{target}' is not a Git repository, sir."

    try:
        branch_res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(target), capture_output=True, text=True, timeout=5
        )
        current_branch = branch_res.stdout.strip() or "HEAD (detached)"

        status_res = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(target), capture_output=True, text=True, timeout=5
        )
        status_lines = [l for l in status_res.stdout.strip().split("\n") if l.strip()]

        commit_res = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            cwd=str(target), capture_output=True, text=True, timeout=5
        )
        last_commit = commit_res.stdout.strip() or "No commits yet"

        summary = [
            f"**Git Repository**: `{target.name}`",
            f"**Branch**: `{current_branch}`",
            f"**Latest Commit**: `{last_commit}`",
            f"**Uncommitted Changes**: {len(status_lines)} file(s)"
        ]
        if status_lines:
            summary.append("\nModified/Untracked Files:")
            for line in status_lines[:8]:
                summary.append(f"  {line}")
            if len(status_lines) > 8:
                summary.append(f"  ... and {len(status_lines) - 8} more files.")

        return "\n".join(summary)

    except Exception as e:
        logger.error(f"[Git Status Error]: {e}")
        return f"Unable to check Git status: {e}"

def explain_code_snippet(code: str, language: Optional[str] = None) -> str:
    """
    Analyzes and explains a code snippet concisely using active AI Provider.
    """
    if not code or not code.strip():
        return "Please provide a valid code snippet to explain, sir."

    lang_hint = f" ({language})" if language else ""
    prompt = (
        f"Explain the following code snippet{lang_hint} concisely for a software engineer:\n\n"
        f"```\n{code[:3000]}\n```\n\n"
        f"Provide:\n1. Purpose / Summary\n2. Key Logic Flow\n3. Potential Edge Cases or Optimizations"
    )

    try:
        from ai.provider import get_ai_provider
        provider = get_ai_provider()
        return provider.generate_response(prompt)
    except Exception as e:
        logger.error(f"[Code Explain Error]: {e}")
        return f"Unable to generate code explanation: {e}"
