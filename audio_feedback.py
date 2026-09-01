"""
=============================================================================
JARVIS Instant Audio & Chime Responder
=============================================================================
Goal: Pre-generates crisp voice responses ('yes_sir.mp3', 'listening.mp3')
      so that when JARVIS listens, he responds OUT LOUD INSTANTLY (0 delay)!

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import asyncio
import os
import edge_tts
import pygame

AUDIO_DIR = os.path.dirname(__file__)
YES_SIR_PATH = os.path.join(AUDIO_DIR, "yes_sir.mp3")

async def generate_prebaked_sounds():
    """Generates local MP3 files for instant playback."""
    if not os.path.exists(YES_SIR_PATH):
        try:
            communicate = edge_tts.Communicate("Yes, sir?", "en-GB-RyanNeural")
            await communicate.save(YES_SIR_PATH)
        except Exception:
            pass

def play_instant_yes_sir():
    """Plays 'Yes, sir?' immediately with zero network delay."""
    if os.path.exists(YES_SIR_PATH):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(YES_SIR_PATH)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            return
        except Exception:
            pass
    # Fallback to standard speak if file missing
    try:
        import jarvis_stage1
        jarvis_stage1.speak("Yes, sir?")
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(generate_prebaked_sounds())
    play_instant_yes_sir()
