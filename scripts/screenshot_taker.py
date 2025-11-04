import mss
import datetime
import os

"""
Screenshot Taker Utility

This script captures a screenshot of the primary monitor and saves it to the user's Pictures/Screenshots folder
with a timestamped filename. It uses the `mss` library for cross-platform screen capture and ensures the output
directory exists before saving.

Functions:
- take_screenshot(): Captures and saves a screenshot with a unique timestamp.

Usage:
Run this script directly to take a screenshot:
    python screenshot_taker.py

The saved image will be named like 'screenshot_2025-11-04_05-41-02.png' and stored in:
    ~/Pictures/Screenshots
"""


def take_screenshot():
    folder = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
    os.makedirs(folder, exist_ok=True)

    # Create timestamp for unique filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(folder, f"screenshot_{timestamp}.png")

    # Take the screenshot
    with mss.mss() as sct:
        sct.shot(output=file_path)

    print(f"Screenshot saved as: {file_path}")

# Example usage
if __name__ == "__main__":
    print("Taking screenshot...")
    take_screenshot()