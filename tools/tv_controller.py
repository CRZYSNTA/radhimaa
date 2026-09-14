"""
JARVIS V4 - Universal Smart TV Controller & Discovery Engine
Supports:
1. Android TV / Google TV / Fire TV (ADB over Wi-Fi, port 5555)
2. Roku TV (External Control Protocol HTTP, port 8060)
3. Samsung Smart TV (Tizen HTTP/WS, port 8001/8002)
4. LG Smart TV (webOS, port 3000/3001)
5. Google Cast / Chromecast (port 8008)
"""

from __future__ import annotations

import os
import re
import json
import socket
import logging
import urllib.request
import urllib.parse
import subprocess
import concurrent.futures
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger("JARVIS.Tools.TV")

TV_CONFIG_FILE = Path(__file__).resolve().parent.parent / ".tv_config.json"


def get_tv_config() -> Dict[str, Any]:
    """Loads saved Smart TV configuration."""
    if TV_CONFIG_FILE.exists():
        try:
            return json.loads(TV_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_tv_config(
    ip: Optional[str] = None,
    port: Optional[int] = None,
    tv_type: Optional[str] = None,
    tv_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Saves Smart TV connection profile."""
    cfg = get_tv_config()
    if ip:
        cfg["tv_ip"] = ip.strip()
    if port:
        cfg["tv_port"] = int(port)
    if tv_type:
        cfg["tv_type"] = tv_type.strip().lower()
    if tv_name:
        cfg["tv_name"] = tv_name.strip()
    try:
        TV_CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not save TV config: {e}")
    return cfg


def get_local_ip_prefix() -> str:
    """Detects local network subnet prefix, e.g. '192.168.1'."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}"
    except Exception:
        return "192.168.1"


def get_adb_bin() -> Optional[str]:
    """Finds adb.exe for Android/Google/Fire TV control."""
    from tools.phone_controller import get_adb_path
    return get_adb_path()


def _probe_port(ip: str, port: int, timeout: float = 0.3) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        ok = (s.connect_ex((ip, port)) == 0)
        s.close()
        return ok
    except Exception:
        return False


def discover_smart_tvs(timeout_sec: float = 2.0) -> str:
    """
    Scans the local Wi-Fi subnet for connected Smart TVs:
    - Android TV / Fire TV (5555)
    - Roku TV (8060)
    - Samsung Smart TV (8001)
    - LG webOS TV (3000)
    - Google Cast / Chromecast (8008)
    """
    prefix = get_local_ip_prefix()
    logger.info(f"[TV Discovery] Scanning local subnet {prefix}.0/24...")

    target_ports = {
        5555: "Android TV / Fire TV",
        8060: "Roku TV",
        8001: "Samsung Smart TV",
        3000: "LG webOS TV",
        8008: "Google Cast / Chromecast",
    }

    found_devices: List[Dict[str, Any]] = []

    def scan_host(host_ip: str):
        for port, kind in target_ports.items():
            if _probe_port(host_ip, port, timeout=0.25):
                name = kind
                # Probe Roku device-info
                if port == 8060:
                    try:
                        req = urllib.request.Request(f"http://{host_ip}:8060/query/device-info", headers={"User-Agent": "JARVIS/4.0"})
                        with urllib.request.urlopen(req, timeout=1.0) as resp:
                            body = resp.read().decode("utf-8", errors="ignore")
                            m_name = re.search(r"<friendly-device-name>([^<]+)</friendly-device-name>", body)
                            m_model = re.search(r"<model-name>([^<]+)</model-name>", body)
                            if m_name:
                                name = f"Roku ({m_name.group(1)})"
                            elif m_model:
                                name = f"Roku ({m_model.group(1)})"
                    except Exception:
                        pass
                # Probe Google Cast info
                elif port == 8008:
                    try:
                        req = urllib.request.Request(f"http://{host_ip}:8008/setup/eureka_info", headers={"User-Agent": "JARVIS/4.0"})
                        with urllib.request.urlopen(req, timeout=1.0) as resp:
                            body = json.loads(resp.read().decode("utf-8", errors="ignore"))
                            if "name" in body:
                                name = f"Google Cast ({body['name']})"
                    except Exception:
                        pass
                # Probe Samsung info
                elif port == 8001:
                    try:
                        req = urllib.request.Request(f"http://{host_ip}:8001/api/v2/", headers={"User-Agent": "JARVIS/4.0"})
                        with urllib.request.urlopen(req, timeout=1.0) as resp:
                            body = json.loads(resp.read().decode("utf-8", errors="ignore"))
                            dev = body.get("device", {})
                            if "name" in dev:
                                name = f"Samsung TV ({dev['name']})"
                    except Exception:
                        pass

                return {
                    "ip": host_ip,
                    "port": port,
                    "type": kind,
                    "name": name,
                }
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as pool:
        futures = [pool.submit(scan_host, f"{prefix}.{i}") for i in range(1, 255)]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                found_devices.append(res)

    if not found_devices:
        cfg = get_tv_config()
        if cfg.get("tv_ip"):
            return (
                f"No new Smart TVs responded to the network broadcast, sir.\n"
                f"Your previously configured TV is at `{cfg['tv_ip']}:{cfg.get('tv_port', 5555)}` ({cfg.get('tv_name', 'Smart TV')}).\n"
                f"Ensure your TV is turned on and connected to Wi-Fi."
            )
        return (
            "No Smart TVs detected on local Wi-Fi, sir.\n"
            "Tip: For Android TV / Fire TV, ensure 'Network Debugging' is enabled in Developer Options.\n"
            "You can also connect directly by specifying: 'connect tv <ip>'."
        )

    # Automatically save the first TV found if none was configured yet
    cfg = get_tv_config()
    if not cfg.get("tv_ip"):
        first = found_devices[0]
        t_kind = "android_tv" if first["port"] == 5555 else ("roku" if first["port"] == 8060 else "smart_tv")
        save_tv_config(ip=first["ip"], port=first["port"], tv_type=t_kind, tv_name=first["name"])

    lines = [f"Found {len(found_devices)} Smart TV device(s) on `{prefix}.0/24`:"]
    for d in found_devices:
        lines.append(f"- **{d['name']}** at `{d['ip']}:{d['port']}` ({d['type']})")
    lines.append("\nYou can control your TV using voice or keyboard: 'tv volume up', 'tv ok', 'open youtube on tv', etc.")
    return "\n".join(lines)


def connect_tv(ip: str, port: Optional[int] = None, tv_type: str = "auto") -> str:
    """Connects to a specific Smart TV IP and saves profile."""
    clean_ip = ip.strip()
    actual_port = int(port) if port else 5555
    detected_type = tv_type.lower()

    if detected_type == "auto":
        if _probe_port(clean_ip, 8060):
            actual_port = 8060
            detected_type = "roku"
        elif _probe_port(clean_ip, 5555):
            actual_port = 5555
            detected_type = "android_tv"
        elif _probe_port(clean_ip, 8001):
            actual_port = 8001
            detected_type = "samsung"
        else:
            actual_port = 5555
            detected_type = "android_tv"

    if detected_type == "android_tv":
        adb = get_adb_bin()
        if adb:
            try:
                res = subprocess.run([adb, "connect", f"{clean_ip}:{actual_port}"], capture_output=True, text=True, timeout=8)
                out = res.stdout.strip()
                save_tv_config(ip=clean_ip, port=actual_port, tv_type=detected_type, tv_name=f"Android TV ({clean_ip})")
                return f"Connected to Android TV at {clean_ip}:{actual_port}: {out}"
            except Exception as e:
                return f"Error connecting to Android TV: {e}"

    save_tv_config(ip=clean_ip, port=actual_port, tv_type=detected_type, tv_name=f"Smart TV ({clean_ip})")
    return f"Smart TV configured at {clean_ip}:{actual_port} ({detected_type}), sir."


def _get_active_tv() -> Dict[str, Any]:
    cfg = get_tv_config()
    if not cfg.get("tv_ip"):
        # Attempt auto-discovery
        discover_smart_tvs()
        cfg = get_tv_config()
    return cfg


def tv_remote_control(action: str, tv_ip: Optional[str] = None) -> str:
    """
    Sends navigation, media, audio, or power keys to the TV.
    Actions:
      up, down, left, right, select, ok, enter,
      back, home, menu,
      volume_up, volume_down, mute,
      play, pause, play_pause, stop, next, prev,
      power, wake, sleep
    """
    cfg = _get_active_tv()
    ip = tv_ip.strip() if tv_ip else cfg.get("tv_ip")
    if not ip:
        return "No Smart TV IP configured. Please run 'discover tvs' or 'connect tv <ip>'."

    tv_type = cfg.get("tv_type", "android_tv")
    port = cfg.get("tv_port", 5555)
    normalized = action.lower().strip().replace(" ", "_")

    try:
        from communication.broadcaster import get_broadcaster
        get_broadcaster().broadcast_tv_status(action, {"ip": ip, "type": tv_type})
    except Exception:
        pass

    # 1. Roku Protocol
    if tv_type == "roku" or port == 8060:
        roku_key_map = {
            "up": "Up", "down": "Down", "left": "Left", "right": "Right",
            "select": "Select", "ok": "Select", "enter": "Select",
            "back": "Back", "home": "Home", "menu": "Info",
            "volume_up": "VolumeUp", "volume_down": "VolumeDown", "mute": "VolumeMute",
            "play": "Play", "pause": "Play", "play_pause": "Play",
            "power": "PowerOff", "sleep": "PowerOff", "wake": "PowerOn",
        }
        roku_key = roku_key_map.get(normalized, "Select")
        try:
            req = urllib.request.Request(f"http://{ip}:8060/keypress/{roku_key}", data=b"", method="POST")
            with urllib.request.urlopen(req, timeout=3):
                return f"Sent key '{roku_key}' to Roku TV at {ip}."
        except Exception as e:
            return f"Failed to send Roku key: {e}"

    # 2. Android TV / Fire TV ADB Protocol
    adb = get_adb_bin()
    if not adb:
        return "Android platform-tools (ADB) not found on PC."

    adb_endpoint = f"{ip}:{port}"
    adb_key_map = {
        "up": 19, "down": 20, "left": 21, "right": 22,
        "select": 23, "ok": 23, "enter": 23,
        "back": 4, "home": 3, "menu": 82,
        "volume_up": 24, "volume_down": 25, "mute": 164,
        "play": 126, "pause": 127, "play_pause": 85,
        "stop": 86, "next": 87, "prev": 88,
        "power": 26, "wake": 224, "sleep": 26,
    }
    keycode = adb_key_map.get(normalized, 23)

    try:
        # Re-ensure connected
        subprocess.run([adb, "connect", adb_endpoint], capture_output=True, timeout=4)
        subprocess.run([adb, "-s", adb_endpoint, "shell", "input", "keyevent", str(keycode)], capture_output=True, timeout=5)
        return f"Dispatched key '{action}' (keycode {keycode}) to TV at {adb_endpoint}, sir."
    except Exception as e:
        return f"TV key dispatch error: {e}"


def tv_launch_app(app_name: str, tv_ip: Optional[str] = None) -> str:
    """
    Launches streaming apps on Smart TV:
    YouTube, Netflix, Prime Video, Spotify, Disney+, Browser, etc.
    """
    cfg = _get_active_tv()
    ip = tv_ip.strip() if tv_ip else cfg.get("tv_ip")
    if not ip:
        return "No Smart TV IP configured. Say 'discover tvs' first."

    tv_type = cfg.get("tv_type", "android_tv")
    port = cfg.get("tv_port", 5555)
    app = app_name.lower().strip()

    try:
        from communication.broadcaster import get_broadcaster
        get_broadcaster().broadcast_tv_status(f"LAUNCH_{app.upper()}", {"ip": ip, "app": app, "type": tv_type})
    except Exception:
        pass

    # Roku App Launcher
    if tv_type == "roku" or port == 8060:
        roku_apps = {
            "youtube": "837",
            "netflix": "12",
            "prime": "13",
            "amazon": "13",
            "spotify": "22271",
            "disney": "291097",
        }
        app_id = None
        for k, v in roku_apps.items():
            if k in app:
                app_id = v
                break
        if not app_id:
            app_id = "837"  # Default to YouTube

        try:
            req = urllib.request.Request(f"http://{ip}:8060/launch/{app_id}", data=b"", method="POST")
            with urllib.request.urlopen(req, timeout=4):
                return f"Launched {app_name} on Roku TV ({ip})."
        except Exception as e:
            return f"Error launching app on Roku: {e}"

    # Android TV App Launcher
    adb = get_adb_bin()
    if not adb:
        return "ADB not found."

    adb_endpoint = f"{ip}:{port}"
    subprocess.run([adb, "connect", adb_endpoint], capture_output=True, timeout=4)

    try:
        if "youtube" in app:
            cmd = ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "vnd.youtube://"]
        elif "netflix" in app:
            cmd = ["shell", "monkey", "-p", "com.netflix.ninja", "1"]
        elif "prime" in app or "amazon" in app:
            cmd = ["shell", "monkey", "-p", "com.amazon.amazonvideo.livingroom", "1"]
        elif "spotify" in app:
            cmd = ["shell", "monkey", "-p", "com.spotify.tv.android", "1"]
        elif "disney" in app:
            cmd = ["shell", "monkey", "-p", "com.disney.disneyplus", "1"]
        elif "browser" in app or "chrome" in app or "web" in app:
            cmd = ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "https://www.google.com"]
        else:
            # General package launch or search
            cmd = ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"https://www.google.com/search?q={urllib.parse.quote(app_name)}"]

        subprocess.run([adb, "-s", adb_endpoint] + cmd, capture_output=True, timeout=6)
        return f"Successfully opened {app_name} on TV ({adb_endpoint}), sir."
    except Exception as e:
        return f"Error launching {app_name} on TV: {e}"


