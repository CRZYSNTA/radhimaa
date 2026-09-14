# 🤖 JARVIS V3.1 — Advanced Personal AI Assistant

An intelligent, autonomous personal assistant for Windows featuring screen-aware computer control, continuous conversational sessions, real-time streaming AI & neural TTS, live HUD task progress, ground-truth security permissions, persistent memory, dual-engine speech recognition, multimodal vision, and an animated PySide6 Arc Reactor HUD.

---

## 🚀 Key Features in V3.1

- **Screen-Aware Computer Control**: `ScreenObservation`, `ScreenAnalyzer`, and `ActionSchema` ensuring computer actions are bound to display geometry with pre/post-action screen state verification.
- **Natural Conversational Sessions**: Multi-turn dialogue without repeating "Jarvis" on each utterance, context retention across consecutive requests, and automatic timeout / goodbye termination.
- **Real-Time Streaming AI & TTS**: Low-latency token generation via Gemini streaming (`streamGenerateContent`) piped directly into sentence-buffered neural speech (`speak_stream`).
- **Live Task Progress PySide6 HUD**: Centralized `EventBus` updating the HUD in real time (`PLANNING`, `OBSERVING`, `EXECUTING`, `VERIFYING`, `REPLANNING`, `CONFIRMATION_REQUIRED`) with step counter and active action description.
- **Deep Security & Jail Hardening**: Ground-truth Python permissions (`SAFE`, `CONFIRM`, `BLOCKED`), prompt-injection `<UNTRUSTED_DATA>` segregation, Windows UNC/device namespace blocking, and fail-closed remote access.
- **Persistent Structured Memory**: SQLite database (`WAL` mode) storing multi-turn conversations, user preferences, profile facts, and execution audit logs.
- **Dual Speech Recognition**: Offline local transcription with `faster-whisper` (int8 on CPU) plus automatic fallback to Google STT.
- **Neural Text-to-Speech**: Microsoft Edge-TTS British neural voice (`en-GB-RyanNeural`) on a non-blocking queue.
- **Multimodal Computer Vision**: Multi-fallback desktop screenshot analysis, webcam environment inspection, and MediaPipe hand-tracking air-mouse control.

---

## ⚡ Quick Start

### 1. Configure Environment
Copy `.env.example` to `.env` or edit `config.json`:
```ini
AI_PROVIDER=gemini
DEFAULT_MODEL=gemini-flash-latest
GEMINI_API_KEY=your_gemini_api_key_here
JARVIS_VOICE=en-GB-RyanNeural
AUTH_TOKEN=your_secure_random_token_here
USE_LOCAL_STT=true
UI_FRAMEWORK=pyside6
```

### 2. Run JARVIS V3.1
```bash
python main.py
```
Or double-click `start_jarvis.bat` or the desktop executable `JARVIS.exe`.

### 3. Run Automated PyTest Suite
```bash
python run_tests.py
```

---

## 🏗️ Architecture & Security
- Complete architecture documentation: [`ARCHITECTURE.md`](file:///ARCHITECTURE.md)
- Security controls & permission tiers: [`SECURITY.md`](file:///SECURITY.md)

