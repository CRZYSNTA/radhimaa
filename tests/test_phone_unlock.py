"""Tests for phone unlocking and wireless phone control tools."""
from unittest.mock import patch, MagicMock
import pytest
from core.router import route_intent
from core.executor import ToolExecutor
from tools.phone_controller import (
    unlock_phone, lock_phone, get_adb_path,
    save_phone_config, get_phone_config,
    connect_wireless_phone, setup_wireless_adb
)

def test_router_unlock_phone():
    # Simple unlock without pin
    res = route_intent("unlock my phone")
    assert res["type"] == "SIMPLE"
    assert res["tool"] == "unlock_phone"
    assert not res["params"].get("pin")
    
    # Unlock with PIN
    res_pin = route_intent("unlock phone with pin 1234")
    assert res_pin["type"] == "SIMPLE"
    assert res_pin["tool"] == "unlock_phone"
    assert res_pin["params"].get("pin") == "1234"

    # Unlock wirelessly
    res_wire = route_intent("unlock it wirelessly")
    assert res_wire["type"] == "SIMPLE"
    assert res_wire["tool"] == "unlock_phone"

    # Setup wireless
    res_setup = route_intent("setup wireless phone")
    assert res_setup["type"] == "SIMPLE"
    assert res_setup["tool"] == "setup_wireless_phone"

    # Connect wireless with IP
    res_conn = route_intent("connect wireless phone 192.168.1.55")
    assert res_conn["type"] == "SIMPLE"
    assert res_conn["tool"] == "connect_wireless_phone"
    assert res_conn["params"]["ip"] == "192.168.1.55"

    # Lock phone
    res_lock = route_intent("lock phone")
    assert res_lock["type"] == "SIMPLE"
    assert res_lock["tool"] == "lock_phone"

def test_executor_phone_tools():
    executor = ToolExecutor()
    assert "unlock_phone" in executor.tools
    assert "lock_phone" in executor.tools
    assert "setup_wireless_phone" in executor.tools
    assert "connect_wireless_phone" in executor.tools

    with patch("tools.phone_controller.subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "List of devices attached\nemulator-5554\tdevice\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result = executor.execute_step("unlock_phone", {"pin": "5678"})
        assert result.success is True
        assert "dismissed" in result.output.lower()

        res_lock = executor.execute_step("lock_phone", {})
        assert res_lock.success is True
        assert "locked" in res_lock.output.lower()

def test_phone_config_and_wireless_connection(tmp_path):
    with patch("tools.phone_controller.subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "connected to 192.168.1.100:5555"
        mock_run.return_value = mock_proc

        res = connect_wireless_phone("192.168.1.100", 5555)
        assert "successfully connected" in res.lower()

        cfg = get_phone_config()
        assert cfg.get("wireless_ip") == "192.168.1.100"
