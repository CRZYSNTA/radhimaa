"""
=============================================================================
JARVIS 24/7 Cloud Server Engine (FastAPI)
=============================================================================
Hosted 24/7 on Free Cloud Platforms (Render / HuggingFace / Koyeb / Railway).

Endpoints:
 - GET  /           : Live Web Dashboard & HUD
 - GET  /health      : 24/7 Cloud Health Check
 - POST /ask         : Mobile & iOS Shortcut Endpoint
 - POST /api/chat    : Web API Endpoint

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import json
import requests
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="JARVIS 24/7 Cloud Server", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
AUTH_TOKEN = os.environ.get("JARVIS_AUTH_TOKEN", "")


class AskQuery(BaseModel):
    text: str

class ChatQuery(BaseModel):
    message: str


def fetch_gemini_ai_response(user_text: str) -> str:
    """Queries Google Gemini 3.6 Flash / 2.5 Flash cloud models."""
    if not user_text:
        return "I received an empty query, sir."

    # Quick Local Skills
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
        return f"I received your query: '{user_text}'. Please configure GEMINI_API_KEY in environment variables."

    models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash-8b"]
    system_prompt = "You are JARVIS, a highly intelligent, polite, and concise AI assistant inspired by Iron Man. Keep answers brief (1 to 3 sentences max)."
    
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

    return f"I received your query: '{user_text}'. Brain active!"


def verify_auth(request: Request, x_jarvis_token: str = Header(None)):
    """Verifies security auth token for remote callers."""
    client_ip = request.client.host if request.client else ""
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        return

    token_to_check = AUTH_TOKEN or os.environ.get("JARVIS_AUTH_TOKEN")
    if token_to_check and x_jarvis_token != token_to_check:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid JARVIS Security Token")


@app.get("/health")
def health_check():
    return {"status": "online", "system": "JARVIS 24/7 Cloud Server", "version": "2.0"}


@app.get("/", response_class=HTMLResponse)
def get_web_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JARVIS 24/7 Cloud Console</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; display: flex; justify-content: center; }
            .card { width: 100%; max-width: 500px; background: #1e293b; border: 1px solid #38bdf8; border-radius: 12px; padding: 20px; box-shadow: 0 0 25px rgba(56, 189, 248, 0.3); }
            h1 { color: #38bdf8; text-align: center; margin-top: 0; font-size: 22px; }
            #box { height: 320px; overflow-y: auto; background: #0f172a; border-radius: 8px; padding: 12px; margin-bottom: 12px; border: 1px solid #334155; }
            .msg { margin: 8px 0; padding: 10px; border-radius: 6px; font-size: 14px; }
            .user { background: #0284c7; color: white; }
            .jarvis { background: #334155; color: #38bdf8; border-left: 3px solid #38bdf8; }
            .row { display: flex; gap: 8px; }
            input { flex: 1; padding: 12px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: white; }
            button { padding: 12px 18px; border-radius: 6px; border: none; background: #38bdf8; color: #0f172a; font-weight: bold; cursor: pointer; }
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
            async function send() {
                const inp = document.getElementById('inp');
                const text = inp.value.trim();
                if(!text) return;
                append('You: ' + text, 'user');
                inp.value = '';
                try {
                    const res = await fetch('/ask', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text: text})
                    });
                    const data = await res.json();
                    append('JARVIS: ' + data.reply, 'jarvis');
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
    return HTMLResponse(content=html_content)


@app.post("/ask")
def ask_endpoint(payload: AskQuery, request: Request, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    reply = fetch_gemini_ai_response(payload.text)
    return {"reply": reply}


@app.post("/api/chat")
def chat_endpoint(query: ChatQuery, request: Request, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    reply = fetch_gemini_ai_response(query.message)
    return {"response": reply}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