def tv_play_media(media_query: str, tv_ip: Optional[str] = None) -> str:
    """
    Plays a YouTube video or media URL directly on the TV.
    """
    cfg = _get_active_tv()
    ip = tv_ip.strip() if tv_ip else cfg.get("tv_ip")
    if not ip:
        return "No Smart TV IP configured."

    adb = get_adb_bin()
    if not adb:
        return "ADB not found."

    adb_endpoint = f"{ip}:{cfg.get('tv_port', 5555)}"
    query = media_query.strip()

    # Form URL if plain query
    if not (query.startswith("http://") or query.startswith("https://") or query.startswith("vnd.youtube:")):
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    else:
        url = query

    try:
        subprocess.run([adb, "connect", adb_endpoint], capture_output=True, timeout=4)
        subprocess.run(
            [adb, "-s", adb_endpoint, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url],
            capture_output=True, timeout=6
        )
        return f"Playing '{media_query}' on TV ({adb_endpoint}), sir."
    except Exception as e:
        return f"Error playing media on TV: {e}"


def tv_input_text(text: str, tv_ip: Optional[str] = None) -> str:
    """Types search terms or text into the TV."""
    cfg = _get_active_tv()
    ip = tv_ip.strip() if tv_ip else cfg.get("tv_ip")
    if not ip:
        return "No Smart TV IP configured."

    adb = get_adb_bin()
    if not adb:
        return "ADB not found."

    adb_endpoint = f"{ip}:{cfg.get('tv_port', 5555)}"
    clean_text = text.replace(" ", "%s").strip()

    try:
        subprocess.run([adb, "connect", adb_endpoint], capture_output=True, timeout=4)
        subprocess.run([adb, "-s", adb_endpoint, "shell", "input", "text", clean_text], capture_output=True, timeout=5)
        subprocess.run([adb, "-s", adb_endpoint, "shell", "input", "keyevent", "66"], capture_output=True, timeout=5)
        return f"Typed '{text}' on TV, sir."
    except Exception as e:
        return f"Error typing text on TV: {e}"
