"""
JARVIS V3.0 - Autonomous Background Monitors & Triggers
Provides continuous background tracking for:
1. Cryptocurrency price triggers (CoinGecko free API)
2. Website uptime, HTTP response codes, and latency
3. System hardware thresholds (CPU spike, High RAM consumption)
Alerts are announced via audio TTS, task HUD, and system logger.
"""

from __future__ import annotations

import time
import uuid
import psutil
import logging
import threading
import urllib.request
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JARVIS.Tools.BackgroundMonitor")

_MONITORS: Dict[str, Dict[str, Any]] = {}
_MONITOR_LOCK = threading.Lock()
_WORKER_THREAD: Optional[threading.Thread] = None
_RUNNING = False


def _dispatch_alert(title: str, message: str, alert_type: str = "warning"):
    """Dispatches alert to Voice TTS, Task HUD, and logging."""
    logger.warning(f"[Background Alert] {title}: {message}")

    # UI Task HUD banner
    try:
        from ui.overlay import show_task_hud
        show_task_hud(title=title, subtitle=message, icon="⚠️", alert_type=alert_type)
    except Exception as e:
        logger.debug(f"HUD alert error: {e}")

    # Voice TTS alert
    try:
        from voice.text_to_speech import speak
        speak(f"Alert, sir: {message}", block=False)
    except Exception as e:
        logger.debug(f"Voice alert error: {e}")


def _check_system_monitor(m: Dict[str, Any]):
    ram = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent(interval=None)

    ram_thresh = m.get("ram_threshold", 85.0)
    cpu_thresh = m.get("cpu_threshold", 90.0)

    if ram > ram_thresh:
        _dispatch_alert("Memory Spike Alert", f"RAM usage has reached {ram}%, exceeding your threshold of {ram_thresh}%.", "alert")
    elif cpu > cpu_thresh:
        _dispatch_alert("CPU Spike Alert", f"Processor load is at {cpu}%, exceeding your threshold of {cpu_thresh}%.", "alert")


def _check_crypto_monitor(m: Dict[str, Any]):
    coin = m.get("coin_id", "bitcoin").lower().strip()
    thresh = float(m.get("threshold", 0.0))
    cond = m.get("condition", "above").lower().strip()

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Assistant/3.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if coin in data and "usd" in data[coin]:
            price = data[coin]["usd"]
            m["last_price"] = price

            if cond == "above" and price >= thresh:
                _dispatch_alert("Crypto Price Trigger", f"{coin.capitalize()} has crossed above ${thresh:,.2f}. Current price: ${price:,.2f}.", "success")
                m["triggered"] = True
            elif cond == "below" and price <= thresh:
                _dispatch_alert("Crypto Price Trigger", f"{coin.capitalize()} has fallen below ${thresh:,.2f}. Current price: ${price:,.2f}.", "alert")
                m["triggered"] = True


def _check_website_monitor(m: Dict[str, Any]):
    url = m.get("url", "")
    if not url.startswith("http"):
        url = "https://" + url

    start_t = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Uptime-Monitor/3.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        latency_ms = int((time.time() - start_t) * 1000)
        status_code = resp.getcode()
        m["last_status"] = status_code
        m["last_latency_ms"] = latency_ms

        if status_code >= 400:
            _dispatch_alert("Website Downtime Alert", f"Website {url} returned HTTP error code {status_code}.", "alert")


def _monitor_loop():
    global _RUNNING
    while _RUNNING:
        time.sleep(5)
        now = time.time()

        with _MONITOR_LOCK:
            for mid, m in list(_MONITORS.items()):
                if m.get("triggered") and m.get("one_shot", False):
                    continue

                interval = m.get("interval_sec", 60)
                last_chk = m.get("last_check", 0)

                if now - last_chk >= interval:
                    m["last_check"] = now
                    try:
                        m_type = m.get("type")
                        if m_type == "system":
                            _check_system_monitor(m)
                        elif m_type == "crypto":
                            _check_crypto_monitor(m)
                        elif m_type == "website":
                            _check_website_monitor(m)
                    except Exception as err:
                        logger.debug(f"[Monitor Check Error mid={mid}]: {err}")


