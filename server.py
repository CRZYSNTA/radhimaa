"""
=============================================================================
JARVIS Stage 4: Central Cross-Device FastAPI Web Server (Hardened & Secure)
=============================================================================
Security & Architecture Fixes Applied:
 - [P0] Protected /api/history with verify_auth
 - [P0] Remote auth fails closed: Rejects remote requests if AUTH_TOKEN is missing
 - [P1] Hardened CORS policy (allow_credentials=False with explicit controls)
 - [P1] Active Ollama local LLM fallback after Gemini API failures

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import json
import requests
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import database

database.init_db()

app = FastAPI(title="JARVIS Central API Server", version="1.4")

# [P1 Fix]: Hardened CORS configuration (no wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Config Load Error]: {e}")
    return {}

config = load_config()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = config.get("DEFAULT_MODEL", os.environ.get("DEFAULT_MODEL", "llama3.2:1b"))
AUTH_TOKEN = config.get("AUTH_TOKEN", os.environ.get("JARVIS_AUTH_TOKEN", None))


class AskQuery(BaseModel):
    text: str

class ChatQuery(BaseModel):
    message: str


def fetch_ai_brain_reply(user_text: str) -> str:
    """Queries Gemini API, local skills, or Ollama fallback model."""
    if not user_text:
        return "I received an empty query, sir."

    # 1. Quick Local Skills
    q = user_text.lower()
    if "time" in q:
        import datetime
        return f"The current local time is {datetime.datetime.now().strftime('%I:%M %p')}, sir."
    if "date" in q:
        import datetime
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}, sir."
    if "weather" in q:
        try:
            res = requests.get("https://wttr.in?format=%C+%t", timeout=3)
            if res.status_code == 200:
                return f"Current weather: {res.text.strip()}, sir."
        except Exception:
            pass

    # 2. Try Gemini API
    cfg = load_config()
    gemini_key = cfg.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if gemini_key:
        models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash-8b"]
        system_prompt = "You are JARVIS, a highly intelligent, polite, and concise AI assistant. Keep answers brief (1 to 3 sentences max)."
        for model in models:
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                payload = {"contents": [{"parts": [{"text": f"{system_prompt}\nUser: {user_text}\nJARVIS:"}]}]}
                res = requests.post(gemini_url, json=payload, timeout=6)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception as e:
                print(f"[Gemini Error on {model}]: {e}")

    # 3. [P1 Fix]: Real Ollama local LLM fallback execution
    try:
        system_prompt = "You are JARVIS, a polite and concise assistant."
        payload = {
            "model": DEFAULT_MODEL,
            "prompt": f"{system_prompt}\n\nUser: {user_text}\nJARVIS:",
            "stream": False
        }
        res = requests.post(OLLAMA_URL, json=payload, timeout=8)
        if res.status_code == 200:
            ollama_reply = res.json().get("response", "").strip()
            if ollama_reply:
                return ollama_reply
    except Exception as e:
        print(f"[Ollama Fallback Offline]: {e}")

    # 4. Final Fallback
    return f"I processed your message ('{user_text}'), sir. All brain models are currently unreachable."


def process_query_with_brain(user_text: str) -> str:
    """Saves to database memory and returns AI reply."""
    database.save_conversation("User", user_text)
    reply = fetch_ai_brain_reply(user_text)
    database.save_conversation("JARVIS", reply)
    return reply


def verify_auth(request: Request, x_jarvis_token: str = Header(None)):
    """
    Security Check:
    - [P0 Fix]: Loopback (localhost) calls are allowed without token.
    - [P0 Fix]: Fails CLOSED for remote calls if AUTH_TOKEN is absent/unconfigured.
    """
    client_ip = request.client.host if request.client else ""
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        return

    cfg = load_config()
    token_to_check = cfg.get("AUTH_TOKEN") or os.environ.get("JARVIS_AUTH_TOKEN")

    if not token_to_check:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Remote authentication is not configured on server (AUTH_TOKEN missing)."
        )

    if x_jarvis_token != token_to_check:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid JARVIS Security Token")


@app.get("/health")
def health_check():
    return {"status": "online", "system": "JARVIS Backend", "version": "1.4"}


@app.get("/", response_class=HTMLResponse)
def get_web_dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "ripple_overlay.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>JARVIS Backend Active</h1>")


@app.post("/ask")
def ask_endpoint(payload: AskQuery, request: Request, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    reply = process_query_with_brain(payload.text)
    return {"reply": reply}


@app.post("/api/chat")
def chat_endpoint(query: ChatQuery, request: Request, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    reply = process_query_with_brain(query.message)
    return {"response": reply}


# [P0 Fix]: Added verify_auth to protect chat history from unauthorized remote callers
@app.get("/api/history")
def history_endpoint(request: Request, limit: int = 10, x_jarvis_token: str = Header(None)):
    verify_auth(request, x_jarvis_token)
    return {"history": database.get_recent_conversations(limit)}


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            reply = process_query_with_brain(data)
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    print("==========================================================")
    print("[START] HARDENED JARVIS SERVER RUNNING!")
    print(" - Local Access:       http://localhost:8000")
    print("==========================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000)
