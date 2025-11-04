import win32gui
import win32con
from screeninfo import get_monitors
import math

def get_visible_windows():
    """Return list of (hwnd, title) for all visible windows with a title."""
    windows = []

    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((hwnd, title))

    win32gui.EnumWindows(enum_handler, None)
    return windows

def best_layout(n):
    """Return (rows, cols) for smallest grid that can contain n windows."""
    if n == 2:
        cols = 2
        rows = 1
    elif n < 5:
        cols = 2
        rows = 1
    elif n < 7:
        cols = 3
        rows = 2
    else:
        cols = 4
        rows = 2
    return rows, cols

def tile_windows():
    windows = get_visible_windows()
    n = len(windows)
    if n == 0:
        print("No windows found to tile.")
        return

    monitor = get_monitors()[0]
    screen_width, screen_height = monitor.width, monitor.height

    rows, cols = best_layout(n)
    tile_width = screen_width // cols
    tile_height = screen_height // rows

    for index, (hwnd, title) in enumerate(windows[:rows * cols]):
        r = index // cols
        c = index % cols
        x = c * tile_width
        y = r * tile_height
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.MoveWindow(hwnd, x, y, tile_width, tile_height, True)
        except Exception as e:
            print(f"Could not move/resize window '{title}': {e}")

    print(f"Tiled {min(n, rows * cols)} windows in {rows}x{cols} layout.")

if __name__ == "__main__":
    tile_windows()