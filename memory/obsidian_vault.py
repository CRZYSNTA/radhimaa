"""
Obsidian Memory Subsystem for Leo/Jarvis
Connects to 'C:/Users/gowth/das and co' with read-only initialization at startup,
just-in-time note retrieval, and controlled note proposals.
"""

from __future__ import annotations

import os
import re
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("JARVIS.Memory.ObsidianVault")

DEFAULT_VAULT_DIR = Path("C:/Users/gowth/das and co")


class ObsidianVaultManager:
    """Manages the external Obsidian Knowledge Vault for Leo/Jarvis."""

    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = vault_path or DEFAULT_VAULT_DIR
        self._cached_index: Optional[str] = None
        self._cached_priorities: Optional[str] = None

    def is_available(self) -> bool:
        return self.vault_path.exists() and self.vault_path.is_dir()

    def load_startup_context(self) -> Dict[str, str]:
        """
        Loads ONLY VAULT-INDEX.md and Active Priorities.md at startup.
        Does NOT dump the entire vault to memory or LLM context.
        """
        if not self.is_available():
            logger.warning(f"[ObsidianVault] Vault not found at {self.vault_path}")
            return {
                "vault_status": "unavailable",
                "vault_index": "",
                "active_priorities": ""
            }

        # 1. Read VAULT-INDEX.md
        index_file = self.vault_path / "VAULT-INDEX.md"
        if index_file.exists():
            try:
                self._cached_index = index_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"[ObsidianVault] Failed reading VAULT-INDEX.md: {e}")
                self._cached_index = f"Error reading VAULT-INDEX: {e}"
        else:
            self._cached_index = "VAULT-INDEX.md not found in vault root."

        # 2. Read Active Priorities.md
        priorities_file = self.vault_path / "Active Priorities.md"
        if priorities_file.exists():
            try:
                self._cached_priorities = priorities_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"[ObsidianVault] Failed reading Active Priorities.md: {e}")
                self._cached_priorities = f"Error reading Active Priorities: {e}"
        else:
            self._cached_priorities = "Active Priorities.md not found in vault root."

        return {
            "vault_status": "ready",
            "vault_index": self._cached_index,
            "active_priorities": self._cached_priorities
        }

    def read_note(self, relative_path: str) -> Tuple[bool, str]:
        """
        Safely reads any note given relative to the vault root.
        Enforces path containment within the vault directory.
        """
        if not self.is_available():
            return False, f"Vault unavailable at {self.vault_path}"

        clean_rel = relative_path.strip().lstrip("/\\")
        if not clean_rel.endswith(".md"):
            clean_rel += ".md"

        target_file = (self.vault_path / clean_rel).resolve()
        try:
            target_file.relative_to(self.vault_path.resolve())
        except ValueError:
            return False, "Access denied: Path escapes vault boundary."

        if not target_file.exists():
            # Try fuzzy search in subfolders if not found directly
            found = list(self.vault_path.glob(f"**/{Path(clean_rel).name}"))
            if found:
                target_file = found[0]
            else:
                return False, f"Note not found: '{relative_path}'"

        try:
            content = target_file.read_text(encoding="utf-8")
            rel_source = target_file.relative_to(self.vault_path.resolve())
            return True, f"=== Source: {rel_source} ===\n\n{content}"
        except Exception as e:
            return False, f"Error reading note '{relative_path}': {e}"

    def propose_note_update(self, relative_path: str, proposed_content: str) -> Dict[str, Any]:
        """
        Proposes an update to a note without writing it.
        Returns a structured plan for the Action Confirmation Panel.
        """
        clean_rel = relative_path.strip().lstrip("/\\")
        if not clean_rel.endswith(".md"):
            clean_rel += ".md"

        target_file = (self.vault_path / clean_rel).resolve()
        try:
            target_file.relative_to(self.vault_path.resolve())
        except ValueError:
            return {
                "success": False,
                "error": "Access denied: Path escapes vault boundary."
            }

        existing_content = ""
        is_new = not target_file.exists()
        if not is_new:
            try:
                existing_content = target_file.read_text(encoding="utf-8")
            except Exception as e:
                existing_content = f"Error reading existing file: {e}"

        # Frontmatter validation check
        has_frontmatter = proposed_content.strip().startswith("---") and "\n---" in proposed_content[3:]

        return {
            "success": True,
            "requires_confirmation": True,
            "action": "update_note" if not is_new else "create_note",
            "target_path": str(clean_rel),
            "absolute_path": str(target_file),
            "is_new": is_new,
            "has_valid_frontmatter": has_frontmatter,
            "proposed_content": proposed_content,
            "existing_length": len(existing_content),
            "proposed_length": len(proposed_content)
        }

    def execute_confirmed_note_update(self, relative_path: str, content: str) -> Tuple[bool, str]:
        """
        Executes a note write after explicit user confirmation.
        """
        clean_rel = relative_path.strip().lstrip("/\\")
        if not clean_rel.endswith(".md"):
            clean_rel += ".md"

        target_file = (self.vault_path / clean_rel).resolve()
        try:
            target_file.relative_to(self.vault_path.resolve())
        except ValueError:
            return False, "Access denied: Path escapes vault boundary."

        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(content.strip() + "\n", encoding="utf-8")
            rel_display = target_file.relative_to(self.vault_path.resolve())
            return True, f"Successfully updated note: '{rel_display}'."
        except Exception as e:
            return False, f"Failed updating note '{relative_path}': {e}"


_vault_instance: Optional[ObsidianVaultManager] = None

def get_vault_manager() -> ObsidianVaultManager:
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = ObsidianVaultManager()
    return _vault_instance
