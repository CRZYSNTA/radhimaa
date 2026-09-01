# 🤖 JARVIS Personal AI Assistant

An intelligent, voice-enabled, cross-device AI assistant with hand gesture control built in Python.

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables (Recommended)
Set environment variables or edit local `config.json`:
```bash
export GEMINI_API_KEY="your_api_key_here"
export JARVIS_AUTH_TOKEN="your_secret_auth_token_here"
```

### 3. Run JARVIS
- **Option A (Interactive Terminal Mode):** `python jarvis_main.py`
- **Option B (Silent Desktop Launcher):** Double-click `Launch_JARVIS.bat` on your Desktop.

---

## 🔒 Security Recommendations
- **API Keys & Secrets:** Store sensitive tokens in environment variables (`GEMINI_API_KEY`, `JARVIS_AUTH_TOKEN`).
- **Git Safety:** `config.json` and `jarvis_memory.db` are strictly `.gitignore`d.
