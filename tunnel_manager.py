"""
=============================================================================
JARVIS Public HTTPS Tunnel Manager (Non-Blocking Timeout Fixed)
=============================================================================
Goal: Exposes local JARVIS server to a public HTTPS URL (e.g. https://xxx.trycloudflare.com)
      without blocking or hanging on process output streams.

Fixes Applied:
 - [P1 Fix]: Non-blocking Queue reader thread for stderr prevent hangs.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import queue
import re
import subprocess
import threading
import time
import urllib.request

CLOUDFLARED_PATH = os.path.join(os.path.dirname(__file__), "cloudflared.exe")
CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

def ensure_cloudflared_exists():
    if not os.path.exists(CLOUDFLARED_PATH):
        print("[INFO] Downloading Cloudflare Tunnel binary (54 MB)...")
        try:
            urllib.request.urlretrieve(CLOUDFLARED_URL, CLOUDFLARED_PATH)
            print("[OK] Cloudflared binary downloaded!")
        except Exception as e:
            print(f"[ERROR] Failed to download cloudflared: {e}")

class PublicTunnel:
    def __init__(self, target_port=8000):
        self.target_port = target_port
        self.process = None
        self.public_url = None

    def start(self, timeout_seconds=15):
        """Starts Cloudflare Tunnel process and extracts the public HTTPS URL safely."""
        ensure_cloudflared_exists()
        if not os.path.exists(CLOUDFLARED_PATH):
            return None

        cmd = [CLOUDFLARED_PATH, "tunnel", "--url", f"http://localhost:{self.target_port}"]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="ignore"
            )
        except Exception as e:
            print(f"[Tunnel Launch Error]: {e}")
            return None

        # Threaded Queue reader to prevent readline() hanging
        output_queue = queue.Queue()

        def reader_thread(pipe, q):
            try:
                for line in iter(pipe.readline, ''):
                    q.put(line)
                pipe.close()
            except Exception:
                pass

        t = threading.Thread(target=reader_thread, args=(self.process.stderr, output_queue), daemon=True)
        t.start()

        print("[TUNNEL] Creating Public HTTPS Tunnel...")
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            try:
                line = output_queue.get(timeout=0.2)
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    self.public_url = match.group(0)
                    print("==========================================================")
                    print("[OK] PUBLIC HTTPS URL CREATED SUCCESSFULLY!")
                    print(f" - Public Domain: {self.public_url}")
                    print(f" - iOS Shortcut Endpoint: {self.public_url}/ask")
                    print("==========================================================")
                    return self.public_url
            except queue.Empty:
                pass

            if self.process.poll() is not None:
                # Process exited unexpectedly
                print("[Tunnel Warning]: cloudflared process terminated early.")
                break

        print("[Tunnel Timeout]: Cloudflare tunnel initialization reached timeout.")
        return None

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass

if __name__ == "__main__":
    tunnel = PublicTunnel(8000)
    url = tunnel.start()
    if url:
        print(f"[SUCCESS] Endpoint: {url}/health")
        time.sleep(3)
        tunnel.stop()
