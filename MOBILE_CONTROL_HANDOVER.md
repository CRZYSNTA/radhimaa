# JARVIS Mobile Control Subsystem — Technical Handover Document

> **Target Audience**: AI Assistants, System Architects, Full-Stack Engineers  
> **Purpose**: Complete technical blueprint detailing how a mobile device pairs with, controls, and receives telemetry from the JARVIS host PC, as well as how JARVIS controls the mobile device back.

---

## 1. Executive Architecture Summary

JARVIS features a bidirectional mobile control bridge:
1. **Mobile $\rightarrow$ PC Control**: Mobile acts as a remote controller (Trackpad, Keyboard, Media/System controls, AI Voice/Chat interface, Screen Mirror, Clipboard sync, File uploader).
   - **Protocol**: HTTP REST (FastAPI) + WebSockets (`/ws/chat`).
   - **Frontend**: Responsive PWA (`/mobile` directory) and Native Android wrapper (`/android_app`).
2. **PC $\rightarrow$ Mobile Control**: JARVIS controls the mobile phone using **Wireless ADB (Android Debug Bridge)** over Wi-Fi (wake, unlock, PIN typing, lock screen).

---

## 2. Core File Registry & Responsibilities

| File Path | Role & Responsibilities |
| :--- | :--- |
| `server.py` | Central FastAPI backend (port 8000). Hosts API endpoints, serves PWA at `/app`, manages WebSocket `/ws/chat`, authenticates requests via bearer tokens. |
| `core/mobile_bridge.py` | Low-level execution engine. Win32 mouse/keyboard injection, system commands, telemetry collection (`psutil`), JPEG screen grabber, and AI execution routing. |
| `tools/pairing_manager.py` | Generates 6-digit PIN, renders scannable QR codes (ASCII terminal & `pairing_qr.png` on Desktop), and manages paired devices. |
| `mobile/app.js` | Mobile PWA logic: touch gestures $\rightarrow$ mouse deltas, WebSocket dispatch, Web Speech recognition, Neural TTS voice playback, telemetry polling. |
| `mobile/index.html` & `style.css` | Cyberpunk/Iron Man HUD UI for trackpad, chat, system controls, screen mirror, and voice settings. |
| `tools/phone_controller.py` | Host-side ADB integration. Discovers phone IP, connects over port 5555, executes `input keyevent`, `input swipe`, and `input text` to unlock phone. |
| `setup_wireless_phone.bat` | One-click setup utility to switch phone from USB ADB to Wireless TCP/IP mode. |
| `pair_mobile.bat` | Interactive terminal launcher for generating a pairing PIN and QR code. |

---

## 3. Security & Pairing Handshake Workflow

### Pairing Protocol (One-Time PIN $\rightarrow$ Permanent Token)
1. **Initiation**: User runs `pair_mobile.bat` (or triggers `tools.pairing_manager.pair_mobile()`).
   - Generates random 6-digit PIN with a 10-minute TTL (`expires_at = now + 600`).
   - Discovers host LAN IP (Wi-Fi preferred, e.g. `192.168.1.50`).
   - Construct URL: `http://<HOST_IP>:8000/app?pin=<PIN>`.
   - Generates a QR code image saved to Desktop (`pairing_qr.png`) and renders an ASCII QR in the terminal.
2. **Verification (`POST /api/pairing/verify`)**:
   - Mobile opens `/app?pin=123456` or user enters PIN manually in UI.
   - Body: `{"pin": "123456", "device_name": "iPhone / Pixel"}`.
   - Server validates PIN against active pairing memory.
   - Upon match: burns PIN (single-use), generates a cryptographically secure token (`secrets.token_urlsafe(32)`), generates a device ID (`dev_xxxx`), and writes it to SQLite DB table `paired_devices`.
   - Response: `{"success": true, "auth_token": "...", "device_id": "..."}`.
3. **Session Persistence**:
   - Mobile stores token in browser `localStorage.setItem('jarvis_mobile_token', token)`.
   - Subsequent requests pass `Authorization: Bearer <token>` or `x-jarvis-token` header. Remote calls without a valid token are rejected with HTTP 401/403.

---

## 4. Communication & Control APIs

