"""
JARVIS V4 - Obsidian Markdown Memory Vault Sync Engine (LEO Full Stack)
Interacts directly with Gowtham's authoritative Obsidian vault at 'C:/Users/gowth/das and co':
 - 00 - Inbox/: Capture raw thoughts and ideas
 - 01 - Daily Notes/: Dated logs (e.g. 09 - September 2026/YYYY-MM-DD.md)
 - 02 - Polacraft/: Orders, inventory, operations
 - 03 - Canvs/: Brand, design, collections, roadmap
 - 04 - Screenplays/: Beat sheets, active drafts
 - 05 - Cyber & Dev/: Labs, skill roadmap
 - 06 - Career/: Job applications, target roles
 - 07 - Content/: Copywriting, creative media
 - 08 - Personal/: Routines, personal goals
 - Active Priorities.md: Single source of truth for open priorities
 - VAULT-INDEX.md: Root index & operating manual
Preserves bi-directional sync with SQLite memory.
"""

from __future__ import annotations

import os
import re
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import config
from memory.user_memory import user_memory

logger = logging.getLogger("JARVIS.Memory.VaultSync")

DAS_AND_CO = Path("C:/Users/gowth/das and co")
VAULT_DIR: Path = DAS_AND_CO if DAS_AND_CO.exists() else (Path(config.BASE_DIR) / "vault")


DEFAULT_IDENTITY_MD = """# ⚡ JARVIS V4 (LEO Stack) - Agent Profile & Core Directives

**Name**: JARVIS / LEO  
**Role**: Personal Workflow Assistant & Engineering Pair-Programmer for Gowtham  
**Tone**: Quietly encouraging, calm, direct, precise on technical work, loose on creative work  
**Safety Tier**: Authoritative 3-tier security model (SAFE, CONFIRM, BLOCKED)  
"""

DEFAULT_PREFERENCES_MD = """# 👤 User Preferences & Profile

- **Preferred Voice**: Adam (ElevenLabs / `pNInz6obpgDQGcFmaJgB`) with Kokoro / Edge-TTS fallback
- **Model**: gemini-3.6-flash
- **Projects**: Polacraft, Canvs, Screenplays, Cyber & Dev, Career, Content
- **Style**: Quiet, direct, zero hype, high competence
"""

DEFAULT_PROJECTS_MD = """# 🚀 Active Projects & Milestones

- [[Polacraft]]: Orders, inventory, operations
- [[Canvs]]: Brand, design, collections, roadmap
- [[Screenplays]]: Beat sheets, active drafts
- [[Cyber & Dev]]: Labs, skill roadmap
- [[Career]]: Job applications, target roles
"""

DEFAULT_LESSONS_MD = """# 📚 Lessons & Learned Rules

- Evidence only, never guess.
- Full reads, no skimming.
- Checkpoint persistence: update vault notes immediately.
- Close the loop: when asking a question, stop and wait.
"""


