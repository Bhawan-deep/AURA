import mss
import datetime
import os

def take_screenshot():
    folder = r"C:\Users\mohan\OneDrive\Pictures\Screenshots"
    os.makedirs(folder, exist_ok=True)

    # Create timestamp for unique filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(folder, f"screenshot_{timestamp}.png")

    # Take the screenshot
    with mss.mss() as sct:
        sct.shot(output=file_path)

    print(f"✅ Screenshot saved as: {file_path}")

# Example usage
if __name__ == "__main__":
    print("📸 Taking screenshot...")
    take_screenshot()
