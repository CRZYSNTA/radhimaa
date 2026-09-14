# JARVIS V4 — Comprehensive Codebase & Architecture Audit
**Source of Truth:** Existing RADHIMAA / JARVIS Codebase  
**Date:** September 13, 2026  
**Auditor:** Antigravity Autonomous Agent (Google DeepMind)  
**Status:** Audit Complete — Baseline Established  

---

## 1. Executive Summary & Audit Baseline

The RADHIMAA repository is an established, highly capable agentic personal desktop operating assistant for Windows. It features a complete multi-modal Observe-Plan-Execute-Verify-Replan loop, an Obsidian Markdown knowledge vault, local faster-whisper speech recognition, Edge-TTS synthesis with RyanNeural cadence, webcam vision (`look`/`watch`), and a native Edge WebView2 holographic desktop HUD.

However, the repository exhibits architectural divergence accumulated across rapid development phases (V3.0, LEO, and initial V4 slices):
1. **Parallel Execution Engines**: `core/agent.py` (V3 synchronous loop) and `orchestration/orchestrator.py` (V4 async orchestrator) run concurrently with duplicate tool registration and model calling paths.
2. **Brain Bypasses in Server**: `server.py` contains direct REST calls to Gemini and Ollama (`fetch_ai_brain_reply`), bypassing both `AIGateway` and `ChatService`.
3. **Critical Path Traversal Security Gap**: `is_path_safe` permits access to `BASE_DIR`, allowing `read_file("config.json")` to expose secrets and API keys to callers.
4. **Missing V4 Autonomous Modules**: Screen Eyes with local image diffing, Focus Sessions with deferred locking, centralized Model Registry with exact brain switching, live Diagnostics endpoints, and Live Preflight are currently missing.

---

## 2. Current Architecture Map

```text
                               ┌───────────────────────────┐
                               │   User Input / Triggers   │
                               │ Voice / Desktop HUD / API │
                               └─────────────┬─────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
          [Push-to-Talk / Hands-Free]                 [FastAPI /v1/chat & /ask]
             voice/ptt_engine.py                               server.py
                       │                                           │
                       ▼                                           ▼
             [Faster-Whisper STT]                     [ChatService / DTO]
            voice/speech_to_text.py               orchestration/chat_service.py
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │     Central Fast-Path     │
                               │       core/router.py      │
                               └─────────────┬─────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
             {SIMPLE Tool Intent}                          {COMPLEX Goal}
              <0.05s Direct Call                      orchestration/orchestrator.py
                      │                                             │
                      │                                             ▼
                      │                               ┌───────────────────────────┐
                      │                               │       Rich Context        │
                      │                               │  Obsidian Vault + SQLite  │
                      │                               └─────────────┬─────────────┘
                      │                                             │
                      │                                             ▼
                      │                               ┌───────────────────────────┐
                      │                               │        AI Gateway         │
                      │                               │  orchestration/ai_gateway │
                      │                               │    (Gemini Primary)       │
                      │                               └─────────────┬─────────────┘
                      │                                             │
                      └──────────────────────┬──────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │    Authoritative Policy   │
                               │  orchestration/tool_router│
                               │   SAFE / CONFIRM / BLOCKED│
                               └─────────────┬─────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
               [SAFE Execution]                             [CONFIRM Gate]
              Hardware / System /                      Action Confirmation Modal
              Read Note / Look / Watch                  (/v1/tools/{name}/confirm)
                      │                                             │
                      └──────────────────────┬──────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │      Action Verifier      │
                               │  psutil / disk / registry │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │    Speech Formatting &    │
                               │       Acoustic TTS        │
                               │   format_speech_text()    │
                               │  en-GB-RyanNeural (Edge)  │
                               └───────────────────────────┘
```

---

## 3. Existing Capabilities (Functional & Verified)

