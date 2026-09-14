# 🤖 JARVIS V3.0 — Architecture Specification

## Overview

JARVIS V3.0 is a modular, multi-modal, agentic personal desktop assistant for Windows. It operates an autonomous **Observe $\rightarrow$ Plan $\rightarrow$ Execute $\rightarrow$ Verify $\rightarrow$ Replan** loop powered by unified AI providers (Gemini, OpenAI, and local Ollama), persistent SQLite memory, hardware-grounded security permissions, faster-whisper local speech recognition, computer vision, and a modern PySide6 HUD.

```
                             ┌────────────────────────┐
                             │       User Input       │
                             │ (Voice / UI / Web API) │
                             └───────────┬────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │    Voice/Text Ingest    │
                            │ (Whisper STT / Router)  │
                            └────────────┬────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │    JarvisAgent Brain    │
                            │  Observe & Context Load │
                            └────────────┬────────────┘
                                         │
                 ┌───────────────────────┼──────────────────────┐
                 ▼                       ▼                      ▼
        ┌─────────────────┐    ┌──────────────────┐   ┌──────────────────┐
        │   User Memory   │    │   AI Provider    │   │  Tools Registry  │
        │ SQLite WAL DB   │    │ Gemini / OpenAI  │   │  Ground Truth    │
        │ Facts & History │    │ / Local Ollama   │   │  Permissions     │
        └─────────────────┘    └─────────┬────────┘   └─────────┬────────┘
                                         │                      │
                                         ▼                      │
                               ┌───────────────────┐            │
                               │ Action Plan (JSON)│            │
                               └─────────┬─────────┘            │
                                         │                      │
                                         ▼                      ▼
                            ┌─────────────────────────────────────────┐
                            │           ToolExecutor Core             │
                            │    Authoritative Permission Guard:      │
                            │        SAFE / CONFIRM / BLOCKED         │
                            └────────────────────┬────────────────────┘
                                                 │
                                                 ▼
                            ┌─────────────────────────────────────────┐
                            │             Tool Execution              │
                            │  PyAutoGUI | System | Files | Vision    │
                            └────────────────────┬────────────────────┘
                                                 │
                                                 ▼
                            ┌─────────────────────────────────────────┐
                            │           Action Verifier               │
                            │ Checks State: Process/File/Volume/Memory│
                            └────────────────────┬────────────────────┘
                                                 │
                                 ┌───────────────┴───────────────┐
                                 │                               │
                          [Passes Checks]                 [Fails Checks]
                                 │                               │
                                 ▼                               ▼
                      ┌──────────────────────┐        ┌──────────────────────┐
                      │ Log Action & Report  │        │   Replanner Loop     │
                      │  (Edge-TTS Aloud)    │        │  (Max 2 Re-attempts) │
                      └──────────────────────┘        └──────────────────────┘
```

---

## Component Breakdown

### 1. Configuration & Core (`config.py`, `core/`)
- **`config.py`**: Centralized, unified configuration manager loading from environment variables, `.env`, and `config.json`.
- **`core/agent.py`**: Main agent orchestrator. Coordinates multi-turn memory context, intent routing, plan generation, step verification, and replanning.
- **`core/planner.py`**: Formulates structured, typed JSON action plans with explicit goals, steps, and parameters.
- **`core/permissions.py`**: Hardened security catalog. Python-level permission tiers (`SAFE`, `CONFIRM`, `BLOCKED`) that cannot be elevated by LLM JSON.
- **`core/verifier.py`**: Inspects real system state post-execution (e.g., checks running processes via `psutil`, confirms file creation/deletion, verifies memory storage).
- **`core/replanner.py`**: Dynamically crafts an alternative execution plan if an action step fails verification (capped at 2 replan attempts).

### 2. AI Intelligence Providers (`ai/`)
- **`ai/provider.py`**: Abstract base class `AIProvider` defining text generation, structured action planning, and multimodal vision analysis. Includes dynamic fallback cascade.
- **`ai/gemini_provider.py`**: Google Gemini REST integration supporting `gemini-flash-latest`, `gemini-3.5-flash`, and multimodal image analysis.
- **`ai/openai_provider.py`**: OpenAI integration supporting `gpt-4o-mini` and `gpt-4o` with JSON response formatting.
- **`ai/local_provider.py`**: Offline local intelligence via Ollama REST API (`/api/generate`).

### 3. Structured Persistent Memory (`memory/`)
- **`memory/database.py`**: Thread-safe SQLite connection pool with Write-Ahead Logging (`WAL` mode). Manages schema migrations for `conversations`, `user_facts`, `action_logs`, and `reminders`.
- **`memory/conversation.py`**: Manages sliding-window conversation history for LLM prompt context injection.
- **`memory/user_memory.py`**: Explicit and heuristic fact memory (`remember`, `forget`, `get_fact`).
- **`memory/retrieval.py`**: Fast keyword and substring search across facts and conversation logs. Provides complete execution audit logging.

### 4. Voice Subsystem (`voice/`)
- **`voice/speech_to_text.py`**: Dual-engine speech recognition using local `faster-whisper` (int8 on CPU) with automatic fallback to Google STT. Includes dynamic ambient noise floor calibration and Realtek stereo-to-mono resampling.
- **`voice/text_to_speech.py`**: High-fidelity neural voice synthesis (`edge-tts` with `en-GB-RyanNeural`) running on a dedicated background worker queue to eliminate UI freezing.
- **`voice/wake_word.py`**: Local acoustic and text wake word detection ("Jarvis").
- **`voice/clap_detection.py`**: Energy-based acoustic double-clap engine for touchless activation.

### 5. Multimodal Vision (`vision/`)
- **`vision/screen.py`**: High-performance multi-fallback screen capture (PyAutoGUI, PIL ImageGrab) coupled with multimodal vision analysis.
- **`vision/camera.py`**: Webcam snapshot acquisition and visual inspection.
- **`vision/gestures.py`**: MediaPipe Hand Landmarker air-mouse virtual control.

### 6. System & Automation Tools (`tools/`)
- **`tools/computer.py`**: Master volume control, screen locking, media playback keys, window management, and screenshots.
- **`tools/files.py`**: Path-restricted, sandboxed file manager preventing directory traversal (`..`) outside authorized roots.
- **`tools/system.py`**: Hardware telemetry reporting (CPU %, RAM %, Disk Free, Battery charging status).
- **`tools/applications.py`**: Application launcher and process terminator supporting native Windows alias mapping.
- **`tools/browser.py`**: Selenium-based web navigation, Google Search, and YouTube video autoplay.
- **`tools/web.py`**: BeautifulSoup4 web scraping for news RSS feeds and Wikipedia.

### 7. User Interface (`ui/`)
- **`ui/overlay.py`**: Sleek, frameless PySide6 HUD widget featuring an animated rotating Arc Reactor core, live system monitor bar, state indicator rings, and mouse dragging. Seamlessly falls back to Tkinter in lightweight or headless environments.
- **`ui/system_monitor.py`**: Background polling thread streaming live CPU and RAM metrics to the UI.
