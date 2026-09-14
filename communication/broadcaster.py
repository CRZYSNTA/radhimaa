"""
JARVIS V4 Hologram Event Broadcaster
Thread-safe event dispatcher that bridges Python core, voice, TV tools,
and system monitors to all connected holographic UI clients.
"""

import json
import logging
import threading
import time
from typing import Callable, List, Dict, Any, Optional

logger = logging.getLogger("JARVIS.Broadcaster")

class HologramBroadcaster:
    """Thread-safe event broadcaster for holographic UI clients."""
    _instance: Optional["HologramBroadcaster"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._subscribers: List[Callable[[str], None]] = []
        self._async_subscribers: List[Any] = []
        self._current_state = "IDLE"
        self._current_theme = "orange"
        self._last_system_stats: Dict[str, Any] = {"cpu": 0, "ram": 0, "network": "CONNECTED"}
        self._sub_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "HologramBroadcaster":
        with cls._lock:
            if cls._instance is None:
                cls._instance = HologramBroadcaster()
            return cls._instance

    def subscribe(self, callback: Callable[[str], None]) -> None:
        """Register a synchronous JSON consumer callback."""
        with self._sub_lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[str], None]) -> None:
        """Remove a subscriber."""
        with self._sub_lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def register_async_queue(self, q: Any) -> None:
        """Register an asyncio.Queue for async WebSocket connections."""
        with self._sub_lock:
            if q not in self._async_subscribers:
                self._async_subscribers.append(q)

    def unregister_async_queue(self, q: Any) -> None:
        """Unregister an asyncio.Queue."""
        with self._sub_lock:
            if q in self._async_subscribers:
                self._async_subscribers.remove(q)

    def _broadcast_payload(self, payload: Dict[str, Any]) -> None:
        """Serialize and push event payload to all subscribers."""
        try:
            payload["timestamp"] = time.time()
            message = json.dumps(payload)
        except Exception as e:
            logger.error(f"[Broadcaster] JSON encode error: {e}")
            return

        # Synchronous subscribers
        with self._sub_lock:
            sync_subs = list(self._subscribers)
            async_subs = list(self._async_subscribers)

        for callback in sync_subs:
            try:
                callback(message)
            except Exception as e:
                logger.debug(f"[Broadcaster] Subscriber error: {e}")

        # Async queues
        for q in async_subs:
            try:
                q.put_nowait(message)
            except Exception:
                pass

    # --- Domain Specific Broadcast API ---

    def broadcast_state(self, state: str, details: str = "") -> None:
        """Broadcasts JARVIS/LEO operational state change and syncs .voice_state."""
        self._current_state = state.upper()
        self._broadcast_payload({
            "event": "state_change",
            "state": self._current_state,
            "details": details
        })

        # Sync to LEO visualizer bus
        from pathlib import Path
        import config
        s_dirs = [
            Path("d:/agent/backtalk"),
            Path(getattr(config, "BASE_DIR", ".")) / "leo" / "backtalk",
            Path(getattr(config, "BASE_DIR", ".")),
        ]
        for s_dir in s_dirs:
            if s_dir.exists():
                try:
                    (s_dir / ".voice_state").write_text(self._current_state.lower(), encoding="utf-8")
                except Exception:
                    pass

    def broadcast_theme(self, theme_or_color: str) -> None:
        """Broadcasts dynamic theme or hex color change."""
        is_hex = theme_or_color.startswith("#")
        self._current_theme = theme_or_color
        payload = {
            "event": "theme_change",
            "theme": theme_or_color if not is_hex else "custom",
            "color": theme_or_color if is_hex else None
        }
        self._broadcast_payload(payload)

    def broadcast_audio_level(self, level: float) -> None:
        """Broadcasts normalized 0.0 - 1.0 audio amplitude level."""
        clamped = max(0.0, min(1.0, float(level)))
        self._broadcast_payload({
            "event": "audio_level",
            "level": round(clamped, 3)
        })

    def broadcast_command(self, command: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Broadcasts tool/command execution visualization event."""
        self._broadcast_payload({
            "event": "command",
            "command": command.upper(),
            "details": details or {}
        })

    def broadcast_assistant_text(self, text: str) -> None:
        """Broadcasts AI speech / response text."""
        self._broadcast_payload({
            "event": "assistant_text",
            "text": text
        })

    def broadcast_system_status(self, cpu: float, ram: float, network: str = "CONNECTED") -> None:
        """Broadcasts hardware and network telemetry."""
        self._last_system_stats = {
            "cpu": round(cpu, 1),
            "ram": round(ram, 1),
            "network": network
        }
        self._broadcast_payload({
            "event": "system_status",
            "cpu": round(cpu, 1),
            "ram": round(ram, 1),
            "network": network
        })

        from pathlib import Path
        import config
        s_dirs = [
            Path("d:/agent/backtalk"),
            Path(getattr(config, "BASE_DIR", ".")) / "leo" / "backtalk",
            Path(getattr(config, "BASE_DIR", ".")),
        ]
        telemetry_json = json.dumps({
            "cpu": round(cpu),
            "ram": round(ram),
            "ts": time.time()
        })
        for s_dir in s_dirs:
            if s_dir.exists():
                try:
                    (s_dir / ".voice_telemetry").write_text(telemetry_json, encoding="utf-8")
                except Exception:
                    pass

    def broadcast_tv_status(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Broadcasts Smart TV state / command visualization."""
        base_details = {
            "device": "TCL Android TV",
            "action": action.upper()
        }
        if details:
            base_details.update(details)

        self._broadcast_payload({
            "event": "tv_status",
            "action": action.upper(),
            "details": base_details
        })


def get_broadcaster() -> HologramBroadcaster:
    """Convenience accessor for the global singleton broadcaster."""
    return HologramBroadcaster.get_instance()
