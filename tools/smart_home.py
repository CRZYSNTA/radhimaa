"""
JARVIS V3.0 - Smart Home & IoT Automation Tools
Integrates with local network smart plugs, smart switches, and smart bulbs
(e.g., TP-Link Kasa) with zero external cloud dependencies.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JARVIS.Tools.SmartHome")

def discover_smart_devices() -> str:
    """
    Discovers smart plugs and lights connected to the local Wi-Fi network.
    """
    try:
        from kasa import Discover

        async def _find():
            return await Discover.discover()

        devices = asyncio.run(_find())
        if not devices:
            return "No smart home devices responded on your local Wi-Fi subnet, sir."

        lines = [f"Discovered {len(devices)} smart device(s):"]
        for ip, dev in devices.items():
            lines.append(f"- **{dev.alias}** ({dev.model}) at `{ip}`: State is {'ON' if dev.is_on else 'OFF'}")
        return "\n".join(lines)

    except ImportError:
        return "Smart Home module is not installed. Install 'python-kasa' to enable local smart device control."
    except Exception as e:
        logger.error(f"[SmartHome Discovery Error]: {e}")
        return f"Smart home discovery failed: {e}"

def control_smart_plug(device_alias: str, state: str = "on") -> str:
    """
    Toggles a smart plug on or off.
    Args:
        device_alias: The named alias of the plug (e.g. 'Desk Lamp', 'Charger').
        state: 'on' or 'off'.
    """
    turn_on = state.lower().strip() in ("on", "true", "1", "enable")

    try:
        from kasa import Discover

        async def _set_state():
            devices = await Discover.discover()
            target = None
            for dev in devices.values():
                if device_alias.lower() in dev.alias.lower():
                    target = dev
                    break
            if not target:
                return None
            if turn_on:
                await target.turn_on()
            else:
                await target.turn_off()
            return target.alias

        matched = asyncio.run(_set_state())
        if matched:
            return f"Smart plug '{matched}' turned {'ON' if turn_on else 'OFF'}, sir."
        return f"Could not locate smart device matching '{device_alias}' on the network."

    except ImportError:
        return "Smart Home module not installed."
    except Exception as e:
        logger.error(f"[SmartPlug Control Error]: {e}")
        return f"Failed to control smart plug: {e}"

def control_smart_bulb(device_alias: str, state: str = "on", brightness: Optional[int] = None) -> str:
    """
    Controls smart light bulb power and brightness.
    Args:
        device_alias: The name/alias of the bulb (e.g. 'Living Room Light').
        state: 'on' or 'off'.
        brightness: Optional level from 1 to 100.
    """
    turn_on = state.lower().strip() in ("on", "true", "1", "enable")

    try:
        from kasa import Discover

        async def _set_bulb():
            devices = await Discover.discover()
            target = None
            for dev in devices.values():
                if device_alias.lower() in dev.alias.lower() and dev.is_bulb:
                    target = dev
                    break
            if not target:
                return None
            if turn_on:
                await target.turn_on()
                if brightness is not None:
                    b_val = max(1, min(int(brightness), 100))
                    await target.set_brightness(b_val)
            else:
                await target.turn_off()
            return target.alias

        matched = asyncio.run(_set_bulb())
        if matched:
            b_str = f" at {brightness}% brightness" if brightness and turn_on else ""
            return f"Smart light '{matched}' turned {'ON' if turn_on else 'OFF'}{b_str}, sir."
        return f"Could not locate smart light matching '{device_alias}' on the network."

    except ImportError:
        return "Smart Home module not installed."
    except Exception as e:
        logger.error(f"[SmartBulb Control Error]: {e}")
        return f"Failed to control smart bulb: {e}"
