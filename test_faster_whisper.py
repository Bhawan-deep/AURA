import torch 
import sounddevice as sd 
import numpy as np 
import tempfile
import os
import wavio 
from faster_whisper import WhisperModel 

# Initialize the English-only model
model = WhisperModel("base.en", device="cuda" if torch.cuda.is_available() else "cpu")

# Audio recording settings
SAMPLE_RATE = 16000
DURATION = 5  # seconds per recording

def record_audio(duration=DURATION, fs=SAMPLE_RATE):
    """Record audio for a fixed duration"""
    print("\n🎙 Speak now...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    return np.squeeze(audio)

while True:
    # Record voice
    audio_data = record_audio()

    # Save temporary audio file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        wavio.write(tmp_file.name, audio_data, SAMPLE_RATE, sampwidth=2)
        audio_path = tmp_file.name

    # Transcribe using Faster Whisper
    segments, info = model.transcribe(audio_path, beam_size=5)
    print("\n🗣 Transcribed text:")
    for segment in segments:
        print(segment.text, end=" ", flush=True)

    # Clean up temp file
    os.remove(audio_path)

    # Ask to continue
    cont = input("\n\nPress Enter to record again or type 'q' to quit: ")
    if cont.lower().startswith("q"):
        print("👋 Exiting live recognition.")
        break