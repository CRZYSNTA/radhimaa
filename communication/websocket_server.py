"""
JARVIS V4 WebSocket Server Bridge
Provides a dedicated WebSocket server on port 8765 (or integrated into FastAPI)
connecting the Python backend to the 3D WebGL Holographic UI.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Set, Optional, Any
from communication.broadcaster import get_broadcaster

logger = logging.getLogger("JARVIS.WebSocketServer")


class HologramWebSocketServer:
    """Lightweight WebSocket server using FastAPI & Uvicorn for holographic clients."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[Any] = set()
        self._broadcaster = get_broadcaster()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start_in_background(self):
        """Starts the standalone bridge server on a daemon thread using uvicorn."""
        if self._running:
            return
        self._running = True

        def _run():
            try:
                import uvicorn
                from fastapi import FastAPI, WebSocket, WebSocketDisconnect

                app = FastAPI(title="JARVIS Hologram WebSocket Bridge")

                @app.websocket("/ws/hologram")
                @app.websocket("/")
                async def ws_hologram_endpoint(websocket: WebSocket):
                    await websocket.accept()
                    self.clients.add(websocket)
                    logger.info("[WebSocketServer] Client connected to hologram bridge.")

                    # Send initial synchronization
                    try:
                        init_burst = {
                            "event": "init_sync",
                            "state": self._broadcaster._current_state,
                            "theme": self._broadcaster._current_theme,
                            "system": self._broadcaster._last_system_stats
                        }
                        await websocket.send_text(json.dumps(init_burst))
                    except Exception as e:
                        logger.debug(f"[WebSocketServer] Init error: {e}")

                    queue = asyncio.Queue()
                    self._broadcaster.register_async_queue(queue)

                    async def send_worker():
                        try:
                            while True:
                                msg = await queue.get()
                                await websocket.send_text(msg)
                        except asyncio.CancelledError:
                            pass
                        except Exception:
                            pass

                    send_task = asyncio.create_task(send_worker())

                    try:
                        while True:
                            data = await websocket.receive_text()
                            try:
                                payload = json.loads(data)
                                event_type = payload.get("event")
                                if event_type in ("set_theme", "theme_change"):
                                    theme = payload.get("theme") or payload.get("color", "orange")
                                    self._broadcaster.broadcast_theme(theme)
                                elif event_type == "ping":
                                    await websocket.send_text(json.dumps({"event": "pong"}))
                                elif event_type == "user_query":
                                    q = payload.get("query", "").strip()
                                    if q:
                                        from core.router import route_intent
                                        route_res = route_intent(q)
                                        self._broadcaster.broadcast_command("EXECUTE_QUERY", {"query": q, "route": route_res.get("tool")})
                            except json.JSONDecodeError:
                                pass
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        logger.debug(f"[WebSocketServer] Client connection error: {e}")
                    finally:
                        send_task.cancel()
                        self._broadcaster.unregister_async_queue(queue)
                        self.clients.discard(websocket)
                        logger.info("[WebSocketServer] Client disconnected from hologram bridge.")

                uvicorn.run(app, host=self.host, port=self.port, log_level="warning")
            except Exception as e:
                logger.error(f"[WebSocketServer] Failed to run uvicorn server: {e}")

        self._thread = threading.Thread(target=_run, daemon=True, name="HologramWSBridge")
        self._thread.start()
        return self._thread


_global_ws_server: Optional[HologramWebSocketServer] = None

def get_hologram_ws_server(port: int = 8765) -> HologramWebSocketServer:
    global _global_ws_server
    if _global_ws_server is None:
        _global_ws_server = HologramWebSocketServer(port=port)
    return _global_ws_server


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    srv = get_hologram_ws_server()
    srv.start_in_background()
    print("Hologram WebSocket Bridge started on ws://127.0.0.1:8765")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
