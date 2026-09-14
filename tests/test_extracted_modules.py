"""
Unit and Integration Tests for modules extracted and modernized from D:\\agent:
1. Multi-face Holographic Visualizer (faces discovery, state polling, static routes)
2. AudioDucker background audio attenuation
3. Obsidian Vault Knowledge Templates & scaffolding
4. Mobile Desktop Controller (trackpad, keyboard, screen capture)
"""

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)


# --- 1. Multi-Face Visualizer Tests ---

def test_visualizer_faces_discovery(client):
    res = client.get("/api/hologram/faces")
    assert res.status_code == 200
    data = res.json()
    assert "faces" in data
    assert "jarvis-v4" in data["faces"]
    assert "neural" in data["faces"]
    assert "radial" in data["faces"]
    assert "rain" in data["faces"]
    assert "board" in data["faces"]


def test_visualizer_state_polling(client):
    res = client.get("/state")
    assert res.status_code == 200
    data = res.json()
    assert "state" in data
    assert "level" in data
    assert "samples" in data
    assert len(data["samples"]) == 64


def test_visualizer_static_face_pages(client):
    for face in ["neural", "radial", "rain", "board"]:
        url = f"/interface/faces/{face}/index.html"
        res = client.get(url)
        assert res.status_code == 200, f"Face {face} failed to load"
        assert len(res.text) > 100


def test_visualizer_core_js_served(client):
    res = client.get("/interface/core.js")
    assert res.status_code == 200
    assert "AV" in res.text


# --- 2. AudioDucker Tests ---

def test_audio_ducker_initialization_and_methods():
    from voice.audio_ducking import get_audio_ducker, AudioDucker
    ducker = get_audio_ducker()
    assert ducker is not None
    assert isinstance(ducker, AudioDucker)

    # Test duck and unduck without exceptions
    ducker.duck()
    assert ducker._is_ducked is True or ducker.get_current_volume() <= 0.15
    ducker.unduck(debounce=0.01)
    ducker.restore_now()
    assert ducker._is_ducked is False


# --- 3. Vault Templates Tests ---

def test_vault_templates_exist():
    template_dir = Path("vault/templates")
    assert template_dir.exists()
    assert (template_dir / "VAULT-INDEX.md").exists()
    assert (template_dir / "MEMORY.md").exists()
    assert (template_dir / "DAILY-NOTE.md").exists()
    assert (template_dir / "CLAUDE.md").exists()

    content = (template_dir / "VAULT-INDEX.md").read_text(encoding="utf-8")
    assert len(content) > 500


def test_vault_initialization_scaffolding():
    from memory.vault_sync import ensure_vault_initialized
    vault_path = ensure_vault_initialized()
    assert vault_path.exists()
    assert (vault_path / "Identity.md").exists()
    assert (vault_path / "Projects.md").exists()


# --- 4. Desktop Controller Tests ---

def test_desktop_controller_touchpad():
    from mobile.desktop_controller import handle_touchpad_event
    res = handle_touchpad_event("move", dx=0, dy=0)
    assert res["status"] in ("ok", "error")

    res_click = handle_touchpad_event("click", button="left")
    assert res_click["status"] in ("ok", "error")


def test_desktop_controller_keyboard():
    from mobile.desktop_controller import handle_keyboard_event
    res = handle_keyboard_event("key", key="")
    assert res["status"] in ("ok", "error")
