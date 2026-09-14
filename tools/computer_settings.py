"""
JARVIS V3.0 - Windows Computer & Environment Settings Tools
Native Windows settings controls for display brightness, dark/light themes,
Wi-Fi, Bluetooth, and audio output configuration.
"""

from __future__ import annotations

import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("JARVIS.Tools.Settings")

def set_brightness(level: int) -> str:
    """
    Sets laptop/monitor screen brightness with ultra-fast multi-engine fallback:
    1. screen_brightness_control (direct C-level / DDC-CI / WMI in <15ms)
    2. Direct WMI via wmi package (in-process)
    3. PowerShell WmiSetBrightness (external process fallback)
    """
    try:
        level = max(0, min(int(level), 100))

        # 1. Primary: screen_brightness_control
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(level)
            logger.info(f"[Settings] Brightness set to {level}% via sbc")
            return f"Display brightness set to {level}%, sir."
        except Exception as err:
            logger.debug(f"[Settings] sbc fallback: {err}")

        # 2. Secondary: WMI via wmi package
        try:
            import wmi
            w = wmi.WMI(namespace="wmi")
            methods = w.WmiMonitorBrightnessMethods()
            if methods:
                for m in methods:
                    m.WmiSetBrightness(1, level)
                logger.info(f"[Settings] Brightness set to {level}% via wmi COM")
                return f"Display brightness set to {level}%, sir."
        except Exception as err:
            logger.debug(f"[Settings] wmi COM fallback: {err}")

        # 3. Tertiary: PowerShell WMI call
        cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=10)
        logger.info(f"[Settings] Brightness adjusted to {level}% via PowerShell")
        return f"Display brightness set to {level}%, sir."
    except Exception as e:
        logger.error(f"[Settings Brightness Error]: {e}")
        return f"Unable to adjust display brightness: {e}"

def get_brightness() -> Optional[int]:
    """
    Returns current display brightness level (0-100) or None if unavailable.
    """
    try:
        import screen_brightness_control as sbc
        vals = sbc.get_brightness()
        if vals:
            if isinstance(vals, list):
                return int(vals[0])
            return int(vals)
    except Exception:
        pass

    try:
        import wmi
        w = wmi.WMI(namespace="wmi")
        monitors = w.WmiMonitorBrightness()
        if monitors:
            return int(monitors[0].CurrentBrightness)
    except Exception:
        pass

    return None

def toggle_dark_mode(enabled: bool = True) -> str:
    """
    Toggles Windows 10/11 system and app theme between Dark and Light mode.
    Args:
        enabled: True for Dark Mode, False for Light Mode.
    """
    try:
        val = 0 if enabled else 1
        theme_name = "Dark" if enabled else "Light"
        reg_cmd = (
            f"Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name 'AppsUseLightTheme' -Value {val}; "
            f"Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name 'SystemUsesLightTheme' -Value {val}"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", reg_cmd], capture_output=True, timeout=5)
        logger.info(f"[Settings] Windows theme switched to {theme_name} mode")
        return f"Windows interface switched to {theme_name} mode, sir."
    except Exception as e:
        logger.error(f"[Settings DarkMode Error]: {e}")
        return f"Unable to switch Windows theme: {e}"

def toggle_wifi(state: str = "enable") -> str:
    """
    Toggles Wi-Fi network adapter.
    Args:
        state: 'enable'/'on' or 'disable'/'off'
    """
    try:
        admin_state = "ENABLED" if state.lower() in ("enable", "on", "true", "1") else "DISABLED"
        cmd = f"netsh interface set interface name=\"Wi-Fi\" admin={admin_state}"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8)
        if res.returncode == 0:
            return f"Wi-Fi adapter has been {admin_state.lower()}d, sir."
        return f"Wi-Fi toggle executed: {res.stdout or res.stderr or 'Completed'}"
    except Exception as e:
        logger.error(f"[Settings WiFi Error]: {e}")
        return f"Unable to toggle Wi-Fi: {e}"

def toggle_bluetooth(state: str = "enable") -> str:
    """
    Toggles Bluetooth radio adapter.
    Args:
        state: 'enable'/'on' or 'disable'/'off'
    """
    try:
        desired = "On" if state.lower() in ("enable", "on", "true", "1") else "Off"
        ps_script = f"""
        [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
        [Windows.Devices.Radios.Radio]::RequestAccessAsync().AsTask().Wait()
        $radios = [Windows.Devices.Radios.Radio]::GetRadiosAsync().AsTask().Result
        $bt = $radios | Where-Object {{ $_.Kind -eq 'Bluetooth' }}
        if ($bt) {{
            $bt.SetStateAsync('{desired}').AsTask().Wait()
            Write-Output "Bluetooth turned {desired}"
        }} else {{
            Write-Output "No Bluetooth adapter detected"
        }}
        """
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=8)
        out = res.stdout.strip() or f"Bluetooth state set to {desired}"
        return f"{out}, sir."
    except Exception as e:
        logger.error(f"[Settings Bluetooth Error]: {e}")
        return f"Unable to configure Bluetooth: {e}"

def get_system_settings() -> Dict[str, Any]:
    """
    Retrieves current desktop display, theme, and battery status.
    """
    settings: Dict[str, Any] = {}
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            settings["battery_percent"] = battery.percent
            settings["power_plugged"] = battery.power_plugged
    except Exception:
        pass

    try:
        import pyautogui
        w, h = pyautogui.size()
        settings["display_resolution"] = f"{w}x{h}"
    except Exception:
        pass

    try:
        reg_check = "Get-ItemPropertyValue -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name 'AppsUseLightTheme'"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", reg_check], capture_output=True, text=True, timeout=4)
        if res.stdout.strip() == "0":
            settings["theme"] = "Dark"
        elif res.stdout.strip() == "1":
            settings["theme"] = "Light"
    except Exception:
        pass

    return settings
