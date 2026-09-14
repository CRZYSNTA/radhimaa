"""
JARVIS V4 - Android Phone Control & Wireless Unlock Tool
Controls connected Android devices via ADB (USB or Wireless Wi-Fi).
Supports:
1. Wireless ADB setup and automatic IP discovery
2. Seamless auto-reconnect over Wi-Fi
3. Waking display, swiping to unlock, and automated PIN typing
4. Screen locking
"""

from __future__ import annotations

import os
import re
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger("JARVIS.Tools.Phone")

PHONE_CONFIG_FILE = Path(__file__).resolve().parent.parent / ".phone_config.json"


def get_phone_config() -> Dict[str, Any]:
    """Loads saved phone connection settings."""
    if PHONE_CONFIG_FILE.exists():
        try:
            return json.loads(PHONE_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_phone_config(
    ip: Optional[str] = None,
    port: Optional[int] = None,
    default_pin: Optional[str] = None,
) -> Dict[str, Any]:
    """Saves phone connection settings for auto-reconnect."""
    cfg = get_phone_config()
    if ip:
        cfg["wireless_ip"] = ip.strip()
    if port:
        cfg["wireless_port"] = int(port)
    if default_pin is not None:
        cfg["default_pin"] = default_pin.strip()
    try:
        PHONE_CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not save phone config: {e}")
    return cfg


def get_adb_path() -> Optional[str]:
    """Finds adb.exe in PATH or standard Android SDK locations."""
    which_adb = shutil.which("adb")
    if which_adb and os.path.exists(which_adb):
        return which_adb

    local_sdk = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")
    if os.path.exists(local_sdk):
        return local_sdk

    return None


def get_connected_devices() -> List[str]:
    """Returns list of connected ADB device serials/endpoints."""
    adb = get_adb_path()
    if not adb:
        return []

    try:
        res = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=5)
        lines = res.stdout.strip().splitlines()[1:]
        devices = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices
    except Exception:
        return []


