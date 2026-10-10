"""Platform-specific paths and input behavior for the desktop companion."""

import os
import sys
from pathlib import Path


def data_dir(platform=None, home=None, environ=None):
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else Path(home)
    environ = os.environ if environ is None else environ
    if platform == "darwin":
        base = home / "Library" / "Application Support"
    elif platform == "win32":
        base = Path(environ.get("APPDATA") or home)
    else:
        base = Path(environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    return base / "AltTrackingAssistantCompanion"


def wow_dirs(platform=None, home=None):
    platform = sys.platform if platform is None else platform
    home = Path.home() if home is None else Path(home)
    if platform == "darwin":
        return ["/Applications/World of Warcraft", str(home / "Applications" / "World of Warcraft")]
    if platform == "win32":
        return [r"C:\Program Files (x86)\World of Warcraft", r"C:\Program Files\World of Warcraft", r"D:\World of Warcraft"]
    return []


def wheel_units(delta, multiplier=3, platform=None):
    """Mac trackpads send small deltas; Windows wheels use multiples of 120."""
    if not delta:
        return 0
    platform = sys.platform if platform is None else platform
    if platform == "darwin":
        return -int(delta)
    steps = max(1, int(abs(delta) / 120))
    return -multiplier * steps if delta > 0 else multiplier * steps
