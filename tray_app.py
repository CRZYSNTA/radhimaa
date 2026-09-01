"""
=============================================================================
JARVIS System Tray & Full Voice / Clap Engine Launcher (Robust Port Handling)
=============================================================================
Goal: Starts all JARVIS subsystems gracefully:
 - Handles port 8000 seamlessly if server is already active
 - Launches Native Siri/Arc Reactor Orb Overlay (jarvis_overlay.py)
 - Runs Voice ("Jarvis") + Sensitive Double-Clap Listener

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
import requests
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import uvicorn

import server
import tunnel_manager
import clap_wake_engine

def create_jarvis_icon():
    width = 64
    height = 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    draw.ellipse((4, 4, width - 4, height - 4), outline=(56, 189, 248, 255), width=4)
    draw.ellipse((18, 18, width - 18, height - 18), fill=(2, 132, 199, 255))
    draw.ellipse((26, 26, width - 26, height - 26), fill=(255, 255, 255, 255))
    return image

public_tunnel_obj = None
public_url_str = None
overlay_process = None

def is_server_running():
    """Checks if JARVIS backend server is already active on port 8000."""
    try:
        res = requests.get("http://localhost:8000/health", timeout=1)
        return res.status_code == 200
    except Exception:
        return False

def run_server_safely():
    """Starts Uvicorn server, catching port-in-use errors gracefully."""
    if not is_server_running():
        try:
            uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="error")
        except Exception as e:
            print(f"[Server Launch Note]: {e}")

def start_services():
    global public_tunnel_obj, public_url_str, overlay_process

    # 1. Start FastAPI server thread (if not already running)
    server_thread = threading.Thread(target=run_server_safely, daemon=True)
    server_thread.start()

    # 2. Start Dual Trigger Voice ("Jarvis") & Sensitive Double-Clap Listener Thread
    try:
        dual_engine = clap_wake_engine.DualTriggerEngine(clap_threshold=1200)
        voice_thread = threading.Thread(target=dual_engine.start, daemon=True)
        voice_thread.start()
        print("[OK] Voice ('Jarvis') & Double-Clap Listener Active!")
    except Exception as e:
        print(f"[Voice Engine Note]: {e}")

    # 3. Start Cloudflare Tunnel
    time.sleep(1)
    try:
        public_tunnel_obj = tunnel_manager.PublicTunnel(8000)
        public_url_str = public_tunnel_obj.start()
    except Exception as e:
        print(f"[Tunnel Note]: {e}")

    # 4. Launch Native Python Siri/Arc Reactor Glowing Orb Overlay Widget
    try:
        overlay_script = os.path.join(os.path.dirname(__file__), "jarvis_overlay.py")
        pythonw_bin = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw_bin):
            pythonw_bin = sys.executable
        overlay_process = subprocess.Popen([pythonw_bin, overlay_script])
    except Exception as e:
        print(f"[Overlay Launch Error]: {e}")

def open_dashboard(icon, item):
    target_url = public_url_str if public_url_str else "http://localhost:8000"
    webbrowser.open(target_url)

def copy_public_url(icon, item):
    if public_url_str:
        try:
            import pyperclip
            pyperclip.copy(f"{public_url_str}/ask")
            icon.notify(f"Copied endpoint: {public_url_str}/ask", title="[OK] URL Copied!")
        except Exception:
            icon.notify(f"Endpoint: {public_url_str}/ask", title="[INFO] Public Endpoint")

def show_status(icon, item):
    if public_url_str:
        icon.notify(f"JARVIS Active!\nPublic Endpoint: {public_url_str}/ask", title="🤖 JARVIS Active")
    else:
        icon.notify("JARVIS Server is running online at http://localhost:8000", title="🤖 JARVIS Active")

def quit_app(icon, item):
    global public_tunnel_obj, overlay_process
    if overlay_process:
        try:
            overlay_process.terminate()
        except Exception:
            pass
    if public_tunnel_obj:
        public_tunnel_obj.stop()
    icon.stop()
    sys.exit(0)

def main():
    bg_thread = threading.Thread(target=start_services, daemon=True)
    bg_thread.start()

    icon_image = create_jarvis_icon()

    menu = pystray.Menu(
        item('🤖 JARVIS Status', show_status),
        item('🌐 Open Web Console', open_dashboard),
        item('📋 Copy Public HTTPS URL', copy_public_url),
        pystray.Menu.SEPARATOR,
        item('🛑 Quit JARVIS', quit_app)
    )

    icon = pystray.Icon("JARVIS_System_Tray", icon_image, "JARVIS Personal Assistant", menu)
    icon.run()

if __name__ == "__main__":
    main()
