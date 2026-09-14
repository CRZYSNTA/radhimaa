"""
JARVIS V3.0 - Automated Test Suite for Integrated Automation Tools
Tests office generation, website builder, file processor, settings,
productivity, media controls, permissions, and tool execution.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from core.permissions import check_permission, PermissionLevel, TOOL_PERMISSIONS
from core.tools_registry import TOOLS_REGISTRY
from core.executor import ToolExecutor

@pytest.fixture
def temp_workspace():
    tmp = tempfile.mkdtemp(prefix="jarvis_test_ws_")
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)

def test_office_tools(temp_workspace):
    from tools.office import (
        create_presentation, create_spreadsheet,
        create_word_document, create_pdf_document
    )

    # 1. Presentation
    ppt_out = temp_workspace / "test_deck.pptx"
    slides = [{"title": "Intro", "bullets": ["First point", "Second point"]}]
    res_ppt = create_presentation("Test Presentation", slides, output_path=str(ppt_out))
    assert "generated" in res_ppt.lower() or "saved" in res_ppt.lower()
    # Check either .pptx or fallback .md exists
    assert ppt_out.exists() or ppt_out.with_suffix(".md").exists()

    # 2. Spreadsheet
    sheet_out = temp_workspace / "test_sheet.xlsx"
    data = [["Item", "Quantity", "Price"], ["Apple", 5, 1.20], ["Banana", 10, 0.80]]
    res_sheet = create_spreadsheet("Test Sheet", data, output_path=str(sheet_out))
    assert "generated" in res_sheet.lower() or "saved" in res_sheet.lower()
    assert sheet_out.exists() or sheet_out.with_suffix(".csv").exists()

    # 3. Word Document
    doc_out = temp_workspace / "test_doc.docx"
    content = [{"heading": "Section 1", "text": "This is a test paragraph for JARVIS."}]
    res_doc = create_word_document("Test Document", content, output_path=str(doc_out))
    assert "generated" in res_doc.lower() or "saved" in res_doc.lower()
    assert doc_out.exists() or doc_out.with_suffix(".txt").exists()

    # 4. PDF Document
    pdf_out = temp_workspace / "test_doc.pdf"
    res_pdf = create_pdf_document("Test PDF", content, output_path=str(pdf_out))
    assert "generated" in res_pdf.lower() or "printable" in res_pdf.lower()
    assert pdf_out.exists() or pdf_out.with_suffix(".html").exists()

def test_web_builder(temp_workspace):
    from tools.web_builder import build_website
    site_dir = temp_workspace / "MyStartup"
    res = build_website("My Startup", template_style="dark_tech", output_dir=str(site_dir))
    assert "successfully built" in res.lower()
    assert (site_dir / "index.html").exists()
    assert (site_dir / "style.css").exists()
    assert (site_dir / "script.js").exists()

    with open(site_dir / "index.html", "r", encoding="utf-8") as f:
        html = f.read()
        assert "My Startup" in html
        assert "JARVIS AI Assistant" in html

def test_file_processor(temp_workspace):
    from tools.file_processor import (
        organize_directory, find_large_files,
        compress_files, extract_archive
    )

    # Create dummy files
    f_img = temp_workspace / "photo.png"
    f_img.write_text("dummy image data")
    f_doc = temp_workspace / "notes.txt"
    f_doc.write_text("dummy document text")

    # Organize
    res_org = organize_directory(str(temp_workspace))
    assert "organized" in res_org.lower()
    assert (temp_workspace / "Images" / "photo.png").exists()
    assert (temp_workspace / "Documents" / "notes.txt").exists()

    # Find large files
    res_find = find_large_files(str(temp_workspace), min_mb=0.00001)
    assert "found" in res_find.lower()

    # Compress
    res_zip = compress_files(str(temp_workspace / "Documents"), zip_name="test_archive")
    assert "successfully created" in res_zip.lower()
    zip_file = temp_workspace / "test_archive.zip"
    assert zip_file.exists()

    # Extract
    ext_dir = temp_workspace / "extracted"
    res_ext = extract_archive(str(zip_file), target_dir=str(ext_dir))
    assert "successfully extracted" in res_ext.lower()
    assert (ext_dir / "Documents" / "notes.txt").exists() or (ext_dir / "notes.txt").exists()

def test_productivity_tools():
    from tools.productivity import (
        set_reminder, get_active_reminders,
        cancel_reminder, daily_briefing, analyze_clipboard
    )

    # Reminders
    res_rem = set_reminder("Test unit reminder", delay_minutes=60.0)
    assert "reminder set" in res_rem.lower()

    active_rems = get_active_reminders()
    assert "Test unit reminder" in active_rems

    res_cancel = cancel_reminder("Test unit reminder")
    assert "cancelled" in res_cancel.lower()

    # Daily briefing
    briefing = daily_briefing()
    assert len(briefing) > 30
    assert "Today is" in briefing or "Good" in briefing

    # Analyze clipboard
    clip_analysis = analyze_clipboard()
    assert isinstance(clip_analysis, str)

def test_settings_and_media():
    from tools.computer_settings import get_system_settings
    from tools.media_controller import spotify_control
    from tools.dev_tools import git_quick_status

    # Settings
    settings = get_system_settings()
    assert isinstance(settings, dict)

    # Spotify control
    res_spot = spotify_control(action="toggle")
    assert "playback" in res_spot.lower() or "sent" in res_spot.lower()

    # Git status
    git_status = git_quick_status(".")
    assert "Git Repository" in git_status or "not a Git repository" in git_status

def test_new_tools_permissions():
    new_tools = [
        "create_presentation", "create_spreadsheet", "create_word_document", "create_pdf_document",
        "build_website", "set_brightness", "toggle_dark_mode", "toggle_wifi", "toggle_bluetooth",
        "get_system_settings", "organize_directory", "find_large_files", "clean_temp_files",
        "compress_files", "extract_archive", "spotify_control", "get_youtube_transcript_and_summary",
        "set_reminder", "get_active_reminders", "cancel_reminder", "daily_briefing", "analyze_clipboard",
        "send_whatsapp_message", "check_instagram_dms", "reply_instagram_dm", "analyze_meal_nutrition",
        "count_exercise_reps", "discover_smart_devices", "control_smart_plug", "control_smart_bulb",
        "git_quick_status", "explain_code_snippet",
        "pair_mobile", "list_paired_devices", "revoke_mobile_device"
    ]
    for tool in new_tools:
        level, _ = check_permission(tool, {})
        assert level in (PermissionLevel.SAFE, PermissionLevel.CONFIRM), f"Tool {tool} has invalid permission {level}"
        assert tool in TOOL_PERMISSIONS, f"Tool {tool} missing in TOOL_PERMISSIONS"
        assert tool in TOOLS_REGISTRY, f"Tool {tool} missing in TOOLS_REGISTRY"

def test_tool_executor_execution():
    executor = ToolExecutor()
    assert "daily_briefing" in executor.tools
    assert "build_website" in executor.tools
    assert "create_presentation" in executor.tools
    assert "clean_temp_files" in executor.tools

    # Test safe execution
    res = executor.execute_step("daily_briefing", {})
    assert res.success
    assert len(res.output) > 20
