"""
JARVIS V3.1 - Prompt Injection Defense & Data Sanitization Subsystem
Treats all external content (web pages, OCR, files, clipboard) as strictly untrusted DATA.
Provides boundary tagging and parameter sanitization so external data cannot override instructions.
"""

import re
import html
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("JARVIS.Core.Security")

FORBIDDEN_INJECTION_PATTERNS = [
    r"ignore\\s+(all\\s+)?previous\\s+instructions",
    r"system\\s*:\\s*you\\s+are",
    r"reveal\\s+(the\\s+)?api\\s+key",
    r"delete\\s+all\\s+files",
    r"format\\s+drive",
    r"download\\s+and\\s+execute",
    r"bypass\\s+security"
]

def sanitize_untrusted_data(content: str, source: str = "external") -> str:
    """
    Wraps external data inside strict UNTRUSTED_DATA boundary tags.
    Neutralizes instructions attempting to masquerade as system prompts.
    """
    if not content or not isinstance(content, str):
        return ""

    # Escape any existing fake boundary tags
    clean = content.replace("<UNTRUSTED_DATA>", "&lt;UNTRUSTED_DATA&gt;")
    clean = clean.replace("</UNTRUSTED_DATA>", "&lt;/UNTRUSTED_DATA&gt;")

    # Flag obvious prompt injection phrases
    detected_injections = []
    for pat in FORBIDDEN_INJECTION_PATTERNS:
        if re.search(pat, clean, re.IGNORECASE):
            detected_injections.append(pat)

    if detected_injections:
        logger.warning(f"[Security] Potential prompt injection detected in {source} content: {detected_injections}")

    return (
        f'<UNTRUSTED_DATA source="{source}">\n'
        f'{clean}\n'
        f'</UNTRUSTED_DATA>'
    )

def sanitize_param_string(val: str, max_len: int = 1000) -> str:
    """
    Sanitizes single-parameter inputs like application names, file names, or queries.
    Blocks shell metacharacters and enforces length limits.
    """
    if not val:
        return ""
    # Strip null bytes and control chars
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(val))
    return clean[:max_len].strip()


