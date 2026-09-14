"""
JARVIS V3.0 - Mobile Bridge Subsystem
Provides secure mobile pairing, remote trackpad/keyboard control, live screen mirror,
real-time hardware telemetry, and direct mobile-to-agent task execution.
"""

from __future__ import annotations

import io
import os
import sys
import time
import socket
import secrets
import asyncio
import random
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from PIL import Image

import psutil
import tempfile
import config
from memory.database import register_paired_device, validate_device_token, get_paired_devices, revoke_device
import database

logger = logging.getLogger("JARVIS.MobileBridge")

# Cross-process pairing session file in system temp
PAIRING_SESSION_FILE = Path(tempfile.gettempdir()) / "jarvis_active_pairing.json"

# In-memory pairing session state cache
_active_pairing_session: Dict[str, Any] = {
    "pin": None,
    "expires_at": 0.0,
    "created_at": 0.0
}

def _load_stored_pairing_session() -> Dict[str, Any]:
    """Loads active pairing session across processes (memory + temp file)."""
    now = time.time()
    if _active_pairing_session.get("pin") and now < _active_pairing_session.get("expires_at", 0.0):
        return _active_pairing_session

    if PAIRING_SESSION_FILE.exists():
        try:
            data = json.loads(PAIRING_SESSION_FILE.read_text(encoding="utf-8"))
            if data.get("pin") and now < data.get("expires_at", 0.0):
                _active_pairing_session.update(data)
                return data
        except Exception:
            pass

    return {"pin": None, "expires_at": 0.0, "created_at": 0.0}

def _save_stored_pairing_session(pin: str, created_at: float, expires_at: float):
    """Persists active pairing session across processes."""
    data = {"pin": str(pin).strip(), "created_at": created_at, "expires_at": expires_at}
    _active_pairing_session.update(data)
    try:
        PAIRING_SESSION_FILE.write_text(json.dumps(data), encoding="utf-8")
    except Exception as e:
        logger.debug(f"Could not persist pairing session file: {e}")

def _clear_stored_pairing_session():
    """Clears active pairing session from memory and disk."""
    _active_pairing_session["pin"] = None
    if PAIRING_SESSION_FILE.exists():
        try:
            PAIRING_SESSION_FILE.unlink(missing_ok=True)
        except Exception:
            pass


def get_network_ips() -> List[Dict[str, str]]:
    """Discovers host network interface IPs (Wi-Fi, Ethernet, Tailscale/VPN)."""
    ip_list = []
    # 1. Primary outbound socket detection
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Dummy connect to public DNS to find default outgoing interface
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and not primary_ip.startswith("127."):
            ip_list.append({"ip": primary_ip, "type": "Primary LAN"})
    except Exception:
        pass

    # 2. psutil interface scan
    try:
        addrs = psutil.net_if_addrs()
        for iface, addr_list in addrs.items():
            iface_lower = iface.lower()
            if "loopback" in iface_lower or "pseudo" in iface_lower:
                continue
            for a in addr_list:
                if a.family == socket.AF_INET and not a.address.startswith("127.") and not a.address.startswith("169.254."):
                    kind = "Wi-Fi" if "wi-fi" in iface_lower or "wlan" in iface_lower else (
                        "Tailscale" if "tailscale" in iface_lower else (
                            "Ethernet" if "ethernet" in iface_lower else "Network"
                        )
                    )
                    if not any(entry["ip"] == a.address for entry in ip_list):
                        ip_list.append({"ip": a.address, "type": f"{kind} ({iface})"})
    except Exception as e:
        logger.warning(f"Error scanning network interfaces: {e}")

    if not ip_list:
        ip_list.append({"ip": "127.0.0.1", "type": "Localhost"})
    return ip_list

def generate_pairing_session(ttl_seconds: int = 600) -> Dict[str, Any]:
    """
    Generates a fresh 6-digit pairing PIN with a 10-minute expiry time.
    Returns session details with URLs for local network connection.
    """
    pin = f"{random.randint(100000, 999999)}"
    now = time.time()
    expires_at = now + ttl_seconds
    _save_stored_pairing_session(pin, now, expires_at)

    ips = get_network_ips()
    primary_ip = ips[0]["ip"] if ips else "127.0.0.1"
    
    # Priority for Wi-Fi or standard 192.168 / 10.x LAN
    for item in ips:
        if "wi-fi" in item["type"].lower() or item["ip"].startswith("192.168."):
            primary_ip = item["ip"]
            break

    url = f"http://{primary_ip}:8000/app?pin={pin}"

    return {
        "pin": pin,
        "expires_at": expires_at,
        "ttl_remaining": int(ttl_seconds),
        "url": url,
        "primary_ip": primary_ip,
        "interfaces": ips
    }

