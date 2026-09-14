"""
JARVIS V4 - Typed Configuration Settings
Replaces scattered globals with typed settings groups and explicit environment validation.
Secrets are isolated and sourced from environment / config.json securely.
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


def _load_raw_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


_RAW = _load_raw_config()


@dataclass
class AISettings:
    provider: str = field(default_factory=lambda: os.getenv("AI_PROVIDER", _RAW.get("AI_PROVIDER", "gemini")).lower())
    default_model: str = field(default_factory=lambda: os.getenv("DEFAULT_MODEL", _RAW.get("DEFAULT_MODEL", "gemini-flash-latest")))
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", _RAW.get("GEMINI_API_KEY")))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", _RAW.get("OPENAI_API_KEY")))
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", _RAW.get("OLLAMA_URL", "http://localhost:11434/api/generate")))
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class DatabaseSettings:
    db_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_memory.db"))
    wal_mode: bool = True
    timeout: float = 10.0


@dataclass
class SecuritySettings:
    auth_token: Optional[str] = field(default_factory=lambda: os.getenv("JARVIS_AUTH_TOKEN", _RAW.get("AUTH_TOKEN")))
    rate_limit_per_minute: int = 60
    max_message_length: int = 4000
    allow_loopback_without_token: bool = True


@dataclass
class VoiceSettings:
    default_voice: str = field(default_factory=lambda: _RAW.get("JARVIS_VOICE", "en-GB-RyanNeural"))
    rate: str = "+0%"
    pitch: str = "+0Hz"
    push_to_talk_key: str = "home"


@dataclass
class StorageSettings:
    workspace_dir: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(__file__)))
    sandbox_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(__file__)), "sandbox"))
    vault_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(__file__)), "vault"))


@dataclass
class ObservabilitySettings:
    log_level: str = "INFO"
    enable_audit_logging: bool = True
    log_file: Optional[str] = None


@dataclass
class AppSettings:
    ai: AISettings = field(default_factory=AISettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    observability: ObservabilitySettings = field(default_factory=ObservabilitySettings)


_settings_instance: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Returns the singleton typed AppSettings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AppSettings()
    return _settings_instance
