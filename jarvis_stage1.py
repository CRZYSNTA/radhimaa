"""
=============================================================================
JARVIS Stage 1: Voice & Brain Engine (Config, Device Controls & Cloud AI)
=============================================================================
Goal: Listen to your voice, process thoughts via Local Ollama, Gemini API,
      or Device Actions (Lock Screen, Open Apps), and speak replies out loud.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import asyncio
import datetime
import json
import os
import sys
import tempfile
import requests
import speech_recognition as sr
import edge_tts
import pygame
import device_control

# --- CONFIGURATION ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """Loads configuration settings from config.json if available."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

config = load_config()
JARVIS_VOICE = config.get("JARVIS_VOICE", "en-GB-RyanNeural")
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = config.get("DEFAULT_MODEL", "llama3.2:1b")


# ---------------------------------------------------------------------------
# 1. TEXT-TO-SPEECH (TTS) - Making JARVIS Speak
# ---------------------------------------------------------------------------
async def speak_text_async(text: str):
    """Converts text into spoken audio using Microsoft Edge-TTS and plays it out loud."""
    print(f"\n🤖 JARVIS: {text}\n")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_filename = fp.name

    try:
        communicate = edge_tts.Communicate(text, JARVIS_VOICE)
        await communicate.save(temp_filename)

        pygame.mixer.init()
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        pygame.mixer.quit()

    except Exception as e:
        print(f"[TTS Error] Could not play audio: {e}")
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass

def speak(text: str):
    """Helper wrapper to run async speak function synchronously."""
    asyncio.run(speak_text_async(text))


# ---------------------------------------------------------------------------
# 2. SPEECH-TO-TEXT (STT) - Listening to Microphone
# ---------------------------------------------------------------------------
def listen_to_user() -> str:
    """Captures mic input, filters background noise, and converts speech to text."""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎤 Listening... (Speak into your microphone now)")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        try:
            audio_data = recognizer.listen(source, timeout=8, phrase_time_limit=10)
            print("⏳ Processing speech...")

            user_text = recognizer.recognize_google(audio_data)
            print(f"👤 You said: '{user_text}'")
            return user_text

        except sr.WaitTimeoutError:
            print("⚠️ Listening timed out. No speech detected.")
            return ""
        except sr.UnknownValueError:
            print("⚠️ Could not understand the audio clearly.")
            return ""
        except sr.RequestError as e:
            print(f"⚠️ Speech Recognition Service error: {e}")
            return ""


# ---------------------------------------------------------------------------
# 3. BUILT-IN QUICK UTILITIES (Time, Date, Weather)
# ---------------------------------------------------------------------------
def get_quick_skill_response(user_query: str) -> str:
    """Handles common local commands instantly without waiting for network AI."""
    q = user_query.lower()

    if "time" in q:
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current local time is {now}, sir."

    if "date" in q or "today's date" in q:
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {today}, sir."

    if "weather" in q:
        try:
            res = requests.get("https://wttr.in?format=%C+%t", timeout=4)
            if res.status_code == 200:
                weather_info = res.text.strip()
                return f"Current local weather conditions: {weather_info}, sir."
        except Exception:
            pass
        return "Weather conditions appear pleasant today, sir."

    if "who are you" in q or "your name" in q:
        return "I am JARVIS, your personal artificial intelligence assistant."

    return None


# ---------------------------------------------------------------------------
# 4. THE BRAIN (Device Controls / Skill Handlers / Gemini / Ollama)
# ---------------------------------------------------------------------------
def query_brain(prompt: str) -> str:
    """Queries device actions, quick skills, Gemini API, or local Ollama LLM."""
    # 1. Check for real device commands first (Lock Screen, Open Apps, Launch Gestures)
    device_action_reply = device_control.execute_device_command(prompt)
    if device_action_reply:
        return device_action_reply

    # 2. Check quick local skills (Time, Date, Weather)
    quick_reply = get_quick_skill_response(prompt)
    if quick_reply:
        return quick_reply

    system_prompt = (
        "You are JARVIS, a highly intelligent, polite, and concise AI assistant inspired by Iron Man. "
        "Keep answers brief (1 to 3 sentences max)."
    )

    # 3. Try Gemini Cloud API if API Key configured
    cfg = load_config()
    gemini_key = cfg.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if gemini_key:
        gemini_models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash-8b"]
        for model in gemini_models:
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\nUser: {prompt}\nJARVIS:"}]}]
                }
                res = requests.post(gemini_url, json=payload, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception as e:
                print(f"[Gemini API Error for {model}]: {e}")

    # 4. Try Local Ollama LLM on port 11434
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": f"{system_prompt}\n\nUser: {prompt}\nJARVIS:",
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=8)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception:
        pass

    # 5. Fallback response
    return f"I received your query: '{prompt}'. System online!"


# ---------------------------------------------------------------------------
# 5. MAIN INTERACTIVE LOOP
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("   🤖 WELCOME TO JARVIS STAGE 1: VOICE & BRAIN PROTOTYPE")
    print("=" * 60)
    
    speak("Systems initialized, sir. How may I assist you today?")

    while True:
        print("\nOptions: [1] Speak into Mic  [2] Type a message  [3] Exit")
        choice = input("Enter choice (1/2/3): ").strip()

        if choice == "3" or choice.lower() in ["exit", "quit"]:
            speak("Powering down system. Have a pleasant day, sir.")
            break

        user_input = ""
        if choice == "1":
            user_input = listen_to_user()
        elif choice == "2":
            user_input = input("👤 Type your question: ").strip()
        else:
            print("Invalid choice, please select 1, 2, or 3.")
            continue

        if not user_input:
            continue

        ai_response = query_brain(user_input)
        speak(ai_response)

if __name__ == "__main__":
    main()
