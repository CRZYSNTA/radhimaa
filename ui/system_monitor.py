"""
JARVIS V3.0 - UI System Monitor Thread
Periodically samples CPU, RAM, and Battery levels to update UI displays.
"""

import time
import threading
import psutil
from typing import Callable, Optional

class SystemMonitorThread:
    """Runs a background polling loop for system hardware stats."""
    def __init__(self, update_callback: Callable[[float, float, str], None], interval: float = 1.5):
        self.update_callback = update_callback
        self.interval = interval
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=0.2)
                ram = psutil.virtual_memory().percent
                bat = psutil.sensors_battery()
                if bat is not None:
                    bat_str = f"{bat.percent}%" + (" ⚡" if bat.power_plugged else "")
                else:
                    bat_str = "AC"

                if self.update_callback:
                    self.update_callback(cpu, ram, bat_str)
                time.sleep(self.interval)
            except Exception:
                time.sleep(self.interval)