def get_current_pairing_status() -> Dict[str, Any]:
    """Returns the current active pairing PIN if still valid."""
    session = _load_stored_pairing_session()
    now = time.time()
    pin = session.get("pin")
    expires_at = session.get("expires_at", 0.0)
    if pin and now < expires_at:
        ips = get_network_ips()
        primary_ip = ips[0]["ip"] if ips else "127.0.0.1"
        for item in ips:
            if "wi-fi" in item["type"].lower() or item["ip"].startswith("192.168."):
                primary_ip = item["ip"]
                break
        return {
            "active": True,
            "pin": pin,
            "expires_at": expires_at,
            "ttl_remaining": int(expires_at - now),
            "url": f"http://{primary_ip}:8000/app?pin={pin}",
            "primary_ip": primary_ip,
            "interfaces": ips
        }
    return {"active": False, "pin": None, "ttl_remaining": 0}

def verify_pairing_pin(pin: str, device_name: str = "Mobile Device") -> Optional[Dict[str, Any]]:
    """
    Validates a submitted PIN. If valid, generates a permanent device token,
    registers it in SQLite database, and invalidates the single-use PIN.
    Supports master auth token as an emergency or zero-config pairing key.
    """
    clean_pin = str(pin).strip()
    if not clean_pin:
        return None

    # 1. Master Auth Token check (e.g. naanthaandaleo)
    master_token = getattr(config, "AUTH_TOKEN", "") or os.environ.get("JARVIS_AUTH_TOKEN", "") or os.environ.get("AUTH_TOKEN", "")
    if master_token and clean_pin == master_token.strip():
        token = secrets.token_urlsafe(32)
        device_id = f"dev_{secrets.token_hex(4)}"
        reg = register_paired_device(device_id, device_name, token)
        logger.info(f"Successfully paired mobile device '{device_name}' via master auth token.")
        return {
            "success": True,
            "device_id": device_id,
            "device_name": device_name,
            "auth_token": token,
            "paired_at": reg["paired_at"]
        }

    # 2. Check active pairing session (memory + persistent session file)
    session = _load_stored_pairing_session()
    active_pin = session.get("pin")
    expires_at = session.get("expires_at", 0.0)
    now = time.time()

    if not active_pin or clean_pin != str(active_pin).strip():
        logger.warning(f"Failed pairing attempt with invalid PIN: {clean_pin}")
        return None

    if now > expires_at:
        logger.warning(f"Pairing attempt with expired PIN: {clean_pin}")
        _clear_stored_pairing_session()
        return None

    # Clear active PIN to prevent reuse
    _clear_stored_pairing_session()

    token = secrets.token_urlsafe(32)
    device_id = f"dev_{secrets.token_hex(4)}"
    reg = register_paired_device(device_id, device_name, token)

    logger.info(f"Successfully paired mobile device '{device_name}' (ID: {device_id})")
    return {
        "success": True,
        "device_id": device_id,
        "device_name": device_name,
        "auth_token": token,
        "paired_at": reg["paired_at"]
    }

# ---------------------------------------------------------------------------
# Remote Input Simulation (Mouse & Keyboard)
# ---------------------------------------------------------------------------

