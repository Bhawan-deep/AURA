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

def best_grid(n):
    """
    Compute best rows and columns for n windows to fill screen equally.
    Returns (rows, cols)
    """
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    # Adjust to minimize empty space
    while (rows-1)*cols >= n:
        rows -= 1
    return rows, cols

def tile_windows(layout="grid"):
    windows = get_visible_windows()
    n = len(windows)
    if n == 0:
        print("No windows found to tile.")
        return

    monitor = get_monitors()[0]
    screen_width, screen_height = monitor.width, monitor.height

    # Determine layout
    if layout == "grid":
        rows, cols = best_grid(n)
    elif layout == "horizontal":
        rows, cols = 1, n
    elif layout == "vertical":
        rows, cols = n, 1
    else:
        raise ValueError("Invalid layout type. Use 'grid', 'horizontal', or 'vertical'.")

    # Tile windows dynamically
    index = 0
    for r in range(rows):
        # Number of windows in this row
        if r == rows - 1:  # Last row
            windows_in_row = n - index
            if windows_in_row == 0:
                break
        else:
            windows_in_row = cols

        tile_width = screen_width // windows_in_row
        tile_height = screen_height // rows

        for c in range(windows_in_row):
            if index >= n:
                break
            hwnd, title = windows[index]
            x = c * tile_width
            y = r * tile_height
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.MoveWindow(hwnd, x, y, tile_width, tile_height, True)
            except Exception as e:
                print(f"Could not move/resize window '{title}': {e}")
            index += 1

    print(f"Tiled {n} windows in {rows} rows.")

if __name__ == "__main__":
    tile_windows(layout="grid")