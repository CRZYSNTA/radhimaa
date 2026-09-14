"""
JARVIS V3.0 - System Monitoring Tools
Collects real-time hardware telemetry: CPU, RAM, Disk, Battery, and OS info.
"""

import os
import psutil
from typing import Dict, Any

def get_cpu_percent() -> float:
    """Returns overall CPU usage percentage."""
    return psutil.cpu_percent(interval=0.1)

def get_ram_percent() -> float:
    """Returns memory usage percentage."""
    return psutil.virtual_memory().percent

def get_battery_status() -> Dict[str, Any]:
    """Returns battery percentage, power plug status, and time remaining."""
    battery = psutil.sensors_battery()
    if battery is None:
        return {"percent": 100, "power_plugged": True, "secsleft": -1, "status": "Desktop / No Battery"}
    return {
        "percent": battery.percent,
        "power_plugged": battery.power_plugged,
        "secsleft": battery.secsleft,
        "status": "Charging" if battery.power_plugged else "On Battery"
    }

def get_system_stats() -> Dict[str, Any]:
    """Returns unified hardware telemetry snapshot."""
    cpu = get_cpu_percent()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = get_battery_status()

    return {
        "cpu_percent": cpu,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / (1024**3), 2),
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "battery": battery,
    }

def format_system_report() -> str:
    """Returns user-friendly string of system telemetry."""
    stats = get_system_stats()
    bat = stats["battery"]
    plug_text = "Plugged in" if bat["power_plugged"] else "Discharging"
    return (
        f"System Status:\n"
        f"• CPU Usage: {stats['cpu_percent']}%\n"
        f"• RAM Usage: {stats['ram_percent']}% ({stats['ram_used_gb']}GB / {stats['ram_total_gb']}GB)\n"
        f"• Disk Usage: {stats['disk_percent']}% ({stats['disk_free_gb']}GB Free)\n"
        f"• Battery: {bat['percent']}% ({plug_text})"
    )