def ensure_vault_initialized() -> Path:
    """Ensures vault directory and baseline notes exist."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        "Identity.md": DEFAULT_IDENTITY_MD,
        "Preferences.md": DEFAULT_PREFERENCES_MD,
        "Projects.md": DEFAULT_PROJECTS_MD,
        "Lessons.md": DEFAULT_LESSONS_MD,
    }

    for filename, default_content in files.items():
        file_path = VAULT_DIR / filename
        if not file_path.exists():
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(default_content.strip() + "\n")
                logger.info(f"[Vault] Initialized {filename}")
            except Exception as e:
                logger.error(f"[Vault Init Error {filename}]: {e}")

    # Scaffold templates directory if present in repo
    repo_templates = Path(config.BASE_DIR) / "vault" / "templates"
    vault_templates = VAULT_DIR / "templates"
    if repo_templates.exists() and not vault_templates.exists() and VAULT_DIR != Path(config.BASE_DIR) / "vault":
        try:
            import shutil
            shutil.copytree(repo_templates, vault_templates)
            logger.info("[Vault] Scaffolded templates into Obsidian vault.")
        except Exception as e:
            logger.debug(f"[Vault] Could not copy templates: {e}")

    return VAULT_DIR


def get_active_priorities() -> str:
    """Reads Active Priorities.md from the vault."""
    ensure_vault_initialized()
    priorities_file = VAULT_DIR / "Active Priorities.md"
    if priorities_file.exists():
        try:
            return priorities_file.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading Active Priorities: {e}"
    return "No Active Priorities.md found in vault."


def update_active_priorities(content: str) -> str:
    """Updates Active Priorities.md in the vault."""
    ensure_vault_initialized()
    priorities_file = VAULT_DIR / "Active Priorities.md"
    try:
        priorities_file.write_text(content.strip() + "\n", encoding="utf-8")
        return "Active Priorities.md updated successfully, sir."
    except Exception as e:
        return f"Failed to update Active Priorities: {e}"


def get_vault_index() -> str:
    """Reads VAULT-INDEX.md from the vault root."""
    ensure_vault_initialized()
    vindex = VAULT_DIR / "VAULT-INDEX.md"
    if vindex.exists():
        try:
            return vindex.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading VAULT-INDEX.md: {e}"
    return "VAULT-INDEX.md not found."


def log_daily_note(entry: str) -> str:
    """
    Appends a timestamped log entry to today's daily note in '01 - Daily Notes/MM - Month YYYY/YYYY-MM-DD.md'.
    """
    ensure_vault_initialized()
    now = datetime.datetime.now()
    month_folder_name = now.strftime("%m - %B %Y")
    date_file_name = now.strftime("%Y-%m-%d.md")

    daily_dir = VAULT_DIR / "01 - Daily Notes" / month_folder_name
    daily_dir.mkdir(parents=True, exist_ok=True)
    today_file = daily_dir / date_file_name

    timestamp = now.strftime("%I:%M %p")
    log_line = f"- [{timestamp}] {entry.strip()}"

    if not today_file.exists():
        template_file = VAULT_DIR / "01 - Daily Notes" / "Daily Note Template.md"
        header = f"---\nstatus: active\nproject: meta\ntype: log\ndate: {now.strftime('%Y-%m-%d')}\n---\n\n# Daily Note — {now.strftime('%A, %B %d, %Y')}\n\n## Log\n"
        if template_file.exists():
            try:
                tmpl = template_file.read_text(encoding="utf-8")
                header = tmpl.replace("{{date}}", now.strftime("%Y-%m-%d"))
            except Exception:
                pass
        today_file.write_text(header + f"\n{log_line}\n", encoding="utf-8")
    else:
        with open(today_file, "a", encoding="utf-8") as f:
            f.write(f"{log_line}\n")

    logger.info(f"[Vault Daily Note] Logged entry to {date_file_name}")
    return f"Logged to daily note ({now.strftime('%Y-%m-%d')}): \"{entry}\", sir."


def capture_inbox_item(text: str) -> str:
    """
    Captures a raw thought, idea, or task into '00 - Inbox/'.
    """
    ensure_vault_initialized()
    inbox_dir = VAULT_DIR / "00 - Inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.now()
    clean_title = re.sub(r'[^a-zA-Z0-9_\- ]+', '', text[:30]).strip().replace(' ', '_')
    if not clean_title:
        clean_title = "inbox_item"
    filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{clean_title}.md"
    target_file = inbox_dir / filename

    content = f"""---
status: idea
project: meta
type: log
captured: {now.strftime('%Y-%m-%d %H:%M:%S')}
---

# {text[:50]}

