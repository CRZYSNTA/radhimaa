"""
JARVIS V3.0 - Mobile Pairing Manager
Generates pairing QR codes, prints ASCII terminal codes, saves high-res QR images,
and manages paired devices for remote mobile PC control.
"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from core.mobile_bridge import (
    generate_pairing_session,
    get_current_pairing_status,
    verify_pairing_pin,
    get_network_ips
)
from memory.database import get_paired_devices, revoke_device

logger = logging.getLogger("JARVIS.Tools.Pairing")

def generate_pairing_qr_image(url: str, output_path: str) -> bool:
    """Renders a high-resolution QR code image using qrcode library."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#001428", back_color="#ffffff")
        img.save(output_path)
        return True
    except Exception as e:
        logger.warning(f"Unable to generate QR image: {e}")
        return False

def print_terminal_qr(url: str):
    """Prints a scannable ASCII QR code directly to the terminal."""
    try:
        import qrcode
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.print_ascii(invert=True)
    except Exception:
        pass

def pair_mobile() -> str:
    """
    JARVIS Tool: Initiates a mobile pairing session, creates a 6-digit PIN and QR code,
    and returns instructions with local URLs.
    """
    session = generate_pairing_session(ttl_seconds=600)
    pin = session["pin"]
    url = session["url"]
    primary_ip = session["primary_ip"]

    # Save QR code to desktop and local project directory
    qr_project_file = Path(__file__).resolve().parent.parent / "pairing_qr.png"
    desktop_qr = Path.home() / "OneDrive" / "Desktop" / "pairing_qr.png"
    if not desktop_qr.parent.exists():
        desktop_qr = Path.home() / "Desktop" / "pairing_qr.png"

    generate_pairing_qr_image(url, str(qr_project_file))
    if desktop_qr.parent.exists():
        generate_pairing_qr_image(url, str(desktop_qr))

    msg = (
        f"Mobile pairing session initialized, sir.\n"
        f"PIN: {pin} (valid for 10 minutes)\n"
        f"Mobile App URL: {url}\n"
        f"Local IP: {primary_ip}:8000\n"
        f"A scannable QR Code has been saved to your Desktop: pairing_qr.png"
    )
    return msg

def list_paired_devices() -> str:
    """Lists all active and revoked mobile devices."""
    devices = get_paired_devices()
    if not devices:
        return "No mobile devices are currently paired with JARVIS."
    
    lines = ["Registered Mobile Devices:"]
    for d in devices:
        status = "Active" if d.get("is_active") else "Revoked"
        lines.append(f"- {d.get('device_name')} (ID: {d.get('device_id')}) [{status}]")
    return "\n".join(lines)

def revoke_mobile_device(device_id: str) -> str:
    """Revokes access for a specific mobile device."""
    ok = revoke_device(device_id)
    if ok:
        return f"Successfully revoked mobile device {device_id}."
    return f"Device {device_id} not found or already revoked."

if __name__ == "__main__":
    print("==================================================")
    print("      JARVIS V3.0 - MOBILE DEVICE PAIRING         ")
    print("==================================================")
    session = generate_pairing_session()
    pin = session["pin"]
    url = session["url"]
    
    print(f"\n[+] 6-DIGIT PAIRING PIN:  >>> {pin} <<<")
    print(f"[+] MOBILE APP URL:       {url}")
    print("\n[+] NETWORK INTERFACES:")
    for iface in session["interfaces"]:
        print(f"    - {iface['type']:<24}: http://{iface['ip']}:8000/app?pin={pin}")

    print("\n[+] TERMINAL SCANNABLE QR CODE (Point phone camera here):")
    print_terminal_qr(url)

    desktop_qr = Path.home() / "OneDrive" / "Desktop" / "pairing_qr.png"
    if not desktop_qr.parent.exists():
        desktop_qr = Path.home() / "Desktop" / "pairing_qr.png"
    generate_pairing_qr_image(url, str(desktop_qr))
    print(f"\n[+] QR Code image saved to: {desktop_qr}")
    print("==================================================")
