# JARVIS V4 — Pre-Online Cleanup Audit & Inventory

**Audit Date:** September 13, 2026  
**Objective:** Identify active production code, isolate uncertain legacy implementations, preserve user memory and data, and safely purge confirmed disposable artifacts prior to new online architecture deployment.

---

## 1. Summary of Repository Classification

| Classification | Count Category | Action Policy |
| :--- | :--- | :--- |
| **A. Active Production Code** | Core server, orchestration, tools, UI, V4 services | **KEEP** (Protected) |
| **B. Required Dependency / Config** | `config.py`, `config_v4/`, `.env`, `requirements.txt` | **KEEP** (Protected) |
| **C. Legacy but Still Referenced** | `voice/push_to_talk.py`, `database.py`, legacy routes | **KEEP / ISOLATE** |
| **D. Duplicate Implementations** | Alternative brains (`fetch_ai_brain_reply`), PTT variants | **INVESTIGATE** |
| **E. Temporary / Generated Artifacts** | Stale `temp_*.mp3`, `launch_test.log`, `.voice_state` | **DELETE** (Safe to remove) |
| **F. Documentation** | Architecture, audit, security, and migration guides | **KEEP** |
| **G. Test Fixtures & Suites** | 33 test files in `tests/` | **KEEP** |
| **H. User Data & Memory Vault** | `jarvis_memory.db`, `vault/`, `00 - Inbox/` | **NEVER DELETE** |

---

## 2. Inventory: Temporary & Generated Files (Targeted for Safe Removal)

These files have been confirmed as disposable runtime outputs, build caches, or obsolete logs with zero external code references:

| Path | Type | Size | Last Modified | Referenced? | Imported? | Used at Runtime? | Status | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `temp_1789232729493.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:35:29 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789232760671.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:36:00 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789232791021.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:36:31 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789232821780.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:37:01 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789232852157.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:37:32 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789232882869.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:38:02 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789232913196.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:38:33 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789232943883.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:39:03 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789232974203.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:39:34 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233005001.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:40:05 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233157567.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:42:37 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233568300.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:49:28 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233598642.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:49:58 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233629320.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:50:29 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233659654.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:50:59 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233690274.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:51:30 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233720656.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:52:00 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233751558.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:52:31 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233781887.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:53:01 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233812539.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:53:32 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233842968.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:54:02 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233873644.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:54:33 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233903970.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:55:03 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233934611.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:55:34 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233964995.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:56:04 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789233995844.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:56:35 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789234026155.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:57:06 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789234056888.mp3` | Audio Temp | 0 bytes | Sat Sep 12 22:57:36 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `temp_1789314572673.mp3` | Audio Temp | 100772 bytes | Sun Sep 13 21:19:33 2026 | No | No | No | E (Temporary artifact) | **DELETE** (Stale TTS audio test output) |
| `launch_test.log` | Log File | ~1.3 MB | Sep 13 2026 | No | No | No | E (Obsolete log) | **DELETE** (Stale desktop launch log dump) |
| `.voice_state` | State File | ~10 bytes | Sep 13 2026 | No | No | No | E (Runtime IPC) | **DELETE** (Stale voice IPC state) |
| `.voice_telemetry` | State File | ~50 bytes | Sep 13 2026 | No | No | No | E (Runtime IPC) | **DELETE** (Stale voice telemetry cache) |
| `build/` | Build Dir | Multiple | Sep 2026 | No | No | No | E (Build artifact) | **DELETE** (PyInstaller object cache, safe to regenerate) |

---

## 3. Inventory: Configuration Systems Audit