{text.strip()}
"""
    try:
        target_file.write_text(content, encoding="utf-8")
        return f"Saved thought to Inbox: `{filename}`, sir."
    except Exception as e:
        return f"Failed to save to Inbox: {e}"


def read_project_context(project_query: str) -> str:
    """
    Retrieves context for a specific project:
    Polacraft, Canvs, Screenplays, Cyber & Dev, Career, Content, Personal.
    """
    ensure_vault_initialized()
    q = project_query.lower().strip()

    mapping = {
        "polacraft": "02 - Polacraft",
        "canvs": "03 - Canvs",
        "screenplay": "04 - Screenplays",
        "screenplays": "04 - Screenplays",
        "cyber": "05 - Cyber & Dev",
        "dev": "05 - Cyber & Dev",
        "career": "06 - Career",
        "content": "07 - Content",
        "personal": "08 - Personal",
    }

    target_dir_name = None
    for k, v in mapping.items():
        if k in q:
            target_dir_name = v
            break

    if not target_dir_name:
        # Fallback to reading Projects.md or searching folder names
        for child in VAULT_DIR.iterdir():
            if child.is_dir() and q in child.name.lower():
                target_dir_name = child.name
                break

    if target_dir_name:
        p_dir = VAULT_DIR / target_dir_name
        if p_dir.exists():
            summaries = []
            for md_file in p_dir.glob("*.md"):
                try:
                    text = md_file.read_text(encoding="utf-8")
                    summaries.append(f"### {md_file.name}\n{text[:1500]}\n")
                except Exception:
                    pass
            if summaries:
                return f"## Context for {target_dir_name}:\n\n" + "\n".join(summaries)

    # Fallback to Projects.md
    return read_vault_file("Projects.md")


def sync_memory_to_vault() -> str:
    """Exports SQLite facts and user memory into vault Preferences.md."""
    ensure_vault_initialized()
    try:
        facts = user_memory.get_all_facts()
        pref_file = VAULT_DIR / "Preferences.md"
        if pref_file.exists():
            content = pref_file.read_text(encoding="utf-8")
        else:
            content = DEFAULT_PREFERENCES_MD

        added_count = 0
        for key, val in facts.items():
            fact_entry = f"- **{key}**: {val}"
            if fact_entry not in content:
                content += f"\n{fact_entry}"
                added_count += 1

        pref_file.write_text(content.strip() + "\n", encoding="utf-8")
        logger.info(f"[Vault Sync] Exported {added_count} new facts to Preferences.md")
        return f"Successfully synchronized user memory to Obsidian vault ({added_count} new entries)."
    except Exception as e:
        logger.error(f"[Vault Sync Error]: {e}")
        return f"Failed to sync memory to vault: {e}"


def sync_vault_to_memory() -> str:
    """Parses Markdown files in vault/ and imports user facts into SQLite memory."""
    ensure_vault_initialized()
    imported_count = 0
    try:
        pref_file = VAULT_DIR / "Preferences.md"
        if pref_file.exists():
            for line in pref_file.read_text(encoding="utf-8").splitlines():
                match = re.match(r"^\s*-\s*\*\*([^\*]+)\*\*:\s*(.+)$", line.strip())
                if match:
                    k, v = match.group(1).strip(), match.group(2).strip()
                    user_memory.remember(k, v)
                    imported_count += 1

        logger.info(f"[Vault Sync] Ingested {imported_count} facts from vault into SQLite.")
        return f"Successfully imported {imported_count} facts from vault into active memory."
    except Exception as e:
        logger.error(f"[Vault Import Error]: {e}")
        return f"Failed to import vault notes: {e}"


def read_vault_file(filename: str) -> str:
    """Reads the raw Markdown content of a specific vault file."""
    ensure_vault_initialized()
    safe_name = Path(filename).name
    target = VAULT_DIR / safe_name
    if not target.exists():
        # Check subdirectories
        for match in VAULT_DIR.rglob(safe_name):
            try:
                return match.read_text(encoding="utf-8")
            except Exception:
                pass
        return f"Vault file '{safe_name}' does not exist in {VAULT_DIR}."
    try:
        return target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading vault file: {e}"


def append_vault_note(category: str, note_title: str, note_body: str) -> str:
    """Appends a new note or section into the vault."""
    ensure_vault_initialized()
    cat_clean = category.strip().capitalize()
    if not cat_clean.endswith(".md"):
        cat_clean += ".md"

    target = VAULT_DIR / cat_clean
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    entry = f"\n\n### {note_title} ({timestamp})\n{note_body}\n"

    try:
        with open(target, "a", encoding="utf-8") as f:
            f.write(entry)
        user_memory.remember(f"vault_{note_title}", note_body)
        return f"Appended note '{note_title}' into vault file `{cat_clean}`, sir."
    except Exception as e:
        return f"Failed to append note to vault: {e}"
