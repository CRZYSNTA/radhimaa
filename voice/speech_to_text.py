"""
JARVIS V3.0 Voice: Speech-to-Text Engine
Supports offline local transcription via faster-whisper with automatic fallback
to Google STT. Handles dynamic ambient noise calibration, AGC software gain normalization,
and Realtek stereo microphone arrays with zero-delay loops.
"""

import io
import os
import time
import wave
import logging
from collections import deque
from typing import Optional
import numpy as np
import pyaudio
import speech_recognition as sr
import config

logger = logging.getLogger("JARVIS.Voice.STT")

_whisper_model = None
_shared_recognizer = None
_is_calibrated = False

def get_recognizer() -> sr.Recognizer:
    """Returns singleton recognizer with clamped thresholds."""
    global _shared_recognizer
    if _shared_recognizer is None:
        _shared_recognizer = sr.Recognizer()
        _shared_recognizer.pause_threshold = 0.6
        _shared_recognizer.non_speaking_duration = 0.3
        # Disable drifting dynamic threshold that locks up on Realtek mic arrays
        _shared_recognizer.dynamic_energy_threshold = False
        _shared_recognizer.energy_threshold = 350
    return _shared_recognizer

def normalize_audio(audio_np: np.ndarray, target_peak: float = 24000.0, max_gain: float = 12.0) -> np.ndarray:
    """
    Applies software digital pre-amplification (Automatic Gain Control) to quiet microphone input.
    Prevents Whisper and STT engines from discarding low-amplitude speech without clipping.
    """
    if len(audio_np) == 0:
        return audio_np
    current_peak = float(np.max(np.abs(audio_np)))
    if current_peak < 80.0:  # Below audible room noise / pure silence
        return audio_np
    gain = min(target_peak / current_peak, max_gain)
    if gain > 1.0:
        boosted = np.clip(audio_np.astype(np.float32) * gain, -32768.0, 32767.0)
        return boosted.astype(np.int16)
    return audio_np

