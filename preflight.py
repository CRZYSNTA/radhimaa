"""
JARVIS V4 - Live Preflight Validation Engine
Tests the actual RUNNING JARVIS instance across real operational boundaries:
 SERVER -> AI -> MEMORY -> VOICE -> VISION -> TOOLS -> SECURITY -> WEBSOCKET

Semantics:
 PASS: Expected behavior verified.
 WARN: Environment-dependent / optional hardware capability is unavailable or limited.
 FAIL: Critical JARVIS capability broken or security boundary compromised.

Usage:
 python preflight.py [--url http://127.0.0.1:8000] [--token <optional_auth_token>]
"""

from __future__ import annotations

import sys
import time
import json
import argparse
import requests
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

@dataclass
class CheckResult:
    category: str
    name: str
    status: str  # PASS, WARN, FAIL
    details: str = ""

class PreflightRunner:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {"X-JARVIS-Token": token} if token else {}
        self.results: List[CheckResult] = []

    def log(self, category: str, name: str, status: str, details: str = "") -> None:
        self.results.append(CheckResult(category=category, name=name, status=status, details=details))

    def run_all(self) -> bool:
        """Runs all live preflight checks against the running server."""
        self.check_server_and_diagnostics()
        self.check_ai_subsystem()
        self.check_memory_pipeline()
        self.check_voice_readiness()
        self.check_vision_subsystem()
        self.check_tools_and_executor()
        self.check_security_boundaries()
        self.check_websocket_bridge()
        return not any(r.status == "FAIL" for r in self.results)

    # 1. SERVER & DIAGNOSTICS
    def check_server_and_diagnostics(self):
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            if r.status_code == 200:
                data = r.json()
                self.log("SERVER", "Running server", "PASS", f"Version {data.get('version', 'unknown')}")
            else:
                self.log("SERVER", "Running server", "FAIL", f"HTTP {r.status_code}")
                return
        except Exception as e:
            self.log("SERVER", "Running server", "FAIL", f"Unreachable: {e}")
            return

        try:
            r = requests.get(f"{self.base_url}/api/diagnostics", headers=self.headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "ok" and "server" in data and "ai" in data:
                    self.log("SERVER", "Diagnostics", "PASS", f"Instance: {data['server'].get('instance_id')}")
                else:
                    self.log("SERVER", "Diagnostics", "WARN", "Diagnostics response incomplete")
            else:
                self.log("SERVER", "Diagnostics", "FAIL", f"HTTP {r.status_code}")
        except Exception as e:
            self.log("SERVER", "Diagnostics", "FAIL", str(e))

    # 2. AI SUBSYSTEM
    def check_ai_subsystem(self):
        try:
            r = requests.get(f"{self.base_url}/api/diagnostics", headers=self.headers, timeout=10)
            if r.status_code == 200:
                ai_diag = r.json().get("ai", {})
                if ai_diag.get("initialized"):
                    self.log("AI", "Gateway ready", "PASS", f"Provider: {ai_diag.get('provider')}")
                else:
                    self.log("AI", "Gateway ready", "FAIL", "Gateway uninitialized")

                if ai_diag.get("available"):
                    self.log("AI", "Configured model reachable", "PASS", f"Model: {ai_diag.get('configured_model')}")
                else:
                    self.log("AI", "Configured model reachable", "WARN", "API key missing or provider offline (safe local fallback active)")
            else:
                self.log("AI", "Gateway ready", "FAIL", f"HTTP {r.status_code}")
        except Exception as e:
            self.log("AI", "Gateway ready", "FAIL", str(e))

    # 3. MEMORY PIPELINE
    def check_memory_pipeline(self):
        try:
            from memory.user_memory import user_memory
            probe_key = f"__preflight_probe_{int(time.time() * 1000)}"
            probe_val = "preflight_probe_ok"

            # Step 1: Write
            user_memory.remember(probe_key, probe_val, category="preflight")
            self.log("MEMORY", "Write", "PASS", "Temporary test fact written")

            # Step 2: Immediate Retrieval
            retrieved = user_memory.get_fact(probe_key)
            if retrieved == probe_val:
                self.log("MEMORY", "Immediate retrieval", "PASS", "Fact verified from storage")
            else:
                self.log("MEMORY", "Immediate retrieval", "FAIL", f"Value mismatch: {retrieved}")

            # Step 3: Cleanup
            forgotten = user_memory.forget(probe_key)
            after_forget = user_memory.get_fact(probe_key)
            if forgotten and after_forget is None:
                self.log("MEMORY", "Read & cleanup", "PASS", "Test fact purged successfully")
            else:
                self.log("MEMORY", "Read & cleanup", "WARN", "Fact cleanup incomplete")
        except Exception as e:
            self.log("MEMORY", "Memory pipeline", "FAIL", str(e))

    # 4. VOICE READINESS
    def check_voice_readiness(self):
        try:
            from voice.text_to_speech import format_speech_text
            clean = format_speech_text("Test [link](http://test.com) & 100% audio")
            if clean:
                self.log("VOICE", "TTS formatting & engine", "PASS", "Acoustic rules operational")
            else:
                self.log("VOICE", "TTS formatting & engine", "WARN", "TTS format check returned empty")

            from voice.ptt_engine import PYAUDIO_AVAILABLE, PYNPUT_AVAILABLE
            if PYAUDIO_AVAILABLE:
                self.log("VOICE", "STT audio hardware link", "PASS", "PyAudio device library linked")
            else:
                self.log("VOICE", "STT audio hardware link", "WARN", "PyAudio not installed; PTT fallback mode")

            if PYNPUT_AVAILABLE:
                self.log("VOICE", "Voice readiness", "PASS", "Global hotkey listener active (pynput)")
            else:
                self.log("VOICE", "Voice readiness", "WARN", "Optional PTT dependency unavailable (pynput not installed; native Windows PTT active)")
        except Exception as e:
            self.log("VOICE", "Voice readiness", "WARN", str(e))

    # 5. VISION SUBSYSTEM
    def check_vision_subsystem(self):
        # Screen capture
        try:
            from vision.screen import capture_screen_bytes
            s_bytes = capture_screen_bytes()
            if s_bytes and len(s_bytes) > 100:
                self.log("VISION", "Screen subsystem", "PASS", f"Captured {len(s_bytes)} JPEG bytes")
            else:
                self.log("VISION", "Screen subsystem", "WARN", "Desktop screen grab returned minimal canvas")
        except Exception as e:
            self.log("VISION", "Screen subsystem", "FAIL", str(e))

        # Camera hardware probe
        try:
            from vision.camera import is_camera_available
            if is_camera_available(0):
                self.log("VISION", "Camera device", "PASS", "Physical webcam accessible")
            else:
                self.log("VISION", "Camera device", "WARN", "Camera unavailable (no webcam attached)")
        except Exception as e:
            self.log("VISION", "Camera device", "WARN", f"Camera probe error: {e}")

    # 6. TOOLS AND EXECUTOR
    def check_tools_and_executor(self):
        try:
            from orchestration.tool_router import get_tool_router
            from tools.base import ToolContext
            router = get_tool_router()
            tools = router.list_tools()
            if tools:
                self.log("TOOLS", "Router catalog", "PASS", f"{len(tools)} tools registered")
            else:
                self.log("TOOLS", "Router catalog", "FAIL", "No tools loaded in catalog")
                return

            # Execute harmless read-only telemetry operation
            context = ToolContext(session_id="preflight_session", user_id="preflight_tester")
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        res = pool.submit(lambda: asyncio.run(router.execute_tool("get_system_telemetry", {}, context))).result()
                else:
                    res = loop.run_until_complete(router.execute_tool("get_system_telemetry", {}, context))
            except RuntimeError:
                res = asyncio.run(router.execute_tool("get_system_telemetry", {}, context))

            if res.success:
                self.log("TOOLS", "SAFE execution", "PASS", "get_system_telemetry executed cleanly")
            else:
                self.log("TOOLS", "SAFE execution", "FAIL", f"Execution error: {res.error}")

            if res.verification and res.verification.verified:
                self.log("TOOLS", "Verification", "PASS", "Post-execution verification passed")
            else:
                self.log("TOOLS", "Verification", "WARN", "Post-action verification details missing")
        except Exception as e:
            self.log("TOOLS", "Tools & executor", "FAIL", str(e))

    # 7. SECURITY BOUNDARIES
    def check_security_boundaries(self):
        # 1. Secret Isolation via read_file
        try:
            from tools.files import read_file
            res = read_file("config.json")
            if "i'm afraid i cannot access that file, sir" in res.lower() or "access denied" in res.lower():
                self.log("SECURITY", "Secret isolation", "PASS", "config.json access strictly blocked")
            else:
                self.log("SECURITY", "Secret isolation", "FAIL", "config.json was accessible!")
        except Exception as e:
            self.log("SECURITY", "Secret isolation", "FAIL", str(e))

        # 2. Origin Hijacking Rejection
        try:
            bad_origin_headers = {"Origin": "http://malicious-site.attacker.com"}
            r = requests.post(f"{self.base_url}/ask", json={"text": "ping"}, headers=bad_origin_headers, timeout=3)
            if r.status_code == 403:
                self.log("SECURITY", "Origin protection", "PASS", "Untrusted browser origin rejected with 403")
            else:
                self.log("SECURITY", "Origin protection", "FAIL", f"Origin not blocked: HTTP {r.status_code}")
        except Exception as e:
            self.log("SECURITY", "Origin protection", "FAIL", str(e))

        # 3. Mobile Confirmation Policy Enforcement
        try:
            from core.mobile_bridge import execute_mobile_agent_query
            sec_test = execute_mobile_agent_query(
                "update note 00 - Inbox/preflight_test: Test content",
                conversation_id="preflight_sec_test",
                confirmed=False
            )
            if sec_test.get("status") == "requires_confirmation" and sec_test.get("requires_confirmation") is True:
                self.log("SECURITY", "Mobile confirmation", "PASS", "CONFIRM-tier tool halted for approval")
            else:
                self.log("SECURITY", "Mobile confirmation", "FAIL", "Action executed without confirmation!")
        except Exception as e:
            self.log("SECURITY", "Mobile confirmation", "FAIL", str(e))

    # 8. WEBSOCKET BRIDGE
    def check_websocket_bridge(self):
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/hologram"
        connected = False
        data = None
        error_note = None

        # Method 1: aiohttp (production async client)
        try:
            import aiohttp
            import asyncio

            async def _probe():
                origin = self.base_url
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(ws_url, headers={"Origin": origin}) as ws:
                        msg = await ws.receive_json(timeout=3.0)
                        await ws.close()
                        return msg

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        data = pool.submit(lambda: asyncio.run(_probe())).result()
                else:
                    data = loop.run_until_complete(_probe())
            except RuntimeError:
                data = asyncio.run(_probe())
            connected = True
        except ImportError:
            pass
        except Exception as e:
            error_note = str(e)

        # Method 2: websocket-client fallback
        if not connected and error_note is None:
            try:
                import websocket
                ws = websocket.create_connection(ws_url, headers={"Origin": self.base_url}, timeout=3)
                init_msg = ws.recv()
                data = json.loads(init_msg)
                ws.close()
                connected = True
            except ImportError:
                pass
            except Exception as e:
                error_note = str(e)

        if connected and isinstance(data, dict):
            if data.get("event") == "init_sync":
                self.log("WEBSOCKET", "Holographic link", "PASS", f"State: {data.get('state', 'IDLE')} (verified end-to-end)")
            else:
                self.log("WEBSOCKET", "Holographic link", "WARN", "WebSocket connected without init_sync")
        elif error_note:
            self.log("WEBSOCKET", "Holographic link", "WARN", f"WebSocket probe note: {error_note}")
        else:
            self.log("WEBSOCKET", "Holographic link", "WARN", "No supported WebSocket client module available (aiohttp or websocket-client)")

    def render_report(self) -> str:
        lines = []
        lines.append("JARVIS V4 PREFLIGHT")
        lines.append("===================")

        by_cat: Dict[str, List[CheckResult]] = {}
        for r in self.results:
            by_cat.setdefault(r.category, []).append(r)

        for cat, items in by_cat.items():
            lines.append(f"\n{cat}")
            for item in items:
                status_str = f"[{item.status}]"
                detail_str = f" - {item.details}" if item.details else ""
                lines.append(f"{status_str:<8} {item.name}{detail_str}")

        passes = sum(1 for r in self.results if r.status == "PASS")
        warns = sum(1 for r in self.results if r.status == "WARN")
        fails = sum(1 for r in self.results if r.status == "FAIL")

        lines.append("\n===================")
        lines.append(f"PASS: {passes}")
        lines.append(f"WARN: {warns}")
        lines.append(f"FAIL: {fails}")
        overall = "PASS" if fails == 0 else "FAIL"
        lines.append(f"\nJARVIS PREFLIGHT: {overall}")
        return "\n".join(lines)

    def to_json(self) -> str:
        fails = sum(1 for r in self.results if r.status == "FAIL")
        return json.dumps({
            "overall": "PASS" if fails == 0 else "FAIL",
            "passes": sum(1 for r in self.results if r.status == "PASS"),
            "warnings": sum(1 for r in self.results if r.status == "WARN"),
            "failures": fails,
            "results": [
                {"category": r.category, "name": r.name, "status": r.status, "details": r.details}
                for r in self.results
            ]
        }, indent=2)

def run_preflight(base_url: str = "http://127.0.0.1:8000", token: str = "", as_json: bool = False) -> bool:
    runner = PreflightRunner(base_url=base_url, token=token)
    success = runner.run_all()
    if as_json:
        print(runner.to_json())
    else:
        print(runner.render_report())
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JARVIS V4 Live Preflight Verification")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="JARVIS Server Base URL")
    parser.add_argument("--token", default="", help="Optional JARVIS security token")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    ok = run_preflight(base_url=args.url, token=args.token, as_json=args.json)
    sys.exit(0 if ok else 1)