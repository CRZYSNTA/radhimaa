"""Tests for Smart TV Controller tools, router intents, and executor dispatch."""
from unittest.mock import patch, MagicMock
import pytest
from core.router import route_intent
from core.executor import ToolExecutor
from tools.tv_controller import (
    discover_smart_tvs, connect_tv, tv_remote_control,
    tv_launch_app, save_tv_config, get_tv_config
)

def test_router_tv_intents():
    # Discovery
    res_disc = route_intent("discover tv")
    assert res_disc["type"] == "SIMPLE"
    assert res_disc["tool"] == "discover_smart_tvs"

    res_access = route_intent("access tv")
    assert res_access["type"] == "SIMPLE"
    assert res_access["tool"] == "discover_smart_tvs"

    # Connect with IP
    res_conn = route_intent("connect tv 192.168.1.100")
    assert res_conn["type"] == "SIMPLE"
    assert res_conn["tool"] == "connect_tv"
    assert res_conn["params"]["ip"] == "192.168.1.100"

    # Power
    res_power = route_intent("turn on tv")
    assert res_power["type"] == "SIMPLE"
    assert res_power["tool"] == "tv_remote_control"
    assert res_power["params"]["action"] == "power"

    # Volume
    res_vol = route_intent("tv volume up")
    assert res_vol["type"] == "SIMPLE"
    assert res_vol["tool"] == "tv_remote_control"
    assert res_vol["params"]["action"] == "volume_up"

    # App Launch
    res_app = route_intent("open youtube on tv")
    assert res_app["type"] == "SIMPLE"
    assert res_app["tool"] == "tv_launch_app"
    assert res_app["params"]["app_name"] == "youtube"

    # D-pad / Key
    res_ok = route_intent("tv ok")
    assert res_ok["type"] == "SIMPLE"
    assert res_ok["tool"] == "tv_remote_control"
    assert res_ok["params"]["action"] == "select"

def test_executor_tv_tools():
    executor = ToolExecutor()
    tv_tools = [
        "discover_smart_tvs", "connect_tv", "tv_remote_control",
        "tv_launch_app", "tv_play_media", "tv_input_text"
    ]
    for t in tv_tools:
        assert t in executor.tools

def test_tv_config_and_control(tmp_path):
    test_cfg_file = tmp_path / ".tv_config.json"
    with patch("tools.tv_controller.TV_CONFIG_FILE", test_cfg_file):
        save_tv_config(ip="192.168.1.99", port=5555, tv_type="android_tv", tv_name="Test TV")
        cfg = get_tv_config()
        assert cfg.get("tv_ip") == "192.168.1.99"
        assert cfg.get("tv_type") == "android_tv"

        with patch("tools.tv_controller.subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Success"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            res = tv_remote_control("volume_up")
            assert "dispatched" in res.lower() or "sent" in res.lower()
