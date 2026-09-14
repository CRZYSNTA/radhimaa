"""
=============================================================================
JARVIS Voice: Acoustic Double-Clap Detection Engine
=============================================================================
Goal: Listens to raw mic stream, calculates RMS audio energy peaks, and triggers
      when a double-clap pattern (Clap... Clap!) is detected within 0.15s - 0.7s.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import sys
import time
import numpy as np
import pyaudio
import pygame

class DualTriggerEngine:
    """Listens for acoustic double-clap pattern on default microphone."""
    def __init__(self):
        self.RATE = 44100
        self.CHUNK = 1024
        self.CLAP_THRESHOLD = 2500  # RMS threshold for clap detection
        self.running = False

    def start(self, callback=None):
        self.running = True
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            last_clap_time = 0

            while self.running:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))

                if rms > self.CLAP_THRESHOLD:
                    now = time.time()
                    time_diff = now - last_clap_time
                    if 0.15 < time_diff < 0.7:
                        print("\n[CLAP ENGINE]: Double-Clap Detected! (Clap... Clap!)")
                        if callback:
                            callback()
                        last_clap_time = 0
                    else:
                        last_clap_time = now

            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            print(f"[Clap Engine Stream Note]: {e}")
            try:
                p.terminate()
            except Exception:
                pass

    def stop(self):
        self.running = False

if __name__ == "__main__":
    print("Testing Acoustic Double-Clap Detector...")
    engine = DualTriggerEngine()
    engine.start()
