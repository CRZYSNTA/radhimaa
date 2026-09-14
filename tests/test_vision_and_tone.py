"""
Unit & Integration Tests for:
1. Tone & Speech Formatting Rules (format_speech_text)
2. Vision Subsystem (look & watch routing, Gemini payload formation, tool execution)
3. Gemini Provider as primary engine
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from voice.text_to_speech import format_speech_text
from core.router import route_intent
from ai.gemini_provider import GeminiProvider
from tools.controlled_tools import LookTool, WatchTool
from tools.base import ToolContext, PermissionTier


def test_tone_speech_formatter_strips_markdown():
    raw = "**Warning**: CPU load is `95%`! See [Report](https://status.internal/cpu) for details.\n* Check fans\n* Check thermals"
    formatted = format_speech_text(raw)
    
    assert "**" not in formatted
    assert "`" not in formatted
    assert "[" not in formatted
    assert "]" not in formatted
    assert "https://" not in formatted
    assert "Warning: CPU load is 95 percent! See Report for details. Check fans Check thermals" in formatted


def test_tone_speech_formatter_normalizes_times():
    raw = "The flight arrives at 08:15 and departs at 14:00."
    formatted = format_speech_text(raw)
    
    assert "08:15" not in formatted
    assert "14:00" not in formatted
    assert "eight fifteen" in formatted
    assert "fourteen hundred" in formatted


def test_vision_intent_routing_look():
    res1 = route_intent("Jarvis, look at me")
    assert res1["type"] == "SIMPLE"
    assert res1["tool"] == "look"

    res2 = route_intent("what am I holding?")
    assert res2["type"] == "SIMPLE"
    assert res2["tool"] == "look"

    res3 = route_intent("look through camera")
    assert res3["type"] == "SIMPLE"
    assert res3["tool"] == "look"


def test_vision_intent_routing_watch():
    res1 = route_intent("watch me do this pushup")
    assert res1["type"] == "SIMPLE"
    assert res1["tool"] == "watch"
    assert res1["params"]["seconds"] == 4

    res2 = route_intent("watch my form for 6 seconds")
    assert res2["type"] == "SIMPLE"
    assert res2["tool"] == "watch"
    assert res2["params"]["seconds"] == 6


def test_gemini_provider_models_and_availability():
    provider = GeminiProvider()
    assert "gemini-2.5-flash" in provider.MODELS
    assert "gemini-2.0-flash" in provider.MODELS
    assert "gemini-1.5-flash" in provider.MODELS
    assert provider.name == "gemini"


def test_gemini_analyze_frames_payload_generation():
    provider = GeminiProvider(api_key="test_api_key_mock")
    fake_frames = [
        (b"fake_jpeg_1", 0.0),
        (b"fake_jpeg_2", 1.0)
    ]
    
    with patch.object(provider, "_post_contents", return_value="The subject raised their right hand.") as mock_post:
        result = provider.analyze_frames(fake_frames, prompt="Evaluate the movement.")
        assert result == "The subject raised their right hand."
        assert mock_post.called
        call_args = mock_post.call_args[0]
        parts = call_args[0]
        # Should have text prompt + frame 1 label + frame 1 inline_data + frame 2 label + frame 2 inline_data
        assert len(parts) == 5
        assert "Frame 1 (+0.0s):" in parts[1]["text"]
        assert "inline_data" in parts[2]
        assert "Frame 2 (+1.0s):" in parts[3]["text"]
        assert "inline_data" in parts[4]


@pytest.mark.asyncio
async def test_look_tool_execution():
    tool = LookTool()
    assert tool.name == "look"
    assert tool.permission == PermissionTier.SAFE

    ctx = ToolContext(session_id="s1", user_id="u1", correlation_id="c1")
    
    with patch("vision.camera.look", return_value="You are holding a blue notebook, sir."):
        res = await tool.execute(ctx, {"prompt": "What am I holding?"})
        assert res.success is True
        assert "blue notebook" in res.output


@pytest.mark.asyncio
async def test_watch_tool_execution():
    tool = WatchTool()
    assert tool.name == "watch"
    assert tool.permission == PermissionTier.SAFE

    ctx = ToolContext(session_id="s1", user_id="u1", correlation_id="c1")
    
    with patch("vision.camera.watch", return_value="The form improved significantly on the second repetition, sir."):
        res = await tool.execute(ctx, {"seconds": 3, "prompt": "Watch my form."})
        assert res.success is True
        assert "repetition" in res.output
