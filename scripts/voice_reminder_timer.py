"""
Voice-Based Reminder Assistant

This script allows users to set spoken reminders using voice commands. It listens for a command like
"Remind me in 2 minutes that I have a meeting", extracts the time and message, and triggers a popup
notification with text-to-speech feedback after the specified duration.

Features:
- Voice recognition using Google Speech Recognition API
- Natural language time extraction (minutes and seconds)
- Text-to-speech confirmation and reminder playback
- GUI popup reminder using Tkinter
- Emoji-safe speech output

Usage:
Run the script and speak a command such as:
    "Remind me in 5 minutes that I need to stretch"
    "Remind me in 30 seconds that my tea is ready"

Dependencies:
- speech_recognition
- pyttsx3
- tkinter (standard library)
- pyaudio (for microphone input)

Note:
Ensure your microphone is connected and accessible. Internet is required for Google Speech Recognition.
"""

import speech_recognition as sr # pyright: ignore[reportMissingImports]
import pyttsx3 # pyright: ignore[reportMissingImports]
import time
import re
import tkinter as tk
from threading import Timer

# Initialize recognizer and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    # Speak the text (remove emojis before speaking)
    clean_text = re.sub(r'[^\w\s,.!?]', '', text)
    engine.say(clean_text)
    engine.runAndWait()

def show_popup(message):
    # Create a beautiful popup using tkinter
    popup = tk.Tk()
    popup.title("[Reminder] AI Health Reminder")
    popup.geometry("400x250")
    popup.configure(bg="#eaf6f6")
    popup.attributes('-topmost', True)  # Make sure it appears on top

    label = tk.Label(
        popup,
        text=message,
        font=("Arial Rounded MT Bold", 16),
        fg="#2c3e50",
        bg="#eaf6f6",
        wraplength=350,
        justify="center"
    )
    label.pack(expand=True, pady=30)

    ok_button = tk.Button(
        popup,
        text="OK",
        command=popup.destroy,
        font=("Arial", 12),
        bg="#4caf50",
        fg="white",
        relief="raised",
        width=10
    )
    ok_button.pack(pady=10)

    popup.mainloop()

def extract_time(text):
    # Extract time and convert to seconds
    text = text.lower()
    seconds = 0
    minute_match = re.search(r'(\d+)\s*minute', text)
    second_match = re.search(r'(\d+)\s*second', text)

    if minute_match:
        seconds += int(minute_match.group(1)) * 60
    if second_match:
        seconds += int(second_match.group(1))
    return seconds

# Older version, will not be used now
def listen_and_set_reminder():
    with sr.Microphone() as source:
        print("[LISTENING] Listening for your reminder command...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"[RECOGNIZED] You said: {command}")

            # Extract time and message
            duration = extract_time(command)
            message_match = re.search(r'remind me .? that (.)', command, re.IGNORECASE)

            if duration == 0 or not message_match:
                speak("Sorry, I couldn't understand the time or message.")
                return

            reminder_message = message_match.group(1)
            speak(f"Got it! I'll remind you in {duration} seconds to {reminder_message}.")

            # Wait for the duration, then show popup
            def trigger_popup():
                show_popup(f"[REMINDER] Reminder: {reminder_message}")
                speak(reminder_message)

            Timer(duration, trigger_popup).start()

        except sr.UnknownValueError:
            print("[ERROR] Sorry, I couldn't understand the audio.")
        except sr.RequestError:
            print("[WARNING] Speech service unavailable.")

def main(duration: int = 300, message: str = "Time to take a break"):
    """Entry point for reminder execution via dispatcher."""
    speak(f"Got it! I'll remind you in {duration} seconds to {message}.")
    def trigger_popup():
        show_popup(f"[REMINDER] Reminder: {message}")
        speak(message)
    Timer(duration, trigger_popup).start()
