"""
=============================================================================
JARVIS 24/7 Full Backend Cloud Server Engine (No-Cache Web Dashboard)
=============================================================================
Fixes Applied:
 - [Cache Fix]: Added Cache-Control headers to prevent browser stale cache.
 - [Data Fix]: Unified payload handler supporting text/message/reply/response.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import json
import sqlite3
import requests
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis_memory.db")

def init_db():
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
    conn.commit()
    conn.close()

def save_conversation(sender: str, message: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO conversation_history (sender, message) VALUES (?, ?)', (sender, message))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Save Error]: {e}")

def get_recent_conversations(limit: int = 10):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp, sender, message FROM conversation_history ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{"timestamp": r[0], "sender": r[1], "message": r[2]} for r in reversed(rows)]
    except Exception as e:
        print(f"[DB Fetch Error]: {e}")
        return []

init_db()

app = FastAPI(title="JARVIS 24/7 Full Backend Cloud Server", version="2.7")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
AUTH_TOKEN = os.environ.get("JARVIS_AUTH_TOKEN", "")


class UnifiedQuery(BaseModel):
    text: str = None
    message: str = None

    def get_query(self) -> str:
        return self.text or self.message or ""


def fetch_gemini_ai_response(user_text: str) -> str:
    if not user_text:
        return "I received an empty query, sir."

    q = user_text.lower()
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

    key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if not key:
        return f"I received your query: '{user_text}'. Configure GEMINI_API_KEY in Render environment variables."

    models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash-8b"]
    system_prompt = "You are JARVIS, a highly intelligent, polite, and concise AI assistant inspired by Iron Man. Keep answers brief (1 to 2 sentences max)."
    
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": f"{system_prompt}\nUser: {user_text}\nJARVIS:"}]}]}
            res = requests.post(url, json=payload, timeout=6)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            pass

    return f"I received your query: '{user_text}'. Brain active, sir!"


def process_query_with_memory(user_text: str) -> str:
    save_conversation("User", user_text)
    reply = fetch_gemini_ai_response(user_text)
    save_conversation("JARVIS", reply)
    return reply


def verify_auth(request: Request, x_jarvis_token: str = Header(None)):
    client_ip = request.client.host if request.client else ""
    referer = request.headers.get("referer", "")
    
    # Allow loopback calls or calls originating directly from the web console UI
    if client_ip in ["127.0.0.1", "localhost", "::1"] or "onrender.com" in referer:
        return

    token_to_check = AUTH_TOKEN or os.environ.get("JARVIS_AUTH_TOKEN")
    if token_to_check and x_jarvis_token != token_to_check:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid JARVIS Security Token")


@app.get("/health")
def health_check():
    return {"status": "online", "system": "JARVIS 24/7 Cloud Server", "version": "2.7"}


@app.get("/")
def get_web_dashboard():
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
            .card { width: 100%; max-width: 550px; background: #1e293b; border: 1px solid #38bdf8; border-radius: 12px; padding: 22px; box-shadow: 0 0 30px rgba(56, 189, 248, 0.35); }
            h1 { color: #38bdf8; text-align: center; margin-top: 0; font-size: 22px; letter-spacing: 1px; }
            #box { height: 340px; overflow-y: auto; background: #0f172a; border-radius: 8px; padding: 12px; margin-bottom: 14px; border: 1px solid #334155; }
            .msg { margin: 8px 0; padding: 10px 14px; border-radius: 8px; font-size: 14px; line-height: 1.4; }
            .user { background: #0284c7; color: white; margin-left: 20%; }
            .jarvis { background: #334155; color: #38bdf8; border-left: 4px solid #38bdf8; margin-right: 15%; }
            .row { display: flex; gap: 8px; }
            input { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: white; font-size: 14px; }
            button { padding: 12px 20px; border-radius: 8px; border: none; background: #38bdf8; color: #0f172a; font-weight: bold; cursor: pointer; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🤖 JARVIS 24/7 Cloud Console</h1>
            <div id="box"></div>
            <div class="row">
                <input type="text" id="inp" placeholder="Type a message or ask a question..." onkeydown="if(event.key==='Enter') send()">
                <button onclick="send()">Send</button>
            </div>
        </div>
        <script>
            async function loadHistory() {
                try {
                    const res = await fetch('/api/history?limit=10&v=' + Date.now());
                    if (res.ok) {
                        const data = await res.json();
                        (data.history || []).forEach(item => {
                            const text = item.message || item.text || item.content || '';
                            const sender = item.sender || 'JARVIS';
                            if (text) {
                                append(sender + ': ' + text, sender.toLowerCase() === 'user' ? 'user' : 'jarvis');
                            }
                        });
                    }
                } catch(e) {}
            }
            loadHistory();

            async function send() {
                const inp = document.getElementById('inp');
                const text = inp.value.trim();
                if(!text) return;
                append('You: ' + text, 'user');
                inp.value = '';
                try {
                    const res = await fetch('/ask', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-JARVIS-Token': 'jarvis_secret_key_777'
                        },
                        body: JSON.stringify({text: text, message: text})
                    });
                    const data = await res.json();
                    const reply = data.reply || data.response || data.detail || 'No response';
                    append('JARVIS: ' + reply, 'jarvis');
                } catch(e) {
                    append('JARVIS: Connection Error', 'jarvis');
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


@app.get("/api/history")
def history_endpoint(request: Request, limit: int = 10, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    return {"history": get_recent_conversations(limit)}


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            reply = process_query_with_memory(data)
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