def _ensure_worker_running():
    global _WORKER_THREAD, _RUNNING
    if not _RUNNING:
        _RUNNING = True
        _WORKER_THREAD = threading.Thread(target=_monitor_loop, daemon=True, name="JarvisBackgroundMonitors")
        _WORKER_THREAD.start()


# ── Public Tool APIs ───────────────────────────────────────────────────────────

def monitor_crypto_price(coin_id: str, threshold: float, condition: str = "above", interval_sec: int = 60) -> str:
    """
    Schedules background polling for a cryptocurrency price (CoinGecko).
    Args:
        coin_id: Coin identifier (e.g. 'bitcoin', 'ethereum', 'solana', 'dogecoin').
        threshold: The target price in USD.
        condition: 'above' to trigger when price exceeds threshold, 'below' for drops.
        interval_sec: Polling frequency in seconds (default 60s).
    """
    _ensure_worker_running()
    mid = f"crypto_{coin_id}_{str(uuid.uuid4())[:4]}"

    with _MONITOR_LOCK:
        _MONITORS[mid] = {
            "id": mid,
            "type": "crypto",
            "coin_id": coin_id.lower().strip(),
            "threshold": float(threshold),
            "condition": condition.lower().strip(),
            "interval_sec": max(15, interval_sec),
            "last_check": 0,
            "one_shot": True,
        }

    return f"Background monitor active: I will alert you as soon as {coin_id.capitalize()} moves {condition} ${threshold:,.2f}, sir."


def monitor_website_uptime(url: str, interval_sec: int = 60) -> str:
    """
    Monitors a website URL for uptime, HTTP errors, and latency.
    Args:
        url: The website domain or URL (e.g., 'https://google.com').
        interval_sec: Check frequency in seconds (default 60s).
    """
    _ensure_worker_running()
    mid = f"site_{str(uuid.uuid4())[:6]}"

    with _MONITOR_LOCK:
        _MONITORS[mid] = {
            "id": mid,
            "type": "website",
            "url": url.strip(),
            "interval_sec": max(10, interval_sec),
            "last_check": 0,
        }

    return f"Website uptime monitor established for {url} (checking every {interval_sec}s), sir."


def monitor_system_resources(ram_threshold: float = 85.0, cpu_threshold: float = 90.0, interval_sec: int = 30) -> str:
    """
    Monitors system hardware resources and triggers alerts if thresholds are crossed.
    Args:
        ram_threshold: RAM % usage threshold (default 85%).
        cpu_threshold: CPU % usage threshold (default 90%).
        interval_sec: Check frequency in seconds.
    """
    _ensure_worker_running()
    mid = "sys_health_guard"

    with _MONITOR_LOCK:
        _MONITORS[mid] = {
            "id": mid,
            "type": "system",
            "ram_threshold": float(ram_threshold),
            "cpu_threshold": float(cpu_threshold),
            "interval_sec": max(5, interval_sec),
            "last_check": 0,
        }

    return f"System health monitor configured: Alerts set for RAM > {ram_threshold}% or CPU > {cpu_threshold}%, sir."


def list_background_monitors() -> str:
    """Returns active background monitors and their current statuses."""
    with _MONITOR_LOCK:
        if not _MONITORS:
            return "No background monitors are currently active, sir."

        lines = ["Active Background Monitors:"]
        for mid, m in _MONITORS.items():
            m_type = m.get("type", "unknown")
            if m_type == "crypto":
                lines.append(f"- [{mid}] Crypto: {m['coin_id'].capitalize()} {m['condition']} ${m['threshold']:,.2f}")
            elif m_type == "website":
                lines.append(f"- [{mid}] Web Uptime: {m['url']} (Every {m['interval_sec']}s)")
            elif m_type == "system":
                lines.append(f"- [{mid}] Hardware: RAM > {m['ram_threshold']}%, CPU > {m['cpu_threshold']}%")
        return "\n".join(lines)


def cancel_background_monitor(monitor_id: str) -> str:
    """Cancels an active background monitor by its ID."""
    with _MONITOR_LOCK:
        target = monitor_id.strip().lower()
        matched = [k for k in _MONITORS if k.lower() == target or target in k.lower()]
        if not matched:
            return f"No active monitor found matching '{monitor_id}', sir."

        for k in matched:
            del _MONITORS[k]
        return f"Cancelled {len(matched)} background monitor(s), sir."
