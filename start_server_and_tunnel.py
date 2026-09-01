"""
=============================================================================
JARVIS Server & Public Tunnel Launcher (Terminal Mode)
=============================================================================
Goal: Starts JARVIS server on port 8000 + Cloudflare Public HTTPS Tunnel
      and displays your public URL clearly in the terminal window.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import threading
import time
import uvicorn
import server
import tunnel_manager

def run_uvicorn():
    uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="error")

def main():
    print("==========================================================")
    print("   [START] STARTING JARVIS BACKEND & PUBLIC TUNNEL...")
    print("==========================================================")
    
    # 1. Start Server Thread
    server_thread = threading.Thread(target=run_uvicorn, daemon=True)
    server_thread.start()
    time.sleep(1)

    # 2. Start Public HTTPS Tunnel
    tunnel = tunnel_manager.PublicTunnel(8000)
    public_url = tunnel.start()

    if public_url:
        print("\n==========================================================")
        print("[OK] JARVIS IS LIVE & ONLINE WORLDWIDE!")
        print(f" - Public HTTPS URL:     {public_url}")
        print(f" - iOS Shortcut URL:     {public_url}/ask")
        print(f" - Health Check URL:     {public_url}/health")
        print(f" - Local Web Console:    http://localhost:8000")
        print("==========================================================")
        print("[NOTE] Copy the 'iOS Shortcut URL' above into your iPhone Shortcut!")
        print("JARVIS server active in background. Press Ctrl+C to stop.\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down JARVIS server...")
            tunnel.stop()
    else:
        print("[ERROR] Could not generate public URL. Local access available at http://localhost:8000")

if __name__ == "__main__":
    main()