| Subsystem | Functional Components | Status |
| :--- | :--- | :--- |
| **FastAPI Backend** | `/health`, `/v1/chat`, `/v1/chat/stream`, `/v1/tools/{name}/confirm`, `/ws/hologram` | Verified, 25 tests passing |
| **Desktop Application** | `desktop_window.py` (Edge WebView2 via `pywebview`), Three.js WebGL particle orb, floating chat dock, confirmation modal, port reclamation | Verified, functional |
| **Brain / AI Provider** | `GeminiProvider` (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-flash-latest`), single and multi-frame analysis | Verified, working |
| **Voice Engine** | `voice/ptt_engine.py` (Home key listener, barge-in, Realtek 44.1kHz downmixing), `voice/text_to_speech.py` with `format_speech_text` | Verified, working |
| **Acoustic Persona** | Positional "Sir", 2-sentence ceiling, median <12 words, zero filler/apology, phonetic dates/times | Verified, working |
| **Camera Vision** | `vision/camera.py`: `look()` (single-frame capture), `watch()` (multi-frame sequence with offsets) via DirectShow (`cv2.CAP_DSHOW`) | Verified, working |
| **Controlled Tools** | `SetVolumeTool`, `SystemTelemetryTool`, `OpenApplicationTool`, `ReadNoteTool`, `ProposeNoteUpdateTool`, `LookTool`, `WatchTool` | Verified, working |
| **Memory Vault** | `memory/obsidian_vault.py` (`C:/Users/gowth/das and co`), SQLite WAL DB (`conversations`, `user_facts`, `action_logs`) | Verified, working |

---

## 4. Missing Capabilities (Target V4 Blueprint)

1. **Perception Layer Separation**:
   - Missing separate `vision/frame_manager.py`, `vision/local_perception.py`, and `vision/vision_gateway.py`.
   - Camera and Screen are not yet strictly isolated behind a structured perception gateway.
2. **Screen Eyes & Screen Watch**:
   - Missing structured screen observation engine (`vision/screen_analyzer.py` has dataclasses but no live diffing engine).
   - Missing `ScreenWatchService`: local frame sampling $\rightarrow$ local pixel/hash diffing $\rightarrow$ stillness threshold $\rightarrow$ one-shot Gemini inspection $\rightarrow$ cooldown.
3. **Canonical Model Registry & Exact Brain Switching**:
   - Missing `config/models.json` with canonical IDs, spoken aliases, capabilities, and provider bindings.
   - Missing exact brain switching ("switch to model X") with refusal on unknown models.
4. **Dedicated Focus Sessions & Deferred Lock**:
   - Missing `services/focus/` (`session.py`, `detector.py`, `targets.py`, `callouts.py`, `ledger.py`, `diagnostics.py`).
   - Missing deferred locking (starting focus from HUD must not lock the HUD; requires settling on target app/tab).
   - Missing named distraction callouts ("YouTube can wait, sir.") without persistent identity surveillance.
5. **Observability, Diagnostics & Live Preflight**:
   - Missing `/api/diagnostics` exposing real subsystem booleans (`server`, `agent`, `llm`, `memory`, `voice`, `camera`, `screen`, `executor`).
   - Missing `preflight.py` running actual end-to-end checks on the running instance.
6. **Device Control Abstraction Layer**:
   - Missing `devices/` abstraction (`devices/base.py`, `devices/registry.py`, `devices/android_tv/`). TV commands are currently hardcoded ad-hoc scripts in `tools/tv_controller.py`.

---

## 5. Duplicated & Obsolete Systems

1. **Divergent Agent Loops**:
   - `core/agent.py` (`JarvisAgent.process_input` — V3 sync) vs `orchestration/orchestrator.py` (`JarvisOrchestrator.run` — V4 async).
   - `core/mobile_bridge.py` still invokes `core/agent.py` instead of `orchestration/chat_service.py`.
2. **Divergent Server Brain Calls**:
   - `server.py` defines `fetch_ai_brain_reply()`, making raw HTTP requests directly to Gemini and Ollama with hardcoded system prompts, bypassing `AIGateway`.
3. **Duplicated Push-to-Talk Implementations**:
   - `voice/push_to_talk.py` (legacy `GetAsyncKeyState` polling) vs `voice/ptt_engine.py` (modern `pynput` listener with barge-in).
4. **Duplicated Configuration Groups**:
   - `config.py` (legacy untyped) vs `config_v4/settings.py` (typed dataclasses) vs `config.json`.
5. **Divergent UI Frontends**:
   - PySide6 Qt desktop widgets (`ui/overlay.py`, `ui/floating_orb.py`) vs WebGL Three.js desktop interface (`interface/` + `desktop_window.py`).

---

## 6. Technical Debt & Code Smells

1. **Fake Screen Fallback**:
   - `vision/screen.py` generates a blank blue canvas `Image.new('RGB', (800, 600), (15, 23, 42))` when screen capture fails, analyzing that instead of reporting failure.
2. **Hardcoded Model URLs**:
   - Several files (`vision/screen.py`, `server.py`, `ai/local_provider.py`) hardcode endpoints like `gemini-1.5-flash` or `http://localhost:11434` rather than referencing `AISettings` or a model registry.
3. **Scattered Temporary Audio Files**:
   - 25+ orphaned `temp_*.mp3` files exist in the root folder from uncleaned TTS runs.
4. **Mocked Vector Embeddings**:
   - `orchestration/ai_gateway.py` uses a deterministic modulo hash generator `(hash(text + str(i)) % 1000) / 1000.0` for vector embeddings.
5. **No Verification Timing Tracing**:
   - Tool execution lacks unified correlation trace IDs spanning from user voice input to post-verification audit records.

---

## 7. Critical Security Risks

1. **[HIGH] Secret Exfiltration via `read_file` Tool**:
   - `config.py` places `BASE_DIR` (`c:\Users\gowth\Downloads\RADHIMAA`) inside `SAFE_PATHS`.
   - `is_path_safe()` in `core/permissions.py` considers any path within `SAFE_PATHS` safe.
   - Calling `read_file("config.json")` or `read_file(".env")` reads and leaks live API keys and tokens.
   - **Remediation**: Explicitly blocklist `.env`, `config.json`, `.git`, `.phone_config.json`, `.tv_config.json`, and database files from tool read/write/delete operations.
2. **[HIGH] Loopback CORS / Unauthenticated Local API Hijacking**:
   - In `server.py`, `verify_auth()` unconditionally permits all requests from `127.0.0.1`, `localhost`, and `::1`.
   - `CORSMiddleware` allows `allow_origins=["*"]`.
   - Any malicious webpage opened in the user's browser can execute POST requests against `http://127.0.0.1:8000/ask` or `/v1/chat` to control the desktop without needing `AUTH_TOKEN`.
   - **Remediation**: Restrict CORS to allowed local webview origins, and require a local session nonce or header for loopback execution.
3. **[MEDIUM] Mobile Remote Execution Confirmation Bypass**:
   - `/api/remote/agent` triggers `execute_mobile_agent_query()` which executes tools directly without routing through the desktop Action Confirmation Modal.
4. **[MEDIUM] Inconsistent Permission Enforcement across Callers**:
   - Legacy `ToolExecutor` and V4 `ToolRouter` have slightly different permission check paths, risking tier desynchronization.

---

## 8. Critical Reliability Risks

1. **Orchestrator Fallback Divergence**:
   - If `ChatService` throws an unhandled exception, `server.py` falls back to `fetch_ai_brain_reply`, which has no tool calling, no memory vault access, and no confirmation gates.
2. **Camera Resource Locking**:
   - OpenCV `VideoCapture` instances must guarantee release via `finally` blocks across all execution branches to prevent hardware device lockups.
3. **WebAudio / PyAudio Downmixing Desync**:
   - Dual-channel Realtek microphone arrays on Windows can fail if buffer chunk sizes do not align with 16kHz downsampling steps.
4. **Obsidian Vault Write vs Index Desync**:
   - Writing a note to `das and co/00 - Inbox` succeeds on disk, but if the in-memory cache is not immediately updated, subsequent lookups in the same turn fail to find the newly written note.

---

## 9. Recommended Migration Order (10-Phase Incremental Plan)

```text
Phase 1: Security Hardening & Secret Protection (Block sensitive files, harden loopback CORS)
Phase 2: Observability & Preflight Suite (Implement /api/diagnostics and preflight.py)
Phase 3: Model Registry & Exact Brain Switching (config/models.json, canonical routing)
Phase 4: Agent & Tool Unification (Retire dead legacy paths, route mobile through ChatService)
Phase 5: Perception Layer (Separation of Camera and Screen Eyes, eliminate fake blank images)
Phase 6: Screen Watch & Diff Engine (Local stillness detection, threshold-gated Gemini inspection)
Phase 7: Memory Evidence & Immediate Indexing (Instant indexing post-write, source attribution)
Phase 8: Proactive Focus Sessions (services/focus/, deferred lock, distraction callouts)
Phase 9: Device Control Abstraction (devices/base.py, Android TV clean integration)
Phase 10: Final Hardening & Verification (End-to-end regression, preflight pass, documentation)
```

---

## 10. First Five Concrete Actions to Execute

1. **Secure File Access**: Patch `core/permissions.py` and `tools/files.py` to blocklist `config.json`, `.env`, and secret config files so they cannot be read or exfiltrated via tools. Add unit test `test_secret_files_cannot_be_read()`.
2. **Build Canonical Model Registry**: Create `config/models.json` containing verified Gemini, OpenAI, and Local models with capabilities and aliases. Update `orchestration/ai_gateway.py` to refuse unknown model switches.
3. **Create Live Diagnostics Subsystem**: Implement `/api/diagnostics` and subsystem status endpoints in `server.py` and `orchestration/` exposing live boolean health states without secrets.
4. **Build Live Preflight Suite**: Create `preflight.py` to test the live server, memory, AI brain, tools, permissions, and secret isolation end-to-end.
5. **Fix Screen Vision Integrity**: Eliminate the fake blank-image fallback in `vision/screen.py` and route all screen vision calls through the canonical `AIGateway`.