| File / Directory | Scope & Purpose | Authoritative For | Recommendation |
| :--- | :--- | :--- | :--- |
| [`config.py`](file:///c:/Users/gowth/Downloads/RADHIMAA/config.py) | Centralized settings loader (prioritizes ENV -> config.py -> config.json) | Local desktop runtime, tools, vault paths | **KEEP** (Authoritative for local system) |
| [`config_v4/settings.py`](file:///c:/Users/gowth/Downloads/RADHIMAA/config_v4/settings.py) | Typed Pydantic V4 settings model | V4 AI gateway, timeouts, modern services | **KEEP** (Authoritative for V4 core) |
| [`config.json`](file:///c:/Users/gowth/Downloads/RADHIMAA/config.json) | Local JSON override store | User UI preferences and device overrides | **KEEP** (Local user preferences) |
| [`.env`](file:///c:/Users/gowth/Downloads/RADHIMAA/.env) | Secret credentials & auth tokens (`AUTH_TOKEN=naanthaandaleo`) | Server security & cloud authentication | **KEEP** (Strictly gitignored & protected) |
| [`.phone_config.json`](file:///c:/Users/gowth/Downloads/RADHIMAA/.phone_config.json) | Mobile device pairing credentials | Android wireless ADB & bridge pairing | **KEEP** |
| [`.tv_config.json`](file:///c:/Users/gowth/Downloads/RADHIMAA/.tv_config.json) | Smart TV network credentials | TV remote control tool | **KEEP** |

---

## 4. Inventory: Multiple Brain Implementations Audit

| Brain Implementation | Location | Callers & Usage | Capability | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Authoritative AI Gateway** | `orchestration/ai_gateway.py` + `ai/` | `ChatService`, `JarvisOrchestrator`, `/v1/chat` | Streaming, model cascading, tracing, error categorization, token tracking | **KEEP** (Authoritative production cognitive entry point) |
| **Direct Server Fallback** | `server.py::fetch_ai_brain_reply` | `core/agent.py:186`, `core/mobile_bridge.py:544`, `server.py:318` | Hardcoded REST to Gemini & Ollama (emergency fallback) | **INVESTIGATE / CONSOLIDATE** (Phase 2.2: adapt into AIGateway adapter) |
| **WarmBrain** | `leo/backtalk/backtalk/brain.py` | `leo/backtalk/backtalk/main.py` | Sentence-level streaming chunker, stage directions, Claude/Gemini driver | **INVESTIGATE / ISOLATE** (Preserve for spoken sentence pipeline) |

---

## 5. Inventory: Multiple Voice Implementations Audit

| Module | Purpose | Active Callers | Recommendation |
| :--- | :--- | :--- | :--- |
| [`voice/ptt_engine.py`](file:///c:/Users/gowth/Downloads/RADHIMAA/voice/ptt_engine.py) | Push-to-Talk controller with PyAudio recording & optional pynput | `desktop_window.py`, `server.py`, UI mic button | **KEEP** (Authoritative V4 PTT controller) |
| [`voice/push_to_talk.py`](file:///c:/Users/gowth/Downloads/RADHIMAA/voice/push_to_talk.py) | Native Windows `GetAsyncKeyState` hotkey monitor | Standalone Windows background PTT | **KEEP** (Zero-dependency Windows fallback) |
| [`voice/text_to_speech.py`](file:///c:/Users/gowth/Downloads/RADHIMAA/voice/text_to_speech.py) | Edge-TTS audio synthesis & acoustic formatting rules | All spoken outputs across JARVIS | **KEEP** (Authoritative TTS engine) |
| [`voice/speech_to_text.py`](file:///c:/Users/gowth/Downloads/RADHIMAA/voice/speech_to_text.py) | Faster-Whisper local speech transcription | STT pipeline | **KEEP** (Authoritative STT engine) |

---

## 6. Inventory: Online & Tunnel Infrastructure

| Component | Path | Status | Purpose | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Public HTTPS Tunnel** | `tunnel_manager.py` & `cloudflared.exe` | **ACTIVE** | Instant zero-config Cloudflare HTTPS/WSS tunnel | **KEEP** (Active for mobile remote access) |
| **Tunnel Launcher** | `start_server_and_tunnel.py` | **ACTIVE** | Starts local server, tunnel, and generates pairing QR | **KEEP** |
| **Vercel Serverless** | `vercel.json` & `api/index.py` | **ACTIVE** | Routes cloud serverless requests on Vercel | **KEEP** (Prepared for permanent custom domain) |
| **Cloud Engine** | `cloud_deployment/main.py` | **ACTIVE** | Standalone 24/7 server engine with /tmp SQLite fix | **KEEP** |
| **Mobile Bridge** | `core/mobile_bridge.py` | **ACTIVE** | Paired device authorization & confirmation gating | **KEEP** |

---

## 7. Inventory: User Memory & Vault (Strictly Protected)

- [`jarvis_memory.db`](file:///c:/Users/gowth/Downloads/RADHIMAA/jarvis_memory.db): **DO NOT DELETE**. Stores conversational history and user memory facts.
- `jarvis_memory.db.v3_backup`: **DO NOT DELETE**. Preserved backup of prior state.
- `vault/`, `Inbox/`, `00 - Inbox/`: **DO NOT DELETE**. User Obsidian knowledge base and memory notes.

---

## 8. Inventory: Compiled Binaries & Releases

- `dist/` (`JARVIS.exe`, `JARVIS_V2_backup.exe`, `JARVIS_V3.1.exe`, `JARVIS_V3.exe`, `JARVIS_Widget.exe`): **KEEP / ARCHIVE**. Contains pre-compiled standalone executable builds.