def handle_mouse_event(action: str, **kwargs) -> Dict[str, Any]:
    """
    Dispatches mouse movement, clicks, and scrolling safely.
    Optimized for zero latency and high precision.
    """
    try:
        act = action.lower()
        if sys.platform == "win32":
            import ctypes
            user32 = ctypes.windll.user32
            MOUSEEVENTF_MOVE = 0x0001
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            MOUSEEVENTF_MIDDLEDOWN = 0x0020
            MOUSEEVENTF_MIDDLEUP = 0x0040
            MOUSEEVENTF_WHEEL = 0x0800

            if act == "move":
                dx = int(round(float(kwargs.get("dx", 0))))
                dy = int(round(float(kwargs.get("dy", 0))))
                if dx != 0 or dy != 0:
                    user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
                return {"status": "ok", "action": "move"}

            elif act == "click":
                button = kwargs.get("button", "left").lower()
                if button == "right":
                    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                elif button == "middle":
                    user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                    user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
                else:
                    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                return {"status": "ok", "action": "click", "button": button}

            elif act == "double_click":
                user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0.04)
                user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                return {"status": "ok", "action": "double_click"}

            elif act == "down":
                button = kwargs.get("button", "left").lower()
                flag = MOUSEEVENTF_RIGHTDOWN if button == "right" else MOUSEEVENTF_LEFTDOWN
                user32.mouse_event(flag, 0, 0, 0, 0)
                return {"status": "ok", "action": "down"}

            elif act == "up":
                button = kwargs.get("button", "left").lower()
                flag = MOUSEEVENTF_RIGHTUP if button == "right" else MOUSEEVENTF_LEFTUP
                user32.mouse_event(flag, 0, 0, 0, 0)
                return {"status": "ok", "action": "up"}

            elif act == "scroll":
                dy = int(kwargs.get("dy", 0))
                user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(dy * 40), 0)
                return {"status": "ok", "action": "scroll"}

        import pyautogui
        old_fs = getattr(pyautogui, "FAILSAFE", True)
        old_pause = getattr(pyautogui, "PAUSE", 0.1)
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.0
        try:
            sw, sh = pyautogui.size()
            if act == "move":
                dx = float(kwargs.get("dx", 0))
                dy = float(kwargs.get("dy", 0))
                speed_mult = float(kwargs.get("speed", 1.0))
                pyautogui.moveRel(dx * speed_mult, dy * speed_mult)
                return {"status": "ok", "action": "move"}
            elif act == "move_to":
                x = max(0, min(sw - 1, int(kwargs.get("x", 0))))
                y = max(0, min(sh - 1, int(kwargs.get("y", 0))))
                pyautogui.moveTo(x, y)
                return {"status": "ok", "action": "move_to", "x": x, "y": y}
            elif act == "click":
                button = kwargs.get("button", "left").lower()
                pyautogui.click(button=button if button in ("left", "right", "middle") else "left")
                return {"status": "ok", "action": "click"}
            elif act == "scroll":
                dy = int(kwargs.get("dy", 0))
                pyautogui.scroll(dy * 30)
                return {"status": "ok", "action": "scroll"}
            return {"status": "error", "message": f"Unknown mouse action: {action}"}
        finally:
            pyautogui.FAILSAFE = old_fs
            pyautogui.PAUSE = old_pause
    except Exception as e:
        logger.error(f"Mouse dispatch error: {e}")
        return {"status": "error", "message": str(e)}

