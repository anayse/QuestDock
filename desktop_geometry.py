"""Desktop docking geometry in the caller's Tk coordinate space.

The native lookup deliberately targets the primary work area. Pure geometry
helpers also accept negative origins, but this is not a mixed-DPI monitor
selection implementation.
"""
import ctypes
from ctypes import wintypes
import os


def _area(area):
    left, top, right, bottom = (int(v) for v in area)
    if right <= left or bottom <= top:
        raise ValueError('work area must have positive width and height')
    return left, top, right, bottom


def clamp_position(x, y, width, height, area):
    """Keep a rectangle inside area; pin oversized rectangles to its origin."""
    left, top, right, bottom = _area(area)
    width, height = max(1, int(width)), max(1, int(height))
    return (
        max(left, min(int(round(x)), max(left, right - width))),
        max(top, min(int(round(y)), max(top, bottom - height))),
    )


def nearest_edge(x, y, size, area, threshold=36):
    """Return the nearest edge within threshold, using the ball's outer bounds.

    Ties favor a vertical edge so releasing near a corner produces a stable
    left/right dock. Coordinates may be slightly outside the work area.
    """
    left, top, right, bottom = _area(area)
    size = max(1, int(size))
    distances = (
        ('left', abs(x - left)),
        ('right', abs(x + size - right)),
        ('top', abs(y - top)),
        ('bottom', abs(y + size - bottom)),
    )
    side, distance = min(distances, key=lambda pair: pair[1])
    return side if distance <= max(0, threshold) else None


def dock_position(side, x, y, size, area, hidden=False, peek=12):
    """Dock a square to an edge, optionally leaving only `peek` pixels visible.

    The orthogonal coordinate stays clamped. Reveal from hiding by calling this
    again with hidden=False; hidden coordinates are never persisted as anchors.
    """
    left, top, right, bottom = _area(area)
    size = max(1, int(size))
    peek = max(1, min(size, int(peek)))
    x, y = clamp_position(x, y, size, size, area)
    offset = size - peek if hidden else 0
    if side == 'left':
        x = left - offset
    elif side == 'right':
        x = right - size + offset
    elif side == 'top':
        y = top - offset
    elif side == 'bottom':
        y = bottom - size + offset
    else:
        raise ValueError('side must be left, right, top, or bottom')
    return x, y


def _windows_work_area(hwnd):
    """Read primary work bounds in the calling thread's coordinate space.

    Monitor lookup also works before the Tk root is mapped. No DPI-awareness
    changes or conversion using a hidden window handle are needed.
    """
    class MONITORINFO(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT),
                    ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]

    user32 = ctypes.WinDLL('user32', use_last_error=True)
    monitor_from_point = user32.MonitorFromPoint
    monitor_from_point.argtypes = [wintypes.POINT, wintypes.DWORD]
    monitor_from_point.restype = wintypes.HANDLE
    get_info = user32.GetMonitorInfoW
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
    get_info.restype = wintypes.BOOL
    monitor = monitor_from_point(wintypes.POINT(0, 0), 1)
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(info)
    if not monitor or not get_info(monitor, ctypes.byref(info)):
        raise OSError(ctypes.get_last_error(), 'primary monitor lookup failed')
    rect = info.rcWork
    return _area((rect.left, rect.top, rect.right, rect.bottom))


def work_area(root):
    """Return (left, top, right, bottom) for the primary desktop work area.

    This is read-only and does not change process DPI awareness or OS settings.
    Taskbar space is excluded when Windows APIs are available. The fallback is
    the complete Tk primary screen, which may include taskbar space.
    """
    fallback = (0, 0, max(1, root.winfo_screenwidth()), max(1, root.winfo_screenheight()))
    if os.name != 'nt':
        return fallback
    try:
        return _windows_work_area(root.winfo_id())
    except (AttributeError, OSError, ValueError, RuntimeError):
        return fallback
