"""
=============================================================================
JARVIS Stage 1: Fast Voice Engine & Gemini 3.6 Flash Brain
=============================================================================
Speed Optimizations:
 - pause_threshold = 0.5s for 2x faster STT response
 - Fast Gemini 3.6 Flash API timeouts
 - Async edge-tts neural voice generation

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import asyncio
import os
import sys
import json
import time
import requests
import speech_recognition as sr
import edge_tts
import pygame

try:
    import device_control
except Exception:
    device_control = None

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def listen_to_user():
    """Captures microphone speech with ultra-fast 0.5s silence detection."""
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.5  # Ultra-fast silence pause detection
    recognizer.energy_threshold = 300
    
    with sr.Microphone() as source:
        print("\n🎤 Listening to your voice...")
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            text = recognizer.recognize_google(audio).lower()
            print(f"🗣️ You said: '{text}'")
            return text
        except sr.WaitTimeoutError:
            print("[INFO] Listening timed out.")
            return ""
        except sr.UnknownValueError:
            print("[INFO] Could not understand audio.")
            return ""
        except Exception as e:
            print(f"[Error]: {e}")
            return ""

def speak(text):
    """Synthesizes Edge-TTS British neural voice speech and plays out loud."""
    if not text:
        return
    print(f"🤖 JARVIS: {text}")
    
    audio_file = os.path.join(os.path.dirname(__file__), "temp_response.mp3")

    async def _generate():
        communicate = edge_tts.Communicate(text, "en-GB-RyanNeural")
        await communicate.save(audio_file)

    try:
        asyncio.run(_generate())
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(20)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        if os.path.exists(audio_file):
            os.remove(audio_file)
    except Exception as e:
        print(f"[Speech Output Error]: {e}")

def query_brain(user_text):
    """Processes query against local skills, device actions, or Gemini 3.6 Flash."""
    if not user_text:
        return "I didn't catch that, sir."

    # 1. Device Action Commands
    if device_control and device_control.handle_voice_command(user_text):
        return "Executing command, sir."

    # 2. Fast Local Skills
    q = user_text.lower()
    if "time" in q:
        import datetime
        return f"The current local time is {datetime.datetime.now().strftime('%I:%M %p')}, sir."
    if "date" in q:
        import datetime
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}, sir."
    if "weather" in q:
        try:
            res = requests.get("https://wttr.in?format=%C+%t", timeout=2)
            if res.status_code == 200:
                return f"Current weather: {res.text.strip()}, sir."
        except Exception:
            pass

    # 3. Gemini 3.6 Flash API
    config = load_config()
    gemini_key = config.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if gemini_key:
        models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash-8b"]
        system_prompt = "You are JARVIS, a highly intelligent, polite, and concise AI assistant. Keep answers brief (1 to 2 sentences max)."
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                payload = {"contents": [{"parts": [{"text": f"{system_prompt}\nUser: {user_text}\nJARVIS:"}]}]}
                res = requests.post(url, json=payload, timeout=4)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception:
                pass

    return f"I received your query: '{user_text}'. Brain active, sir."

def main():
    speak("JARVIS systems online. How may I assist you today, sir?")
    while True:
        text = listen_to_user()
        if text:
            if "exit" in text or "quit" in text or "goodbye" in text:
                speak("Powering down systems. Good day, sir!")
                break
            reply = query_brain(text)
            speak(reply)

if __name__ == "__main__":
    main()