def handle_keyboard_event(action: str, **kwargs) -> Dict[str, Any]:
    """
    Dispatches keyboard events (typing text, special key press, key shortcuts).
    """
    try:
        import pyautogui
        old_fs = getattr(pyautogui, "FAILSAFE", True)
        pyautogui.FAILSAFE = False
        try:
            act = action.lower()
            if act == "type":
                text = str(kwargs.get("text", ""))
                if text:
                    pyautogui.write(text, interval=0.005)
                return {"status": "ok", "action": "type", "length": len(text)}

            elif act == "press":
                key = str(kwargs.get("key", "")).lower()
                # Map common mobile alias keys
                key_map = {
                    "enter": "enter", "backspace": "backspace", "delete": "delete",
                    "tab": "tab", "escape": "esc", "esc": "esc",
                    "up": "up", "down": "down", "left": "left", "right": "right",
                    "space": "space", "win": "win", "windows": "win",
                    "home": "home", "end": "end", "pageup": "pageup", "pagedown": "pagedown"
                }
                k = key_map.get(key, key)
                pyautogui.press(k)
                return {"status": "ok", "action": "press", "key": k}

            elif act == "hotkey":
                keys = kwargs.get("keys", [])
                if isinstance(keys, list) and keys:
                    pyautogui.hotkey(*[str(k).lower() for k in keys])
                    return {"status": "ok", "action": "hotkey", "keys": keys}

            return {"status": "error", "message": f"Unknown keyboard action: {action}"}
        finally:
            pyautogui.FAILSAFE = old_fs
    except Exception as e:
        logger.error(f"Keyboard dispatch error: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# System Controls & Telemetry
# ---------------------------------------------------------------------------

def handle_system_command(command: str, value: Any = None) -> Dict[str, Any]:
    """Handles power, audio volume, brightness, and quick app launch commands."""
    cmd = command.lower().strip()
    try:
        import pyautogui
        old_fs = getattr(pyautogui, "FAILSAFE", True)
        pyautogui.FAILSAFE = False
        try:
            if cmd == "volume_up":
                pyautogui.press("volumeup", presses=5)
                return {"status": "ok", "message": "Increased volume"}
            elif cmd == "volume_down":
                pyautogui.press("volumedown", presses=5)
                return {"status": "ok", "message": "Decreased volume"}
            elif cmd == "volume_mute":
                pyautogui.press("volumemute")
                return {"status": "ok", "message": "Toggled volume mute"}
            elif cmd == "media_play_pause":
                pyautogui.press("playpause")
                return {"status": "ok", "message": "Toggled media playback"}
            elif cmd == "media_next":
                pyautogui.press("nexttrack")
                return {"status": "ok", "message": "Skipped track"}
            elif cmd == "media_prev":
                pyautogui.press("prevtrack")
                return {"status": "ok", "message": "Previous track"}
            elif cmd == "set_brightness":
                from tools.computer_settings import set_brightness
                level = int(value if value is not None else 70)
                msg = set_brightness(level)
                return {"status": "ok", "message": msg}
            elif cmd == "get_brightness":
                from tools.computer_settings import get_brightness
                b_val = get_brightness()
                return {"status": "ok", "brightness": b_val}
            elif cmd == "toggle_dark_mode":
                from tools.computer_settings import toggle_dark_mode
                msg = toggle_dark_mode()
                return {"status": "ok", "message": msg}
            elif cmd == "lock_pc":
                import ctypes
                ctypes.windll.user32.LockWorkStation()
                return {"status": "ok", "message": "PC locked successfully"}
            elif cmd == "sleep_pc":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return {"status": "ok", "message": "PC sleep command dispatched"}
            elif cmd == "launch_app":
                try:
                    from tools.applications import launch_application
                except ImportError:
                    from tools.applications import open_app
                    launch_application = open_app
                app_name = str(value if value else "notepad")
                msg = launch_application(app_name)
                return {"status": "ok", "message": msg}
            else:
                return {"status": "error", "message": f"Unknown system command: {cmd}"}
        finally:
            pyautogui.FAILSAFE = old_fs
    except Exception as e:
        logger.error(f"System command error: {e}")
        return {"status": "error", "message": str(e)}

def get_system_telemetry() -> Dict[str, Any]:
    """Collects real-time hardware telemetry: CPU, RAM, Battery, Storage, Active Window."""
    try:
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        
        battery_data = {"percent": 100, "plugged": True}
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_data = {
                    "percent": round(battery.percent, 1),
                    "plugged": battery.power_plugged
                }
        except Exception:
            pass

        disk = psutil.disk_usage('/')
        
        # Active foreground window title
        active_window = "Desktop"
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                active_window = buff.value or "Desktop"
        except Exception:
            pass

        # Display Brightness
        curr_brightness = None
        try:
            from tools.computer_settings import get_brightness
            curr_brightness = get_brightness()
        except Exception:
            pass

        return {
            "cpu_percent": cpu_usage,
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 1),
            "battery": battery_data,
            "active_window": active_window,
            "brightness": curr_brightness,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Telemetry error: {e}")
        return {"cpu_percent": 0, "ram_percent": 0, "error": str(e)}

# ---------------------------------------------------------------------------
# Live Screen Streaming (JPEG Snapshot)
# ---------------------------------------------------------------------------

def get_screen_jpeg(quality: int = 65, scale: float = 0.6) -> bytes:
    """
    Captures the primary monitor screen, scales it down, and compresses
    to JPEG bytes for low-latency streaming to mobile browsers.
    Employs bulletproof multi-fallback (PyAutoGUI -> ImageGrab -> Blank Canvas).
    """
    img = None
    # 1. PyAutoGUI
    try:
        import pyautogui
        old_fs = getattr(pyautogui, "FAILSAFE", True)
        pyautogui.FAILSAFE = False
        try:
            img = pyautogui.screenshot()
        finally:
            pyautogui.FAILSAFE = old_fs
    except Exception:
        pass

    # 2. PIL ImageGrab
    if not img:
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
        except Exception:
            pass

    # 3. Fallback Canvas
    if not img:
        img = Image.new('RGB', (800, 600), color=(5, 11, 20))

    if scale != 1.0 and img:
        new_w = max(320, int(img.width * scale))
        new_h = max(240, int(img.height * scale))
        img = img.resize((new_w, new_h), Image.Resampling.BILINEAR)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()

# ---------------------------------------------------------------------------
# Mobile AI Agent Execution
# ---------------------------------------------------------------------------

def execute_mobile_agent_query(user_text: str, conversation_id: Optional[str] = None, confirmed: bool = False) -> Dict[str, Any]:
    """
    JARVIS V4 Authoritative Mobile Execution.
    Routes through ChatService and strictly enforces server-side confirmation policies
    for CONFIRM-tier tools, blocking unconfirmed remote execution.
    """
    if not user_text.strip():
        return {"reply": "I received an empty message, sir.", "success": False, "actions": []}

    database.save_conversation("User (Mobile)", user_text)

    try:
        from orchestration.chat_service import get_chat_service, ChatRequestDTO
        service = get_chat_service()
        dto = ChatRequestDTO(
            message=user_text,
            conversation_id=conversation_id,
            confirmed=confirmed,
            user_id="mobile_client"
        )

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    res = pool.submit(lambda: asyncio.run(service.handle(dto))).result()
            else:
                res = asyncio.run(service.handle(dto))
        except Exception:
            res = asyncio.run(service.handle(dto))

        reply = res.content
        database.save_conversation("JARVIS", reply)

        actions = [e.get("tool") for e in res.tool_events if e.get("tool")]

        if res.requires_confirmation:
            return {
                "status": "requires_confirmation",
                "requires_confirmation": True,
                "reply": reply or "This action requires confirmation, sir.",
                "tool": (res.confirmation_payload or {}).get("tool"),
                "arguments": (res.confirmation_payload or {}).get("arguments", {}),
                "confirmation_payload": res.confirmation_payload,
                "conversation_id": res.conversation_id,
                "success": False,
                "actions": actions,
                "plan": []
            }

        return {
            "status": "completed" if res.status == "completed" else res.status,
            "reply": reply,
            "conversation_id": res.conversation_id,
            "success": (res.status == "completed"),
            "actions": actions,
            "plan": []
        }
    except Exception as e:
        logger.warning(f"Mobile ChatService execution failed: {e}. Falling back to safe brain reply.")
        try:
            from server import fetch_ai_brain_reply
            reply = fetch_ai_brain_reply(user_text)
            database.save_conversation("JARVIS", reply)
            return {"status": "completed", "reply": reply, "success": True, "actions": []}
        except Exception as e2:
            return {"status": "error", "reply": f"Error executing instruction: {e2}", "success": False, "actions": []}

execute_instruction_mobile = execute_mobile_agent_query

# ---------------------------------------------------------------------------
# Clipboard & File Sync
# ---------------------------------------------------------------------------

def get_clipboard_text() -> str:
    """Retrieves current text from the host PC clipboard."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text
    except Exception:
        return ""

def set_clipboard_text(text: str) -> bool:
    """Writes text to the host PC clipboard."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception as e:
        logger.error(f"Error setting clipboard: {e}")
        return False

def save_uploaded_file(filename: str, file_bytes: bytes) -> str:
    """Saves a file uploaded from mobile into PC Downloads directory safely, rejecting sensitive files."""
    from core.permissions import is_sensitive_path
    clean_name = Path(filename).name
    if not clean_name or is_sensitive_path(clean_name):
        raise ValueError(f"Upload of sensitive or restricted file '{filename}' is prohibited.")

    downloads_dir = Path.home() / "Downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    target_path = downloads_dir / clean_name
    
    # Avoid collision
    counter = 1
    base_stem = target_path.stem
    suffix = target_path.suffix
    while target_path.exists():
        target_path = downloads_dir / f"{base_stem}_{counter}{suffix}"
        counter += 1

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    logger.info(f"Saved uploaded mobile file: {target_path}")
    return str(target_path)