def get_device_wifi_ip(device_id: Optional[str] = None) -> Optional[str]:
    """Retrieves the local Wi-Fi IP address of the connected phone."""
    adb = get_adb_path()
    if not adb:
        return None

    cmd_prefix = [adb]
    if device_id:
        cmd_prefix.extend(["-s", device_id])

    # Method 1: ip -f inet addr show wlan0
    try:
        res = subprocess.run(
            cmd_prefix + ["shell", "ip", "-f", "inet", "addr", "show", "wlan0"],
            capture_output=True, text=True, timeout=5
        )
        match = re.search(r'inet\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', res.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass

    # Method 2: ip route
    try:
        res = subprocess.run(
            cmd_prefix + ["shell", "ip", "route"],
            capture_output=True, text=True, timeout=5
        )
        match = re.search(r'src\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', res.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass

    # Method 3: getprop dhcp.wlan0.ipaddress
    try:
        res = subprocess.run(
            cmd_prefix + ["shell", "getprop", "dhcp.wlan0.ipaddress"],
            capture_output=True, text=True, timeout=5
        )
        ip = res.stdout.strip()
        if ip and re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$', ip):
            return ip
    except Exception:
        pass

    return None


def connect_wireless_phone(ip: str, port: int = 5555) -> str:
    """Connects to a phone wirelessly over TCP/IP ADB."""
    adb = get_adb_path()
    if not adb:
        return "Android platform-tools (ADB) not found on PC."

    clean_ip = ip.strip()
    endpoint = f"{clean_ip}:{port}"
    try:
        res = subprocess.run([adb, "connect", endpoint], capture_output=True, text=True, timeout=8)
        out = res.stdout.strip()
        if "connected to" in out.lower() or "already connected" in out.lower():
            save_phone_config(ip=clean_ip, port=port)
            logger.info(f"[Phone] Wirelessly connected to {endpoint}")
            return f"Successfully connected wirelessly to phone at {endpoint}, sir."
        return f"Could not connect wirelessly to {endpoint}. ADB output: {out}"
    except Exception as e:
        logger.error(f"[Phone Wireless Connect Error]: {e}")
        return f"Wireless connection error: {e}"


def pair_wireless_phone(ip: str, port: int, pairing_code: str) -> str:
    """Pairs phone with Android 11+ Wireless Debugging pairing code."""
    adb = get_adb_path()
    if not adb:
        return "ADB not found."

    endpoint = f"{ip.strip()}:{port}"
    try:
        res = subprocess.run(
            [adb, "pair", endpoint, str(pairing_code).strip()],
            capture_output=True, text=True, timeout=10
        )
        out = res.stdout.strip()
        if "successfully paired" in out.lower():
            return f"Successfully paired with phone at {endpoint}! You can now connect."
        return f"Pairing response: {out}"
    except Exception as e:
        return f"Pairing failed: {e}"


def setup_wireless_adb() -> str:
    """
    1-Click USB to Wireless setup:
    Switches USB-connected phone to port 5555, auto-detects its Wi-Fi IP, connects wirelessly, and saves config.
    After this executes, user can unplug USB!
    """
    adb = get_adb_path()
    if not adb:
        return "Android platform-tools (ADB) not found."

    devices = get_connected_devices()
    if not devices:
        return (
            "No Android phone detected to initialize wireless ADB. "
            "Please plug in your phone via USB cable once and enable USB Debugging."
        )

    device_id = devices[0]
    phone_ip = get_device_wifi_ip(device_id)

    # Enable TCP/IP on port 5555
    res_tcpip = subprocess.run(
        [adb, "-s", device_id, "tcpip", "5555"],
        capture_output=True, text=True, timeout=6
    )

    if phone_ip:
        conn_res = connect_wireless_phone(phone_ip, 5555)
        return (
            f"Wireless ADB successfully initialized!\n"
            f"Phone Wi-Fi IP: {phone_ip}:5555\n"
            f"Status: {conn_res}\n"
            f"You can now UNPLUG the USB cable, sir. JARVIS will unlock and control your phone wirelessly."
        )
    else:
        return (
            "Switched ADB to TCP/IP mode on port 5555, but could not auto-detect phone IP. "
            "Check your phone's Wi-Fi IP in Settings > About Phone > Status, and connect via: "
            "'connect wireless phone <ip>'."
        )

# Alias for tool consistency
setup_wireless_phone = setup_wireless_adb


def auto_reconnect_wireless() -> bool:
    """Attempts automatic reconnection using saved wireless IP if no device is active."""
    devices = get_connected_devices()
    if devices:
        return True

    cfg = get_phone_config()
    saved_ip = cfg.get("wireless_ip")
    saved_port = cfg.get("wireless_port", 5555)

    if saved_ip:
        adb = get_adb_path()
        if adb:
            try:
                subprocess.run(
                    [adb, "connect", f"{saved_ip}:{saved_port}"],
                    capture_output=True, text=True, timeout=5
                )
                devices = get_connected_devices()
                if devices:
                    logger.info(f"[Phone] Reconnected wirelessly to {saved_ip}:{saved_port}")
                    return True
            except Exception:
                pass
    return False


def unlock_phone(pin: Optional[str] = None) -> str:
    """
    Unlocks phone wirelessly or via USB:
    1. Ensures phone is connected (attempts wireless auto-reconnect if needed)
    2. Sends KEYCODE_WAKEUP (224) to turn on display
    3. Sends KEYCODE_MENU (82) and swipe gesture to dismiss lock screen
    4. If PIN is provided (or configured), inputs numeric PIN and sends KEYCODE_ENTER (66)
    """
    adb = get_adb_path()
    if not adb:
        return "Android platform-tools (ADB) not found on PC. Please install Android SDK or platform-tools."

    # Try wireless auto-reconnect if not already connected
    auto_reconnect_wireless()

    devices = get_connected_devices()
    if not devices:
        cfg = get_phone_config()
        saved_ip = cfg.get("wireless_ip")
        if saved_ip:
            return (
                f"Phone is not reachable at saved wireless IP {saved_ip}. "
                "Ensure your phone and PC are on the same Wi-Fi network, or run 'setup wireless phone'."
            )
        return (
            "No Android phone connected, sir. "
            "To unlock wirelessly: run 'setup_wireless_phone.bat' or plug in your phone once to enable wireless ADB."
        )

    device_id = devices[0]
    try:
        # 1. Wake up screen
        subprocess.run([adb, "-s", device_id, "shell", "input", "keyevent", "224"], capture_output=True, timeout=5)

        # 2. Dismiss swipe keyguard
        subprocess.run([adb, "-s", device_id, "shell", "input", "keyevent", "82"], capture_output=True, timeout=5)
        # Swipe up gesture in case keyevent 82 is ignored by OEM keyguard
        subprocess.run([adb, "-s", device_id, "shell", "input", "swipe", "500", "1600", "500", "400", "200"], capture_output=True, timeout=5)

        # 3. Determine PIN
        actual_pin = pin if (pin and str(pin).strip()) else get_phone_config().get("default_pin")

        if actual_pin and str(actual_pin).strip():
            clean_pin = str(actual_pin).strip()
            subprocess.run([adb, "-s", device_id, "shell", "input", "text", clean_pin], capture_output=True, timeout=5)
            subprocess.run([adb, "-s", device_id, "shell", "input", "keyevent", "66"], capture_output=True, timeout=5)
            logger.info(f"[Phone] Unlock sequence with PIN dispatched to {device_id}.")
            return f"Phone awakened, lock screen dismissed, and PIN entered successfully on {device_id}, sir."

        logger.info(f"[Phone] Wake and swipe unlock sequence dispatched to {device_id}.")
        return f"Phone awakened and swipe unlock sequence dispatched successfully on {device_id}, sir."
    except Exception as e:
        logger.error(f"[Phone Unlock Error]: {e}")
        return f"Unable to unlock phone: {e}"


def lock_phone() -> str:
    """Turns off phone screen / locks keyguard wirelessly or via USB."""
    adb = get_adb_path()
    if not adb:
        return "ADB not found."

    auto_reconnect_wireless()
    devices = get_connected_devices()
    if not devices:
        return "No Android device detected."

    subprocess.run([adb, "-s", devices[0], "shell", "input", "keyevent", "26"], capture_output=True, timeout=5)
    return "Phone locked and display turned off, sir."
