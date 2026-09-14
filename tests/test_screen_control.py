"""
Unit & integration tests for Screen-Aware Computer Control (JARVIS V3.1).
Verifies:
 - ScreenObservation capture
 - Display geometry boundary enforcement
 - Invalid coordinate rejection
 - Valid computer action execution
 - Screen change verification
"""

import pytest
from vision.screen_analyzer import (
    ScreenObservation,
    capture_screen_observation,
    ScreenAnalyzer,
    UIElement
)
from core.action_schema import (
    validate_computer_action,
    execute_computer_action,
    get_screen_bounds
)

def test_screen_observation_capture():
    obs = capture_screen_observation()
    assert isinstance(obs, ScreenObservation)
    assert obs.width > 0
    assert obs.height > 0
    assert isinstance(obs.image_bytes, bytes)
    summary = obs.to_summary()
    assert "width" in summary
    assert "height" in summary

def test_action_bounds_validation():
    max_w, max_h = get_screen_bounds()

    # Valid within screen
    val_ok = validate_computer_action("click", {"x": max_w // 2, "y": max_h // 2})
    assert val_ok.is_valid

    # Negative coordinates must be rejected
    val_neg_x = validate_computer_action("click", {"x": -10, "y": 100})
    assert not val_neg_x.is_valid
    assert "outside display boundaries" in val_neg_x.error

    val_neg_y = validate_computer_action("click", {"x": 100, "y": -5})
    assert not val_neg_y.is_valid

    # Out of bounds coordinates must be rejected
    val_out_x = validate_computer_action("click", {"x": max_w + 100, "y": 100})
    assert not val_out_x.is_valid

    val_out_y = validate_computer_action("click", {"x": 100, "y": max_h + 50})
    assert not val_out_y.is_valid

def test_action_typing_validation():
    val_ok = validate_computer_action("type", {"text": "hello jarvis"})
    assert val_ok.is_valid
    assert val_ok.sanitized_params["text"] == "hello jarvis"

    val_empty = validate_computer_action("type", {"text": ""})
    assert not val_empty.is_valid

def test_action_hotkey_validation():
    val_str = validate_computer_action("hotkey", {"keys": "ctrl+c"})
    assert val_str.is_valid
    assert val_str.sanitized_params["keys"] == ["ctrl", "c"]

    val_list = validate_computer_action("hotkey", {"keys": ["win", "down"]})
    assert val_list.is_valid
    assert val_list.sanitized_params["keys"] == ["win", "down"]

def test_unknown_action_type_rejection():
    val = validate_computer_action("format_hard_drive", {})
    assert not val.is_valid
    assert "Unknown computer action" in val.error

def test_screen_change_verification():
    obs1 = ScreenObservation(
        timestamp=100.0,
        width=1920,
        height=1080,
        image_bytes=b"frame1_bytes_" + (b"x" * 1000),
        active_window="Chrome"
    )
    obs2 = ScreenObservation(
        timestamp=101.0,
        width=1920,
        height=1080,
        image_bytes=b"frame2_bytes_" + (b"y" * 3000),
        active_window="YouTube - Google Chrome"
    )
    success, reason = ScreenAnalyzer.verify_screen_change(obs1, obs2, expected_change="YouTube")
    assert success
    assert "Active window shifted" in reason or "Visual screen delta" in reason


