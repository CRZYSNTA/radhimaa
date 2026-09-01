"""
=============================================================================
JARVIS Dual Calling Engine (Synchronized Thread-Safe Triggers)
=============================================================================
Fixes Applied:
 - [P2 Fix]: Thread-safe synchronization lock around trigger_jarvis to prevent race conditions.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import math
import struct
import sys
import threading
import time
import numpy as np
import pyaudio
import speech_recognition as sr
import audio_feedback

try:
    import jarvis_stage1
except Exception:
    jarvis_stage1 = None


class DualTriggerEngine:
    def __init__(self, clap_threshold=1200, min_clap_interval=0.12, max_clap_interval=0.75):
        self.clap_threshold = clap_threshold
        self.min_clap_interval = min_clap_interval
        self.max_clap_interval = max_clap_interval
        
        self.last_clap_time = 0
        self.is_active = False
        self._lock = threading.Lock()  # [P2 Fix]: Synchronization lock

    def calculate_audio_energy(self, audio_data):
        count = len(audio_data) / 2
        if count == 0:
            return 0
        format_str = "%dh" % count
        try:
            shorts = struct.unpack(format_str, audio_data)
            sum_squares = 0.0
            for sample in shorts:
                n = sample / 32768.0
                sum_squares += n * n
            rms = math.sqrt(sum_squares / count)
            return rms * 10000
        except Exception:
            return 0

    def trigger_jarvis(self, trigger_source="Double Clap"):
        """Thread-safe activation of JARVIS voice interaction."""
        with self._lock:  # [P2 Fix]: Race condition protection
            if self.is_active:
                return
            self.is_active = True

        print(f"\n⚡ SUMMONED via [{trigger_source}]!")
        
        try:
            audio_feedback.play_instant_yes_sir()
            if jarvis_stage1:
                user_text = jarvis_stage1.listen_to_user()
                if user_text:
                    reply = jarvis_stage1.query_brain(user_text)
                    jarvis_stage1.speak(reply)
            else:
                print(f"🤖 JARVIS: Triggered via {trigger_source}!")
                time.sleep(2)
        finally:
            with self._lock:
                self.is_active = False

    def listen_for_claps(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            print("[OK] Double-Clap Listener Active (Clap twice to summon)")

            while True:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    energy = self.calculate_audio_energy(data)

                    if energy > self.clap_threshold:
                        current_time = time.time()
                        time_delta = current_time - self.last_clap_time

                        if self.min_clap_interval < time_delta < self.max_clap_interval:
                            self.trigger_jarvis("Double-Clap Sound")
                            self.last_clap_time = 0
                            time.sleep(1)
                        else:
                            self.last_clap_time = current_time

                except Exception:
                    time.sleep(0.05)

        except Exception as e:
            print(f"[Clap Detector Error]: {e}")
        finally:
            p.terminate()

    def listen_for_wake_word(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[OK] Voice Listener Active (Say 'Jarvis' to summon)")
            
            while True:
                try:
                    audio = recognizer.listen(source, timeout=4, phrase_time_limit=3)
                    text = recognizer.recognize_google(audio).lower()
                    if "jarvis" in text:
                        self.trigger_jarvis("Voice Command 'Jarvis'")
                except Exception:
                    pass

    def start(self):
        t1 = threading.Thread(target=self.listen_for_claps, daemon=True)
        t2 = threading.Thread(target=self.listen_for_wake_word, daemon=True)
        
        t1.start()
        t2.start()
        
        print("==========================================================")
        print("[OK] THREAD-SAFE DUAL SUMMONING ENGINE ACTIVE")
        print("==========================================================")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping Dual Summoning Engine.")

if __name__ == "__main__":
    engine = DualTriggerEngine()
    engine.start()
