"""
JARVIS V3.0 - Centralized Configuration Manager
Loads configuration from environment variables, .env file, and config.json.
Provides type-safe, validated settings across the entire JARVIS system.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent
CONFIG_JSON_PATH = BASE_DIR / "config.json"
ENV_PATH = BASE_DIR / ".env"

def _load_env_file():
    """Simple .env parser without requiring external python-dotenv."""
    if ENV_PATH.exists():
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass

def _load_json_config() -> Dict[str, Any]:
    """Load config.json if present."""
    if CONFIG_JSON_PATH.exists():
        try:
            with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

_load_env_file()
_json_cfg = _load_json_config()

def get_setting(key: str, default: Any = "") -> Any:
    """Retrieve setting prioritizing ENV -> config.json -> default."""
    if key in os.environ and os.environ[key].strip() != "":
        return os.environ[key]
    if key in _json_cfg and _json_cfg[key] is not None and str(_json_cfg[key]).strip() != "":
        return _json_cfg[key]
    return default

# AI & LLM Settings
GEMINI_API_KEY: str = get_setting("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    try:
        bt_cfg_file = Path("d:/agent/backtalk/backtalk.json")
        if bt_cfg_file.exists():
            with open(bt_cfg_file, "r", encoding="utf-8") as f:
                GEMINI_API_KEY = json.load(f).get("gemini_api_key", "")
    except Exception:
        pass

OPENAI_API_KEY: str = get_setting("OPENAI_API_KEY", "")
OLLAMA_BASE_URL: str = get_setting("OLLAMA_BASE_URL", "http://localhost:11434")
AI_PROVIDER: str = get_setting("AI_PROVIDER", "gemini" if GEMINI_API_KEY else "ollama")
DEFAULT_MODEL: str = get_setting("DEFAULT_MODEL", "gemini-3.6-flash")

# Obsidian Memory Vault Settings (LEO Stack)
DAS_AND_CO_VAULT = Path("C:/Users/gowth/das and co")
VAULT_DIR: Path = DAS_AND_CO_VAULT if DAS_AND_CO_VAULT.exists() else (BASE_DIR / "vault")

# Voice & Speech Settings
JARVIS_VOICE: str = get_setting("JARVIS_VOICE", "en-GB-RyanNeural")
ELEVENLABS_VOICE_ID: str = get_setting("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
ELEVENLABS_MODEL: str = get_setting("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
FISH_AUDIO_API_KEY: str = get_setting("FISH_AUDIO_API_KEY", "")
FISH_AUDIO_VOICE_ID: str = get_setting("FISH_AUDIO_VOICE_ID", "")
TTS_ENGINE: str = get_setting("TTS_ENGINE", "fish_audio" if get_setting("FISH_AUDIO_API_KEY", "") else "elevenlabs")
WAKE_WORD: str = get_setting("WAKE_WORD", "jarvis")
WHISPER_MODEL: str = get_setting("WHISPER_MODEL", "small.en")
USE_LOCAL_STT: bool = str(get_setting("USE_LOCAL_STT", "true")).lower() in ("true", "1", "yes")

# Security & Permissions
AUTH_TOKEN: str = get_setting("AUTH_TOKEN", "")
SANDBOX_DIR: str = str(BASE_DIR / "sandbox")
SAFE_PATHS: List[str] = [
    str(Path.home() / "Downloads"),
    str(Path.home() / "Documents"),
    str(Path.home() / "Desktop"),
    str(BASE_DIR),
    SANDBOX_DIR,
    str(DAS_AND_CO_VAULT),
    "D:\\agent",
    "d:\\agent",
]

# Feature Toggles
CLAP_ENABLED: bool = str(get_setting("CLAP_ENABLED", "false")).lower() in ("true", "1", "yes")
GESTURES_ENABLED: bool = str(get_setting("GESTURES_ENABLED", "true")).lower() in ("true", "1", "yes")
VISION_ENABLED: bool = str(get_setting("VISION_ENABLED", "true")).lower() in ("true", "1", "yes")
UI_FRAMEWORK: str = get_setting("UI_FRAMEWORK", "pyside6")

def get_all_config() -> Dict[str, Any]:
    """Return unified configuration snapshot."""
    return {
        "AI_PROVIDER": AI_PROVIDER,
        "GEMINI_API_KEY": "***" if GEMINI_API_KEY else "",
        "OPENAI_API_KEY": "***" if OPENAI_API_KEY else "",
        "OLLAMA_BASE_URL": OLLAMA_BASE_URL,
        "DEFAULT_MODEL": DEFAULT_MODEL,
        "JARVIS_VOICE": JARVIS_VOICE,
        "WAKE_WORD": WAKE_WORD,
        "WHISPER_MODEL": WHISPER_MODEL,
        "USE_LOCAL_STT": USE_LOCAL_STT,
        "AUTH_TOKEN": AUTH_TOKEN,
        "SAFE_PATHS": SAFE_PATHS,
        "CLAP_ENABLED": CLAP_ENABLED,
        "GESTURES_ENABLED": GESTURES_ENABLED,
        "VISION_ENABLED": VISION_ENABLED,
        "UI_FRAMEWORK": UI_FRAMEWORK,
    }

def update_config(updates: Dict[str, Any]) -> bool:
    """Safely update config.json."""
    try:
        current = _load_json_config()
        current.update(updates)
        with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return True
    except Exception as e:
        print(f"[Config Error] Failed to update config: {e}")
        return False
