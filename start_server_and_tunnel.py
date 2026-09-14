"""
JARVIS V3.0 - Worldwide Online Server & Public HTTPS Tunnel Launcher
Starts the JARVIS Central Server on port 8000, establishes a secure, zero-config
Cloudflare HTTPS Tunnel, generates an active pairing PIN and QR code,
and exposes the Web Companion and Living Visualizer worldwide.
"""

import os
import sys
import time
import threading
import uvicorn
from pathlib import Path

import server
import tunnel_manager
from core.mobile_bridge import generate_pairing_session
from tools.pairing_manager import generate_pairing_qr_image, print_terminal_qr


def clean_lingering_instances(port: int = 8000):
    """Terminates any previous server instances holding port 8000."""
    try:
        import psutil
        curr_pid = os.getpid()
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr and conn.laddr.port == port and conn.pid and conn.pid != curr_pid:
                try:
                    p = psutil.Process(conn.pid)
                    p.kill()
                except Exception:
                    pass
    except Exception:
        pass

def run_uvicorn():
    uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="warning")


def main():
    print("\n" + "=" * 62)
    print("      JARVIS V3.0 - LAUNCHING WORLDWIDE ONLINE SERVER")
    print("=" * 62)

    # 0. Clean any previous lingering instance
    clean_lingering_instances(8000)

    # 1. Start Server Thread
    server_thread = threading.Thread(target=run_uvicorn, daemon=True, name="JarvisFastAPIServer")
    server_thread.start()
    time.sleep(1.2)

    # 2. Start Cloudflare Tunnel
    tunnel = tunnel_manager.PublicTunnel(8000)
    public_url = tunnel.start(timeout_seconds=25)

    if public_url:
        # 3. Generate active mobile pairing session
        session = generate_pairing_session(ttl_seconds=3600)
        pin = session["pin"]
        mobile_app_url = f"{public_url}/app?pin={pin}"
        visualizer_url = f"{public_url}/visualizer"

        # 4. Save QR Image to Desktop
        desktop_dir = Path.home() / "OneDrive" / "Desktop"
        if not desktop_dir.exists():
            desktop_dir = Path.home() / "Desktop"
        qr_output_path = str(desktop_dir / "pairing_qr.png")
        generate_pairing_qr_image(mobile_app_url, qr_output_path)

        print("\n" + "=" * 62)
        print("  ⚡ JARVIS IS NOW LIVE ONLINE WORLDWIDE (HTTPS / WSS)")
        print("=" * 62)
        print(f"  📱 Mobile Web Companion:  {mobile_app_url}")
        print(f"  ⚡ Living Circuit Board:   {visualizer_url}")
        print(f"  🍎 iOS Siri / Shortcut:    {public_url}/ask")
        print(f"  🔑 One-Time Pairing PIN:   {pin}")
        print(f"  🖼️  QR Code Image:          {qr_output_path}")
        print(f"  💻 Local Fallback:         http://localhost:8000/app")
        print("=" * 62 + "\n")

        print("Point your phone's camera at the QR code below to connect instantly:\n")
        try:
            print_terminal_qr(mobile_app_url)
        except Exception:
            pass

        print("\n[NOTE] Open the Mobile Web Companion link on your phone from ANY network.")
        print("Keep this terminal open while using JARVIS remotely. Press Ctrl+C to terminate.\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down online tunnel and JARVIS server...")
            tunnel.stop()
    else:
        print("\n[ERROR] Cloudflare tunnel failed to establish.")
        print("Local network access is still operational at: http://localhost:8000/app\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
