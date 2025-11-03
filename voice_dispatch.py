import os
import torch
import sounddevice as sd
import numpy as np
import scipy.io.wavfile
from faster_whisper import WhisperModel
import dispatcher as disp

# Configuration
SAMPLE_RATE = 16000
DURATION = 5
AUDIO_PATH = "input.wav"
MODEL_SIZE = "base.en"  # English-only, faster and safer
DEVICE = "cpu"          # Force CPU to avoid cuDNN errors
COMPUTE_TYPE = "int8"

# Initialize model once
model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)

def record_voice(filename=AUDIO_PATH, duration=DURATION, samplerate=SAMPLE_RATE):
    print("🎙 Speak now...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    scipy.io.wavfile.write(filename, samplerate, audio)

def transcribe_and_dispatch():
    record_voice()
    segments, _ = model.transcribe(AUDIO_PATH, beam_size=5)
    user_input = " ".join([seg.text for seg in segments])
    print(f"🗣 Transcribed: {user_input}")
    disp.dispatch(user_input)
    if os.path.exists(AUDIO_PATH):
        os.remove(AUDIO_PATH)