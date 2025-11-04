import os
import sys
import time
import logging
import tempfile
from typing import Optional
from intent_parser import parse_command

import torch
import sounddevice as sd
import numpy as np
import scipy.io.wavfile
from faster_whisper import WhisperModel

import dispatcher as disp

# Configuration (override with env vars if needed)
SAMPLE_RATE = int(os.getenv("AURA_SAMPLE_RATE", "16000"))
DURATION = int(os.getenv("AURA_DURATION", "5"))
AUDIO_PATH = os.getenv("AURA_AUDIO_PATH", "input.wav")
MODEL_SIZE = os.getenv("AURA_MODEL_SIZE", "base.en")  # prefer English-only for safety
FORCE_DEVICE = os.getenv("AURA_DEVICE", "")  # set to "cpu" or "cuda" to override auto-detection
COMPUTE_TYPE = os.getenv("AURA_COMPUTE_TYPE", "int8")
BEAM_SIZE = int(os.getenv("AURA_BEAM_SIZE", "5"))
LOG_PATH = os.getenv("AURA_LOG_PATH", "logs/voice_dispatch.log")

# Logging
os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
logger = logging.getLogger("voice_dispatch")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_PATH)
handler.setFormatter(logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s"))
logger.addHandler(handler)

_model: Optional[WhisperModel] = None
_model_device: Optional[str] = None

def _detect_device() -> str:
    if FORCE_DEVICE:
        return FORCE_DEVICE
    try:
        import torch  # re-import for environments where torch isn't present at module import
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def get_model() -> WhisperModel:
    """Lazy-load and return the WhisperModel singleton."""
    global _model, _model_device
    if _model is None:
        device = _detect_device()
        # Attempt GPU then fallback to CPU if GPU initialization fails
        if device == "cuda":
            try:
                _model = WhisperModel(MODEL_SIZE, device="cuda", compute_type=COMPUTE_TYPE)
                _model_device = "cuda"
            except Exception as e:
                logger.warning("GPU model init failed, falling back to CPU: %s", e)
                _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)
                _model_device = "cpu"
        else:
            _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)
            _model_device = "cpu"
        logger.info("Loaded WhisperModel size=%s device=%s compute_type=%s", MODEL_SIZE, _model_device, COMPUTE_TYPE)
    return _model

def record_voice(filename: str = AUDIO_PATH, duration: int = DURATION, samplerate: int = SAMPLE_RATE) -> str:
    """Record a fixed-duration mono WAV and return the file path."""
    # Use a temp file if the configured AUDIO_PATH is not desired to persist
    use_temp = filename == "input.wav" and os.getenv("AURA_USE_TEMPFILE", "1") == "1"
    out_path = filename
    if use_temp:
        fd, out_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

    print("🎙 Speak now...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    scipy.io.wavfile.write(out_path, samplerate, audio)
    logger.info("Recorded audio to %s (duration=%ds, rate=%d)", out_path, duration, samplerate)
    return out_path

def _transcribe_file(path: str) -> str:
    model = get_model()
    segments, _ = model.transcribe(path, beam_size=BEAM_SIZE)
    text = " ".join([seg.text for seg in segments]).strip()
    logger.info("Transcription result for %s: %s", path, text.replace("\n", " "))
    return text

def transcribe_and_dispatch_once(duration: int = DURATION, samplerate: int = SAMPLE_RATE, cleanup: bool = True):
    """Record once, transcribe, dispatch, and optionally delete the audio file."""
    audio_path = None
    try:
        audio_path = record_voice(duration=duration, samplerate=samplerate)
        user_input = _transcribe_file(audio_path)
        if not user_input:
            print("No speech detected.")
            logger.info("No transcription text detected; skipping dispatch.")
            return
        print(f"🗣 Transcribed: {user_input}")
        logger.info("Dispatching user_input: %s", user_input)
        result = parse_command(user_input)
        if result:
            script_name, args = result
            disp.dispatch(script_name=script_name, args=args)
        else:
            disp.dispatch(user_input)
    except KeyboardInterrupt:
        logger.info("Interrupted by user during recording/transcription.")
        print("\nInterrupted.")
    except Exception as e:
        logger.exception("Error during transcribe_and_dispatch: %s", e)
        print(f"Error: {e}")
    finally:
        if cleanup and audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info("Removed audio file %s", audio_path)
            except Exception as e:
                logger.warning("Failed to remove audio file %s: %s", audio_path, e)

def live_loop():
    """Continuous voice loop: record -> transcribe -> dispatch -> confirm -> repeat/quit."""
    print("Entering live voice loop. Press Ctrl+C to exit.")
    while True:
        transcribe_and_dispatch_once()
        try:
            resp = input("\n↩ Press Enter to record again or type 'q' to quit: ").strip().lower()
            if resp.startswith("q"):
                print("Exiting voice loop.")
                break
        except KeyboardInterrupt:
            print("\nExiting voice loop.")
            break

# Allow CLI invocation: python -m voice_dispatch --live or --once
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AURA voice dispatch")
    parser.add_argument("--live", action="store_true", help="Enter continuous voice loop")
    parser.add_argument("--duration", type=int, default=DURATION, help="Record duration seconds")
    parser.add_argument("--samplerate", type=int, default=SAMPLE_RATE, help="Audio sample rate")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep recorded WAV on disk for debugging")
    args = parser.parse_args()
    if args.live:
        live_loop()
    else:
        transcribe_and_dispatch_once(duration=args.duration, samplerate=args.samplerate, cleanup=not args.no_cleanup)