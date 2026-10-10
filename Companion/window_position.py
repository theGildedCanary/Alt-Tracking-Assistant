"""Save window placement with native Windows support and a Tk fallback."""

import re
import sys

if sys.platform == "win32":
    from window_position_windows import capture, restore
else:
    def capture(root):
        if root.state() == "iconic":
            return None
        return {"geometry": root.geometry()}

    def restore(root, saved):
        if not isinstance(saved, dict):
            return False
        geometry = saved.get("geometry")
        if not isinstance(geometry, str):
            return False
        match = re.fullmatch(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", geometry)
        if not match:
            return False
        width, height, x, y = map(int, match.groups())
        if width <= 0 or height <= 0:
            return False
        width = min(width, root.winfo_screenwidth())
        height = min(height, root.winfo_screenheight())
        x = max(0, min(x, root.winfo_screenwidth() - width))
        y = max(0, min(y, root.winfo_screenheight() - height))
        root.geometry(f"{width}x{height}+{x}+{y}")
        return True
