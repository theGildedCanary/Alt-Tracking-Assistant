"""Save and restore the main window's placement on Windows."""

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)


class WindowPlacement(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.UINT),
        ("flags", wintypes.UINT),
        ("showCmd", wintypes.UINT),
        ("ptMinPosition", wintypes.POINT),
        ("ptMaxPosition", wintypes.POINT),
        ("rcNormalPosition", wintypes.RECT),
    ]


class MonitorInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND

user32.GetWindowPlacement.argtypes = [
    wintypes.HWND, ctypes.POINTER(WindowPlacement)
]
user32.GetWindowPlacement.restype = wintypes.BOOL

user32.SetWindowPlacement.argtypes = [
    wintypes.HWND, ctypes.POINTER(WindowPlacement)
]
user32.SetWindowPlacement.restype = wintypes.BOOL

user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.MonitorFromWindow.restype = wintypes.HANDLE

user32.MonitorFromRect.argtypes = [
    ctypes.POINTER(wintypes.RECT), wintypes.DWORD
]
user32.MonitorFromRect.restype = wintypes.HANDLE

user32.GetMonitorInfoW.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(MonitorInfo)
]
user32.GetMonitorInfoW.restype = wintypes.BOOL


def rect_values(rect):
    return [rect.left, rect.top, rect.right, rect.bottom]


def window_handle(root):
    # Tk's widget handle is inside the native top-level window.
    return user32.GetAncestor(root.winfo_id(), 2)  # GA_ROOT


def monitor_bounds(monitor):
    info = MonitorInfo()
    info.cbSize = ctypes.sizeof(info)
    if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return rect_values(info.rcMonitor)
    return None


def capture(root):
    placement = WindowPlacement()
    placement.length = ctypes.sizeof(placement)
    handle = window_handle(root)

    if not user32.GetWindowPlacement(handle, ctypes.byref(placement)):
        return None

    monitor = user32.MonitorFromWindow(handle, 0)
    bounds = monitor_bounds(monitor)
    if bounds is None:
        return None

    # If closed while minimized, reopen normally or maximized,
    # according to its state before it was minimized.
    maximized = (
        placement.showCmd == 3
        or (placement.showCmd == 2 and placement.flags & 2)
    )

    return {
        "normal_rect": rect_values(placement.rcNormalPosition),
        "maximized": bool(maximized),
        "monitor_bounds": bounds,
    }


def restore(root, saved):
    if not isinstance(saved, dict):
        return False

    rect = saved.get("normal_rect")
    bounds = saved.get("monitor_bounds")

    for values in (rect, bounds):
        if (
            not isinstance(values, list)
            or len(values) != 4
            or any(type(value) is not int for value in values)
            or values[2] <= values[0]
            or values[3] <= values[1]
        ):
            return False

    # Require the saved display area to still exist.
    # A disconnected or rearranged display falls back to default.
    monitor_rect = wintypes.RECT(*bounds)
    monitor = user32.MonitorFromRect(ctypes.byref(monitor_rect), 0)
    if monitor_bounds(monitor) != bounds:
        return False

    placement = WindowPlacement()
    placement.length = ctypes.sizeof(placement)
    placement.showCmd = 3 if saved.get("maximized") is True else 1
    placement.ptMinPosition = wintypes.POINT(-1, -1)
    placement.ptMaxPosition = wintypes.POINT(-1, -1)
    placement.rcNormalPosition = wintypes.RECT(*rect)

    return bool(
        user32.SetWindowPlacement(
            window_handle(root), ctypes.byref(placement)
        )
    )