def is_repetition_hallucination(text: str, max_consecutive_repeats: int = 3) -> bool:
    """
    Detects if text is a Whisper hallucination characterized by repetitive n-grams.
    E.g. "i'm not gonna get you. i'm not gonna get you. i'm not gonna get you."
    """
    if not text:
        return False
    import re
    clean = re.sub(r'[^\w\s]', '', text.lower()).strip()
    words = clean.split()
    if not words:
        return False

    n_words = len(words)
    # Check for n-gram repetitions (from 1-word up to 8-word phrases)
    for n in range(1, min(9, n_words // 2 + 1)):
        for i in range(n_words - n):
            pattern = words[i:i+n]
            repeats = 1
            idx = i + n
            while idx + n <= n_words and words[idx:idx+n] == pattern:
                repeats += 1
                idx += n
                if repeats >= max_consecutive_repeats:
                    return True

    # Check for vocabulary collapse on long outputs
    if n_words >= 8:
        unique_ratio = len(set(words)) / n_words
        if unique_ratio < 0.35:
            return True

    return False

def get_whisper_model():
    """Lazily load faster-whisper model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            model_name = getattr(config, "WHISPER_MODEL", "base")
            logger.info(f"[STT] Loading faster-whisper model '{model_name}' on CPU (int8)...")
            _whisper_model = WhisperModel(model_name, device="cpu", compute_type="int8")
            logger.info("[STT] faster-whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"[STT] Failed to load faster-whisper: {e}")
            _whisper_model = False
    return _whisper_model if _whisper_model is not False else None

logging.getLogger("faster_whisper").setLevel(logging.WARNING)

def transcribe_pcm(pcm_bytes: bytes, sample_rate: int = 16000) -> str:
    """
    Transcribes raw 16-bit PCM bytes.
    First applies software digital pre-amplification.
    If silent, returns immediately without wasting CPU.
    Then attempts fast transcription via faster-whisper (offline local) or Google STT.
    """
    if not pcm_bytes:
        return ""

    try:
        # Ensure even byte count for 16-bit PCM
        if len(pcm_bytes) % 2 != 0:
            pcm_bytes = pcm_bytes[:-1]

        audio_np_raw = np.frombuffer(pcm_bytes, dtype=np.int16)
        if len(audio_np_raw) == 0:
            return ""

        # Resample to 16000 Hz if sample_rate is different (e.g. 44100 or 48000 Hz)
        if sample_rate != 16000 and len(audio_np_raw) > 1:
            target_samples = int(len(audio_np_raw) * 16000 / sample_rate)
            if target_samples > 0:
                audio_np_raw = np.interp(
                    np.linspace(0, len(audio_np_raw), target_samples, endpoint=False),
                    np.arange(len(audio_np_raw)),
                    audio_np_raw
                ).astype(np.int16)

        # Apply software gain boost
        audio_boosted = normalize_audio(audio_np_raw)
        rms = float(np.sqrt(np.mean(audio_boosted.astype(np.float32)**2)))
        if rms < 120.0:  # Audible speech energy threshold
            return ""
        pcm_bytes = audio_boosted.tobytes()
    except Exception as e:
        logger.debug(f"[STT Prep Exception]: {e}")
        audio_boosted = None

    # Method 1: faster-whisper (offline local - prioritized)
    if config.USE_LOCAL_STT:
        model = get_whisper_model()
        if model:
            try:
                if audio_boosted is not None:
                    audio_float = audio_boosted.astype(np.float32) / 32768.0
                else:
                    audio_float = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                
                # 1. Voice Activity Detection (VAD) Pre-filter
                # Prevents sending non-speech ambient room noise (fans/AC) to Whisper
                try:
                    from faster_whisper.vad import get_speech_timestamps, VadOptions
                    speech_chunks = get_speech_timestamps(
                        audio_float,
                        vad_options=VadOptions(threshold=0.45, min_speech_duration_ms=180)
                    )
                    if not speech_chunks:
                        # Audio contains purely ambient noise, fan hiss, or silence
                        return ""
                except Exception as vad_err:
                    logger.debug(f"[VAD pre-filter notice]: {vad_err}")

                # 2. Transcribe with hardened hallucination rejection thresholds
                segments, info = model.transcribe(
                    audio_float,
                    beam_size=1,
                    language="en",
                    temperature=0.0,
                    vad_filter=False,  # Already pre-filtered above
                    condition_on_previous_text=False,
                    compression_ratio_threshold=2.2,
                    log_prob_threshold=-0.8,
                    no_speech_threshold=0.6,
                    repetition_penalty=1.1,
                    hallucination_silence_threshold=2.0
                )
                
                # 3. Filter segments by confidence and compression ratio
                clean_texts = []
                for seg in segments:
                    if getattr(seg, "no_speech_prob", 0.0) > 0.6:
                        continue
                    if getattr(seg, "avg_logprob", 0.0) < -1.0:
                        continue
                    if getattr(seg, "compression_ratio", 0.0) > 2.2:
                        continue
                    clean_texts.append(seg.text)

                text = " ".join(clean_texts).strip().lower()

                # 4. Post-transcription repetition filter
                if is_repetition_hallucination(text):
                    logger.warning(f"[STT] Discarded repetition hallucination: '{text}'")
                    return ""

                if text:
                    logger.info(f"[STT:Whisper] '{text}'")
                    return text
            except Exception as e:
                logger.warning(f"[STT] Whisper error, falling back to Google: {e}")

    # Method 2: Google STT (fallback or if local STT disabled)
    try:
        recognizer = get_recognizer()
        audio_data = sr.AudioData(pcm_bytes, 16000, 2)
        text = recognizer.recognize_google(audio_data, language="en-US").lower()
        if text and not is_repetition_hallucination(text):
            logger.info(f"[STT:Google] '{text}'")
            return text
    except Exception:
        pass

    return ""

def _get_best_mic_index() -> Optional[int]:
    """
    Returns index of best available microphone, strictly excluding system audio
    loopback devices (Stereo Mix, Wave Out, What U Hear, Virtual Cables).
    """
    bad_keywords = ["stereo mix", "wave out", "what u hear", "loopback", "virtual", "cable", "camo"]
    try:
        # Check system default input first
        p = pyaudio.PyAudio()
        try:
            def_info = p.get_default_input_device_info()
            def_name = def_info.get("name", "").lower()
            if not any(bad in def_name for bad in bad_keywords):
                return def_info.get("index")
        except Exception:
            pass
        finally:
            p.terminate()

        names = sr.Microphone.list_microphone_names()
        # Priority 1: Realtek Microphone Array
        for i, name in enumerate(names):
            n = name.lower()
            if any(bad in n for bad in bad_keywords):
                continue
            if "microphone array" in n and "realtek" in n:
                return i

        # Priority 2: Any Realtek physical microphone
        for i, name in enumerate(names):
            n = name.lower()
            if any(bad in n for bad in bad_keywords):
                continue
            if "realtek" in n and "mic" in n:
                return i

        # Priority 3: Sound Mapper input
        for i, name in enumerate(names):
            n = name.lower()
            if any(bad in n for bad in bad_keywords):
                continue
            if "sound mapper - input" in n:
                return i

        # Priority 4: Any non-loopback device with 'mic' or 'input'
        for i, name in enumerate(names):
            n = name.lower()
            if not any(bad in n for bad in bad_keywords) and ("mic" in n or "input" in n):
                return i
    except Exception:
        pass
    return None

def _get_mic_channels(device_index: Optional[int]) -> int:
    """Returns optimal channel count for microphone."""
    if device_index is None:
        return 2
    try:
        names = sr.Microphone.list_microphone_names()
        if device_index < len(names):
            name = names[device_index].lower()
            if "microphone array" in name or "stereo" in name:
                return 2
    except Exception:
        pass
    return 2

def listen_to_user(device_index: Optional[int] = None) -> str:
    """Captures microphone input with minimal latency and automatic gain compensation."""
    # Ensure speaker output has finished completely before opening microphone
    try:
        from voice.text_to_speech import is_speaking
        while is_speaking():
            time.sleep(0.1)
    except Exception:
        pass

    global _is_calibrated
    recognizer = get_recognizer()
    
    mic_index = device_index if device_index is not None else _get_best_mic_index()
    channels = _get_mic_channels(mic_index)
    
    # Use PyAudio stereo-to-mono for Realtek arrays and multi-channel mics
    if channels >= 2 or mic_index is not None:
        try:
            return _listen_stereo_to_mono(recognizer, mic_index)
        except Exception as e:
            logger.debug(f"[PyAudio Capture Error, falling back to sr.Microphone]: {e}")
    
    # Standard microphone fallback
    try:
        with sr.Microphone(device_index=mic_index) as source:
            if not _is_calibrated:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                # Clamp energy threshold to prevent lockup
                recognizer.energy_threshold = max(350, min(recognizer.energy_threshold, 900))
                _is_calibrated = True

            audio = recognizer.listen(source, timeout=2.5, phrase_time_limit=8.0)
            pcm_bytes = audio.get_raw_data()
            text = transcribe_pcm(pcm_bytes, sample_rate=audio.sample_rate)
            if text:
                print(f"[YOU SAID]: '{text}'")
            return text
    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return ""
    except Exception as e:
        logger.debug(f"[Mic Note]: {e}")
        return ""

def _listen_stereo_to_mono(recognizer: sr.Recognizer, device_index: Optional[int]) -> str:
    """
    Records stereo from microphone, downmixes to mono, applies software pre-amplification,
    and returns transcribed text with minimal latency without 8-second buffering hangs.
    """
    RATE = 44100
    CHUNK = 1024
    CHANNELS = 2
    FORMAT = pyaudio.paInt16
    
    p = pyaudio.PyAudio()
    stream = None
    try:
        open_kwargs = {
            "format": FORMAT,
            "channels": CHANNELS,
            "rate": RATE,
            "input": True,
            "frames_per_buffer": CHUNK
        }
        if device_index is not None:
            open_kwargs["input_device_index"] = device_index
            
        stream = p.open(**open_kwargs)
        
        # Adaptive ambient baseline calibration across ~0.28s (12 chunks)
        ambient_frames = []
        for _ in range(12):
            ambient_frames.append(stream.read(CHUNK, exception_on_overflow=False))
            
        amb_raw = np.frombuffer(b"".join(ambient_frames), dtype=np.int16).reshape(-1, 2)
        amb_mono = ((amb_raw[:, 0].astype(np.int32) + amb_raw[:, 1].astype(np.int32)) // 2).astype(np.float32)
        amb_rms = float(np.sqrt(np.mean(amb_mono**2)))
        
        # Adaptive speech onset and silence thresholds calibrated to exclude ambient noise (fans/AC)
        speech_thresh = max(450.0, min(amb_rms * 1.6, 1200.0))
        silence_thresh = max(300.0, min(amb_rms * 1.25, 800.0))
        
        frames = []
        pre_roll = deque(maxlen=6)  # ~140ms pre-speech buffer to prevent clipping first syllable
        speech_started = False
        silence_count = 0
        start_time = time.time()
        timeout = 2.2  # Exit quickly if no speech starts (prevents capturing ambient noise)
        phrase_limit = 8.0  # Max duration once speaking
        
        while True:
            elapsed = time.time() - start_time
            if not speech_started and elapsed > timeout:
                break
            if elapsed > phrase_limit:
                break
                
            data = stream.read(CHUNK, exception_on_overflow=False)
            chunk_raw = np.frombuffer(data, dtype=np.int16).reshape(-1, 2)
            # High quality channel averaging (L + R) // 2
            mono_chunk = ((chunk_raw[:, 0].astype(np.int32) + chunk_raw[:, 1].astype(np.int32)) // 2).astype(np.float32)
            rms = float(np.sqrt(np.mean(mono_chunk**2)))
            
            if not speech_started:
                pre_roll.append(data)
                if rms > speech_thresh:
                    speech_started = True
                    frames.extend(pre_roll)
                    frames.append(data)
            else:
                frames.append(data)
                if rms < silence_thresh:
                    silence_count += 1
                    if silence_count > 15:  # ~0.35s silence ends speech cleanly
                        break
                else:
                    silence_count = max(0, silence_count - 1)
                    
        stream.stop_stream()
        stream.close()
        p.terminate()
        stream = None
        
        if not frames or not speech_started:
            return ""
            
        # Convert captured stereo frames to mono 16kHz for STT
        raw_stereo = b"".join(frames)
        trim_len = len(raw_stereo) - (len(raw_stereo) % 4)
        if trim_len == 0:
            return ""
        audio_stereo = np.frombuffer(raw_stereo[:trim_len], dtype=np.int16).reshape(-1, 2)
        mono_44k = ((audio_stereo[:, 0].astype(np.int32) + audio_stereo[:, 1].astype(np.int32)) // 2).astype(np.int16)
        
        TARGET_RATE = 16000
        num_target_samples = int(len(mono_44k) * TARGET_RATE / RATE)
        mono_16k = np.interp(
            np.linspace(0, len(mono_44k), num_target_samples, endpoint=False),
            np.arange(len(mono_44k)),
            mono_44k
        ).astype(np.int16)
        
        # Apply software digital gain boost
        boosted_16k = normalize_audio(mono_16k)
        text = transcribe_pcm(boosted_16k.tobytes(), sample_rate=TARGET_RATE)
        if text:
            print(f"[YOU SAID]: '{text}'")
        return text
        
    except Exception as e:
        logger.debug(f"[Mic Stereo Note]: {e}")
        return ""
    finally:
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        try:
            p.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    print("Testing fast speech listener...")
    txt = listen_to_user()
    print("Recognized:", txt)