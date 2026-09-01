"""
=============================================================================
JARVIS Personal Assistant App Launcher (Robust Exception Logging)
=============================================================================
Fixes Applied:
 - [P2 Fix]: Explicit logging and graceful degradation reporting on launch failure.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import sys
import threading
import time
import uvicorn

import server
import tunnel_manager
import clap_wake_engine
import jarvis_overlay

def is_server_running():
    try:
        import requests
        res = requests.get("http://localhost:8000/health", timeout=1)
        return res.status_code == 200
    except Exception:
        return False

def run_server_safely():
    if not is_server_running():
        try:
            uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="error")
        except Exception as e:
            # [P2 Fix]: Log explicit failure instead of silently dropping
            print(f"[ERROR] FastAPI Server failed to bind or launch: {e}")

def start_background_services():
    # 1. Start Server
    threading.Thread(target=run_server_safely, daemon=True).start()

    # 2. Start Dual Trigger Voice & Clap Listener
    try:
        engine = clap_wake_engine.DualTriggerEngine(clap_threshold=1200)
        threading.Thread(target=engine.start, daemon=True).start()
    except Exception as e:
        print(f"[ERROR] Dual Trigger Voice/Clap Engine failed to launch: {e}")

    # 3. Start Public Tunnel
    try:
        tunnel = tunnel_manager.PublicTunnel(8000)
        threading.Thread(target=tunnel.start, daemon=True).start()
    except Exception as e:
        print(f"[ERROR] Cloudflare Tunnel failed to launch: {e}")

def main():
    print("==========================================================")
    print("[START] LAUNCHING JARVIS ASSISTANT SYSTEM...")
    print("==========================================================")

    start_background_services()
    time.sleep(1)

    try:
        app = jarvis_overlay.SiriWidgetOverlay()
        app.run()
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to launch UI overlay: {e}")

if __name__ == "__main__":
    main()
