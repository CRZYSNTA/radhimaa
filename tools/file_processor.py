"""
JARVIS V3.0 - Advanced File Processor & Directory Organizer
Automates folder organization, space reclamation, archive handling,
and safe temporary file purging within authorized paths.
"""

from __future__ import annotations

import os
import shutil
import zipfile
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JARVIS.Tools.FileProcessor")

CATEGORY_EXTENSIONS: Dict[str, List[str]] = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".csv", ".md"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
    "Video": [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".cs", ".json", ".ts", ".go"],
    "Installers": [".exe", ".msi", ".iso", ".bat", ".cmd", ".ps1"]
}

def organize_directory(path: str = "~/Downloads") -> str:
    """
    Categorizes and moves files in a target directory into organized subfolders
    (Images, Documents, Audio, Video, Archives, Code, Installers).
    """
    target = Path(path).expanduser().resolve()
    if not target.exists() or not target.is_dir():
        return f"Error: Directory '{path}' does not exist or is not a directory."

    moved_count = 0
    categories_used = set()

    for item in list(target.iterdir()):
        if item.is_file() and not item.name.startswith("."):
            ext = item.suffix.lower()
            placed = False
            for cat, exts in CATEGORY_EXTENSIONS.items():
                if ext in exts:
                    cat_dir = target / cat
                    cat_dir.mkdir(exist_ok=True)
                    dest_file = cat_dir / item.name
                    # Handle duplicate names gracefully
                    if dest_file.exists():
                        dest_file = cat_dir / f"{item.stem}_copy{item.suffix}"
                    try:
                        shutil.move(str(item), str(dest_file))
                        moved_count += 1
                        categories_used.add(cat)
                        placed = True
                        break
                    except Exception as e:
                        logger.warning(f"[FileProcessor] Failed to move {item.name}: {e}")
            
            if not placed and ext:
                other_dir = target / "Miscellaneous"
                other_dir.mkdir(exist_ok=True)
                try:
                    shutil.move(str(item), str(other_dir / item.name))
                    moved_count += 1
                    categories_used.add("Miscellaneous")
                except Exception:
                    pass

    logger.info(f"[FileProcessor] Organized {moved_count} files in {target}")
    return f"Successfully organized {moved_count} files across categories: {', '.join(sorted(categories_used))}."

def find_large_files(path: str = "~", min_mb: float = 100.0) -> str:
    """
    Scans a folder for files larger than a specified size in megabytes.
    """
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return f"Error: Directory '{path}' does not exist."

    min_bytes = int(min_mb * 1024 * 1024)
    large_files: List[Dict[str, Any]] = []

    try:
        for root, _, files in os.walk(target):
            for file in files:
                try:
                    fpath = Path(root) / file
                    if fpath.is_symlink():
                        continue
                    size = fpath.stat().st_size
                    if size >= min_bytes:
                        size_mb = round(size / (1024 * 1024), 2)
                        large_files.append({"path": str(fpath), "size_mb": size_mb})
                except Exception:
                    continue
    except Exception as e:
        logger.error(f"[FileProcessor Scan Error]: {e}")

    large_files.sort(key=lambda x: x["size_mb"], reverse=True)
    top_results = large_files[:15]

    if not top_results:
        return f"No files larger than {min_mb} MB found in {path}."

    lines = [f"Found {len(large_files)} large files (showing top {len(top_results)}):"]
    for f in top_results:
        lines.append(f"- {f['size_mb']} MB: {f['path']}")
    return "\n".join(lines)

def clean_temp_files() -> str:
    """
    Safely purges unneeded files from Windows %TEMP% to reclaim disk space.
    """
    temp_dir = Path(tempfile.gettempdir())
    deleted_count = 0
    bytes_freed = 0

    for item in temp_dir.iterdir():
        try:
            if item.is_file():
                size = item.stat().st_size
                item.unlink(missing_ok=True)
                deleted_count += 1
                bytes_freed += size
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                deleted_count += 1
        except Exception:
            # Skip in-use locked files
            continue

    freed_mb = round(bytes_freed / (1024 * 1024), 2)
    logger.info(f"[FileProcessor] Cleaned {deleted_count} items ({freed_mb} MB) from temp")
    return f"Temporary cleanup complete: purged {deleted_count} items, freeing approximately {freed_mb} MB of space, sir."

def compress_files(source_path: str, zip_name: Optional[str] = None) -> str:
    """
    Compresses a file or directory into a ZIP archive.
    """
    src = Path(source_path).expanduser().resolve()
    if not src.exists():
        return f"Error: Source path '{source_path}' does not exist."

    dest_zip = src.parent / f"{zip_name or src.stem}.zip"

    try:
        with zipfile.ZipFile(dest_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            if src.is_file():
                zf.write(src, arcname=src.name)
            else:
                for root, _, files in os.walk(src):
                    for file in files:
                        full_p = Path(root) / file
                        rel_p = full_p.relative_to(src.parent)
                        zf.write(full_p, arcname=str(rel_p))

        return f"Successfully created archive at: {dest_zip}"
    except Exception as e:
        logger.error(f"[FileProcessor Zip Error]: {e}")
        return f"Failed to compress files: {e}"

def extract_archive(zip_path: str, target_dir: Optional[str] = None) -> str:
    """
    Extracts a ZIP archive into a destination directory.
    """
    zpath = Path(zip_path).expanduser().resolve()
    if not zpath.exists() or not zipfile.is_zipfile(zpath):
        return f"Error: '{zip_path}' is not a valid ZIP file."

    dest = Path(target_dir).expanduser().resolve() if target_dir else zpath.parent / zpath.stem
    dest.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zpath, 'r') as zf:
            zf.extractall(dest)
        return f"Successfully extracted archive to: {dest}"
    except Exception as e:
        logger.error(f"[FileProcessor Unzip Error]: {e}")
        return f"Failed to extract archive: {e}"
