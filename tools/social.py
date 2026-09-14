"""
JARVIS V3.0 - Social & Communication Tools
Provides messaging automation for WhatsApp Desktop and Instagram Direct Messages.
"""

from __future__ import annotations

import re
import urllib.parse
import webbrowser
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("JARVIS.Tools.Social")

def send_whatsapp_message(recipient: str, message: str) -> str:
    """
    Launches WhatsApp with a pre-filled message to a recipient phone number or contact.
    Args:
        recipient: Phone number (e.g. '+1234567890') or contact name.
        message: The text message to send.
    """
    if not recipient or not message:
        return "Recipient and message must both be provided, sir."

    try:
        clean_num = re.sub(r"[^\d+]", "", recipient)
        encoded_msg = urllib.parse.quote(message)

        # If clean phone number is provided, use direct API link
        if len(clean_num) >= 7:
            # WhatsApp desktop deep link
            url = f"whatsapp://send?phone={clean_num}&text={encoded_msg}"
        else:
            # Fallback search
            url = f"whatsapp://send?text={encoded_msg}"

        webbrowser.open(url)
        logger.info(f"[Social] Dispatched WhatsApp message to {recipient}")
        return f"Opening WhatsApp with message drafted for {recipient}, sir."

    except Exception as e:
        logger.error(f"[WhatsApp Error]: {e}")
        return f"Unable to dispatch WhatsApp message: {e}"

def check_instagram_dms(username: Optional[str] = None, password: Optional[str] = None) -> str:
    """
    Checks recent unread Instagram Direct Messages.
    Credentials can be passed directly or read from environment / config.
    """
    try:
        import os
        from instagrapi import Client

        user = username or os.environ.get("INSTAGRAM_USERNAME", "")
        pwd = password or os.environ.get("INSTAGRAM_PASSWORD", "")

        if not user or not pwd:
            return "Instagram credentials not configured. Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in config, sir."

        cl = Client()
        cl.login(user, pwd)
        threads = cl.direct_threads(amount=5)

        if not threads:
            return "No recent Instagram direct message threads found, sir."

        lines = ["Recent Instagram Direct Messages:"]
        for t in threads:
            sender = t.users[0].username if t.users else "Unknown"
            last_msg = t.messages[0].text if t.messages else "(Media/No text)"
            lines.append(f"- **@{sender}**: {last_msg}")

        return "\n".join(lines)

    except ImportError:
        return "Instagram client module not installed. Install 'instagrapi' to enable Instagram integration."
    except Exception as e:
        logger.error(f"[Instagram Check Error]: {e}")
        return f"Failed to check Instagram DMs: {e}"

def reply_instagram_dm(thread_id: str, message: str) -> str:
    """
    Sends a direct message reply to an Instagram thread.
    """
    try:
        import os
        from instagrapi import Client

        user = os.environ.get("INSTAGRAM_USERNAME", "")
        pwd = os.environ.get("INSTAGRAM_PASSWORD", "")

        if not user or not pwd:
            return "Instagram credentials not configured, sir."

        cl = Client()
        cl.login(user, pwd)
        cl.direct_send(message, thread_ids=[thread_id])
        return f"Direct message successfully sent to thread {thread_id}, sir."

    except ImportError:
        return "Instagram client module not installed."
    except Exception as e:
        logger.error(f"[Instagram Reply Error]: {e}")
        return f"Failed to reply to Instagram DM: {e}"