### A. High-Speed Low-Latency WebSocket (`/ws/chat?token=<TOKEN>`)
Used for continuous real-time inputs without HTTP request overhead:
- **Trackpad / Cursor Movement**:
  - Format: `{"type": "mouse", "action": "move", "dx": float, "dy": float}`
  - PC Handler: Calls Windows API directly via `ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)` for zero lag.
  - Ballistic acceleration on mobile converts micro-movements into precise positioning and fast flicks into long glides. Deltas are batched every 16ms.
- **Mouse Clicks & Scrolling**:
  - Left click (single tap): `{"type": "mouse", "action": "click", "button": "left"}`
  - Right click (two-finger tap): `{"type": "mouse", "action": "click", "button": "right"}`
  - Scroll (two-finger vertical swipe): `{"type": "mouse", "action": "scroll", "dy": float}`
- **Virtual Keyboard**:
  - `{"type": "keyboard", "action": "press", "key": "enter"}`
  - `{"type": "keyboard", "action": "type", "text": "Hello PC"}`
- **Direct System Commands**:
  - `{"type": "system", "command": "volume_up|volume_down|volume_mute|lock_pc|sleep_pc"}`

### B. REST Endpoints (`/api/remote/...`)
- `POST /api/remote/agent`:
  - Body: `{"message": "Open Spotify and play rock music"}`.
  - Passes prompt to `orchestration.chat_service.ChatService`, which plans, executes tools with safety guards, and returns textual outcome.
- `GET /api/remote/telemetry`:
  - Returns real-time metrics: CPU %, RAM used/total, Disk free GB, Battery %, Active foreground window title, and Display brightness.
- `GET /api/remote/screen?quality=50&scale=0.5`:
  - Grabs screen via `pyautogui.screenshot()` or `PIL.ImageGrab`, rescales, converts to JPEG stream for live remote monitoring.
- `POST /api/remote/system`:
  - Handles brightness adjustment (`set_brightness`), sleep PC, lock PC, app launches (`launch_app`).
- `POST /api/remote/clipboard`:
  - `action: "get"` reads PC clipboard; `action: "set"` writes mobile text to PC clipboard via Tkinter clipboard bridge.
- `POST /api/remote/upload`:
  - Uploads multipart binary file directly into host user's `Downloads` folder (restricted to non-executable / non-sensitive paths).
- `POST /api/tts/generate`:
  - Text-to-speech using Microsoft Edge-TTS (`edge_tts.Communicate`) returning MP3 audio bytes with neural voices (`en-GB-RyanNeural`, `en-GB-SoniaNeural`, etc.) streamed straight to the phone speaker.

---

## 5. Reverse Control: JARVIS $\rightarrow$ Mobile Phone (Wireless ADB)

Implemented in `tools/phone_controller.py`:
- **Protocol**: Android Debug Bridge (ADB) over TCP/IP (port 5555).
- **Auto-Discovery**: Resolves phone IP from subnet scan or `.phone_config.json`.
- **Waking & Unlocking**:
  ```python
  # 1. Wake screen
  adb shell input keyevent KEYCODE_WAKEUP
  # 2. Swipe up lockscreen
  adb shell input swipe 500 1600 500 400 300
  # 3. Type stored PIN securely
  adb shell input text <PIN>
  adb shell input keyevent KEYCODE_ENTER
  ```
- **Remote Lock**:
  ```python
  adb shell input keyevent KEYCODE_POWER
  ```

---

## 6. How to Recreate or Extend this in Another Assistant

1. **Host Server Setup**: Create a FastAPI / Express / Flask server running on host `0.0.0.0:8000`.
2. **Input Injection**: Use native OS libraries (Python: `ctypes` or `pyautogui`; Node: `robotjs` / `nut.js`) for virtual input dispatch.
3. **Web Client**: Serve a static PWA accessible over Wi-Fi with touch listeners tracking `touchstart`, `touchmove`, `touchend` calculating delta `(dx, dy)`.
4. **WebSocket**: Keep a lightweight socket connection open for streaming mouse events at ~60fps (16ms throttle).
5. **Security**: Never expose open unauthenticated input ports; always enforce single-use pairing PIN $\rightarrow$ persistent device token in SQLite/session store.
