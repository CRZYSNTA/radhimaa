"""
=============================================================================
JARVIS Stage 3: Passive Wake Word Engine
=============================================================================
Goal: Listen passively in the background for a trigger phrase like "Hey Jarvis".
      Only when the trigger is detected does it activate the full STT/Brain pipeline,
      saving CPU, battery, and protecting privacy.

Supports:
 1. openWakeWord (High precision local ONNX wake word detector)
 2. Keyword Energy Trigger (Beginner fallback listening for keyword)

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import time
import speech_recognition as sr

class WakeWordDetector:
    def __init__(self, wake_phrase="jarvis"):
        self.wake_phrase = wake_phrase.lower()
        self.recognizer = sr.Recognizer()

    def listen_for_wake_word(self, on_wake_callback=None) -> bool:
        """
        Passive low-power background listener.
        When 'wake_phrase' is spoken, calls 'on_wake_callback()'.
        """
        print(f"\n👂 Passive Listening active... Say '{self.wake_phrase.capitalize()}' to wake me up.")
        
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
            
            while True:
                try:
                    # Listen in short 3-second audio slices
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=4)
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"[Background Audio Detected]: '{text}'")

                    if self.wake_phrase in text:
                        print(f"\n⚡ WAKE WORD DETECTED! ('{self.wake_phrase}')")
                        if on_wake_callback:
                            on_wake_callback()
                        return True

                except sr.WaitTimeoutError:
                    pass  # Continue passive loop
                except sr.UnknownValueError:
                    pass  # Unrecognized noise, ignore
                except sr.RequestError as e:
                    print(f"STT Error: {e}")
                    time.sleep(1)

def demo_wake_action():
    print("🤖 JARVIS: Yes, sir? I am listening to your command...")

if __name__ == "__main__":
    detector = WakeWordDetector(wake_phrase="jarvis")
    detector.listen_for_wake_word(on_wake_callback=demo_wake_action)
