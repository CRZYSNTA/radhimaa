"""
=============================================================================
JARVIS 24/7 Full Backend Cloud Server Engine (Hardened & Secure V3.0)
=============================================================================
Security & Architecture Hardening:
 - [P0] Remote auth FAILS CLOSED: Rejects remote requests if JARVIS_AUTH_TOKEN is not configured
 - [P0] Removed client-spoofed Referer bypass ("onrender.com")
 - [P0] Authenticated WebSockets (/ws/chat) with token validation and 1008 rejection
 - [P1] Removed hard-coded default secret from client-delivered HTML/JS dashboard
 - [P1] Added message size validation (max 4000 characters)
 - [P1] In-memory sliding-window rate limiter per client IP (30 req/min)
=============================================================================
"""

import os
import time
import json
import sqlite3
import base64
import requests
from pathlib import Path
from collections import defaultdict
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# On Vercel / serverless platforms, only /tmp is writable
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_PATH = "/tmp/jarvis_memory.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis_memory.db")

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sender TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_key TEXT UNIQUE NOT NULL,
                fact_value TEXT NOT NULL
            )
        ''')
        cursor.execute("DELETE FROM conversation_history WHERE message = 'undefined' OR message IS NULL")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Init Error]: {e}")

def save_conversation(sender: str, message: str):
    msg_str = str(message).strip() if message else ""
    if not msg_str or msg_str == "undefined":
        msg_str = "Brain active, sir!"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO conversation_history (sender, message) VALUES (?, ?)', (sender, msg_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Save Error]: {e}")

def get_recent_conversations(limit: int = 10):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, sender, message FROM conversation_history WHERE message != 'undefined' AND message IS NOT NULL ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{"timestamp": r[0], "sender": r[1], "message": r[2]} for r in reversed(rows)]
    except Exception as e:
        print(f"[DB Fetch Error]: {e}")
        return []

init_db()

app = FastAPI(title="JARVIS 24/7 Full Backend Cloud Server", version="3.0")

# Mount modern V4 holographic web interface
interface_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "interface")
if os.path.exists(interface_dir):
    app.mount("/interface", StaticFiles(directory=interface_dir), name="interface")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

def get_gemini_api_key() -> str:
    k = os.environ.get("GEMINI_API_KEY", "")
    if not k:
        try:
            bt_cfg_file = Path("d:/agent/backtalk/backtalk.json")
            if bt_cfg_file.exists():
                with open(bt_cfg_file, "r", encoding="utf-8") as f:
                    k = json.load(f).get("gemini_api_key", "")
        except Exception:
            pass
    return k

GEMINI_API_KEY = get_gemini_api_key()

# Security Parameters
MAX_MESSAGE_LENGTH = 4000
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW = 60  # seconds
_client_request_timestamps = defaultdict(list)

def get_auth_token() -> str:
    """Retrieve expected token from environment without public fallbacks."""
    return os.environ.get("JARVIS_AUTH_TOKEN") or os.environ.get("AUTH_TOKEN") or ""

def check_rate_limit(client_id: str):
    """Sliding-window rate limiter enforcing max requests per minute."""
    now = time.time()
    timestamps = _client_request_timestamps[client_id]
    _client_request_timestamps[client_id] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_client_request_timestamps[client_id]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Too Many Requests: Rate limit of {RATE_LIMIT_REQUESTS} requests per minute exceeded."
        )
    _client_request_timestamps[client_id].append(now)

class UnifiedQuery(BaseModel):
    text: Optional[str] = None
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    confirmed: Optional[bool] = False
    attachments: Optional[List[Any]] = None

    def get_query(self) -> str:
        q = (self.text or self.message or "").strip()
        if len(q) > MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Bad Request: Message length ({len(q)}) exceeds maximum limit of {MAX_MESSAGE_LENGTH} characters."
            )
        return q

def fetch_gemini_ai_response(user_text: str) -> str:
    if not user_text:
        return "I received an empty query, sir."

    q = user_text.lower().strip()
    if "time" in q:
        import datetime
        return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."
    if "date" in q:
        import datetime
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."
    if "weather" in q:
        try:
            res = requests.get("https://wttr.in?format=%C+%t", timeout=3)
            if res.status_code == 200:
                return f"Current weather: {res.text.strip()}."
        except Exception:
            pass

    # Instant deterministic identity handling
    if any(p in q for p in ["who am i", "my name", "who is talking", "do you know me"]):
        return "You are Gowtham, Sir—my creator and operator."

    key = os.environ.get("GEMINI_API_KEY") or get_gemini_api_key()
    if key:
        # Prioritize high-availability and quota-efficient flash-lite models first
        models = [
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-flash-latest",
            "gemini-3.5-flash",
            "gemini-3.6-flash"
        ]
        system_prompt = (
            "You are J.A.R.V.I.S., a sophisticated, polite, and loyal AI operating system "
            "created by and serving Gowtham (whom you address respectfully as Sir or Boss). "
            "You know that the user speaking to you is Gowtham. "
            "Keep answers concise, intelligent, and natural (1 to 2 sentences max)."
        )

        history = get_recent_conversations(4)
        history_lines = []
        for h in history:
            sender = h.get("sender", "User")
            msg = h.get("message", "").strip()
            if msg and msg != "undefined":
                history_lines.append(f"{sender}: {msg}")
        history_context = ("\n".join(history_lines) + "\n") if history_lines else ""

        full_prompt = f"{system_prompt}\n\n{history_context}User: {user_text}\nJARVIS:"

        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
                res = requests.post(url, json=payload, timeout=6)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            ans = parts[0].get("text", "").strip()
                            if ans:
                                return ans
            except Exception:
                pass

    if any(p in q for p in ["who are you", "what are you", "describe yourself"]):
        return "I am J.A.R.V.I.S., a Just A Rather Very Intelligent System, designed to manage your technology and assist with your daily operations, Sir."

    return "All core diagnostics operational, Sir. Standing by for your instructions."

def process_query_with_memory(user_text: str) -> str:
    clean_text = user_text if user_text else "hello"
    save_conversation("User", clean_text)
    reply = fetch_gemini_ai_response(clean_text)
    save_conversation("JARVIS", reply)
    return reply

def verify_auth(request: Request, x_jarvis_token: str = Header(None)):
    """
    Strict security verification:
    - Loopback callers (localhost) are allowed for local development.
    - Remote callers MUST provide a valid token matching JARVIS_AUTH_TOKEN.
    - Fails closed: If no token is configured on the server, remote requests return 403 Forbidden.
    - Referer headers are NOT trusted for authentication.
    """
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        check_rate_limit(client_ip)
        return

    expected_token = get_auth_token()
    if not expected_token:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Remote access denied. JARVIS_AUTH_TOKEN is not configured on the server."
        )

    provided = x_jarvis_token
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        provided = auth_header[7:].strip()

    if not provided or provided != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing or invalid JARVIS Security Token."
        )

    check_rate_limit(client_ip)

@app.get("/health")
def health_check():
    return {"status": "online", "system": "JARVIS 24/7 Cloud Server", "version": "3.0"}

@app.get("/")
def get_web_dashboard():
    # If modern V4 interface exists, redirect to it
    interface_index = os.path.join(os.path.dirname(os.path.dirname(__file__)), "interface", "index.html")
    if os.path.exists(interface_index):
        return RedirectResponse(url="/interface/index.html")

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JARVIS 24/7 Cloud Console</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
        <meta http-equiv="Pragma" content="no-cache">
        <meta http-equiv="Expires" content="0">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; display: flex; justify-content: center; }
            .card { width: 100%; max-width: 560px; background: #1e293b; border: 1px solid #38bdf8; border-radius: 12px; padding: 22px; box-shadow: 0 0 30px rgba(56, 189, 248, 0.35); }
            h1 { color: #38bdf8; text-align: center; margin-top: 0; font-size: 22px; letter-spacing: 1px; }
            .auth-bar { display: flex; gap: 8px; margin-bottom: 12px; background: #0f172a; padding: 8px; border-radius: 8px; border: 1px solid #334155; }
            .auth-bar input { flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: white; font-size: 13px; }
            .auth-bar button { padding: 8px 14px; border-radius: 6px; border: none; background: #38bdf8; color: #0f172a; font-weight: bold; cursor: pointer; font-size: 13px; }
            #box { height: 320px; overflow-y: auto; background: #0f172a; border-radius: 8px; padding: 12px; margin-bottom: 14px; border: 1px solid #334155; }
            .msg { margin: 8px 0; padding: 10px 14px; border-radius: 8px; font-size: 14px; line-height: 1.4; }
            .user { background: #0284c7; color: white; margin-left: 20%; }
            .jarvis { background: #334155; color: #38bdf8; border-left: 4px solid #38bdf8; margin-right: 15%; }
            .err { background: #7f1d1d; color: #fca5a5; border-left: 4px solid #ef4444; }
            .row { display: flex; gap: 8px; }
            .row input { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: white; font-size: 14px; }
            .row button { padding: 12px 20px; border-radius: 8px; border: none; background: #38bdf8; color: #0f172a; font-weight: bold; cursor: pointer; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 JARVIS 24/7 Cloud Console</h1>
            <div class="auth-bar">
                <input type="password" id="authToken" placeholder="Enter Access Token...">
                <button onclick="saveToken()">Set Token</button>
            </div>
            <div id="box"></div>
            <div class="row">
                <input type="text" id="inp" placeholder="Type a message or ask a question..." onkeydown="if(event.key==='Enter') send()">
                <button onclick="send()">Send</button>
            </div>
        </div>
        <script>
            function getToken() {
                return sessionStorage.getItem('jarvis_token') || document.getElementById('authToken').value.trim();
            }
            function saveToken() {
                const val = document.getElementById('authToken').value.trim();
                sessionStorage.setItem('jarvis_token', val);
                append('Security token updated in local session.', 'jarvis');
                loadHistory();
            }
            window.onload = function() {
                const saved = sessionStorage.getItem('jarvis_token');
                if (saved) document.getElementById('authToken').value = saved;
                loadHistory();
            };

            async function loadHistory() {
                const token = getToken();
                try {
                    const res = await fetch('/api/history?limit=10&v=' + Date.now(), {
                        headers: token ? { 'X-JARVIS-Token': token } : {}
                    });
                    if (res.status === 401 || res.status === 403) {
                        append('Authentication required. Please enter your JARVIS Access Token above.', 'err');
                        return;
                    }
                    if (res.ok) {
                        const data = await res.json();
                        (data.history || []).forEach(item => {
                            const text = item.message || item.text || item.content || '';
                            const sender = item.sender || 'JARVIS';
                            if (text && text !== 'undefined') {
                                append(sender + ': ' + text, sender.toLowerCase() === 'user' ? 'user' : 'jarvis');
                            }
                        });
                    }
                } catch(e) {}
            }

            async function send() {
                const inp = document.getElementById('inp');
                const text = inp.value.trim();
                if(!text) return;
                const token = getToken();
                append('You: ' + text, 'user');
                inp.value = '';
                try {
                    const headers = { 'Content-Type': 'application/json' };
                    if (token) headers['X-JARVIS-Token'] = token;
                    const res = await fetch('/ask', {
                        method: 'POST',
                        headers: headers,
                        body: JSON.stringify({text: text, message: text})
                    });
                    if (res.status === 401 || res.status === 403) {
                        append('Access Denied: Please provide a valid JARVIS security token.', 'err');
                        return;
                    }
                    if (res.status === 429) {
                        append('Rate limit exceeded. Please wait a moment before sending more requests.', 'err');
                        return;
                    }
                    const data = await res.json();
                    const reply = data.reply || data.response || data.detail || 'Brain active, sir!';
                    append('JARVIS: ' + reply, 'jarvis');
                } catch(e) {
                    append('JARVIS: Connection Error', 'err');
                }
            }
            function append(m, c) {
                const b = document.getElementById('box');
                const d = document.createElement('div');
                d.className = 'msg ' + c;
                d.innerText = m;
                b.appendChild(d);
                b.scrollTop = b.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(
        content=html_content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/ask")
def ask_endpoint(payload: UnifiedQuery, request: Request, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    reply = process_query_with_memory(payload.get_query())
    return {"reply": reply, "response": reply}

@app.post("/api/chat")
def chat_endpoint(payload: UnifiedQuery, request: Request, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    reply = process_query_with_memory(payload.get_query())
    return {"reply": reply, "response": reply}

def synthesize_fish_audio(text: str) -> Optional[str]:
    fish_key = os.environ.get("FISH_AUDIO_API_KEY", "")
    if not fish_key or not text:
        return None
    try:
        url = "https://api.fish.audio/v1/tts"
        headers = {
            "Authorization": f"Bearer {fish_key}",
            "Content-Type": "application/json"
        }
        payload = {"text": text[:500], "format": "mp3"}
        voice_id = os.environ.get("FISH_AUDIO_VOICE_ID", "")
        if voice_id:
            payload["reference_id"] = voice_id
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        if resp.status_code == 200 and resp.content:
            return base64.b64encode(resp.content).decode("utf-8")
    except Exception:
        pass
    return None

@app.post("/v1/chat")
def v1_chat_endpoint(payload: UnifiedQuery, request: Request, x_jarvis_token: Optional[str] = Header(None)):
    verify_auth(request, x_jarvis_token)
    reply = process_query_with_memory(payload.get_query())
    audio_b64 = synthesize_fish_audio(reply)
    return {
        "reply": reply,
        "response": reply,
        "audio_b64": audio_b64,
        "conversation_id": payload.conversation_id or "conv-cloud",
        "tool_events": []
    }

@app.post("/v1/chat/stream")
async def v1_chat_stream_endpoint(payload: UnifiedQuery, request: Request, x_jarvis_token: Optional[str] = Header(None)):
    verify_auth(request, x_jarvis_token)
    query = payload.get_query()
    reply = process_query_with_memory(query)

    async def event_generator():
        words = reply.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'chunk', 'chunk': chunk})}\n\n"
        audio_b64 = synthesize_fish_audio(reply)
        yield f"data: {json.dumps({'type': 'done', 'content': reply, 'audio_b64': audio_b64})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/history")
@app.get("/history")
def history_endpoint(request: Request, limit: int = 10, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    return {"history": get_recent_conversations(limit)}

@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Secure WebSocket connection.
    Authenticates before accepting: requires valid token via query parameter or headers.
    Enforces message size limits and rate limiting.
    """
    client_ip = websocket.client.host if websocket.client else "unknown"
    expected_token = get_auth_token()

    # Resolve token from query param, X-JARVIS-Token header, or Authorization header
    provided = token
    if not provided:
        provided = websocket.headers.get("x-jarvis-token")
    if not provided:
        auth_hdr = websocket.headers.get("authorization", "")
        if auth_hdr.lower().startswith("bearer "):
            provided = auth_hdr[7:].strip()

    is_local = client_ip in ["127.0.0.1", "localhost", "::1"]

    if not is_local:
        if not expected_token or provided != expected_token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    elif expected_token and provided and provided != expected_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            if len(data) > MAX_MESSAGE_LENGTH:
                await websocket.send_text(f"Error: Message exceeds {MAX_MESSAGE_LENGTH} characters limit.")
                continue

            try:
                check_rate_limit(client_ip)
            except HTTPException as e:
                await websocket.send_text(f"Rate Limit Error: {e.detail}")
                continue

            reply = process_query_with_memory(data)
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
