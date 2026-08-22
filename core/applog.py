"""
Lightweight application file logger for WinTokenMon.

Writes to %APPDATA%/WinTokenMon/logs/wintokenmon.log with simple size-based
rotation. Safe to call from any thread; never raises.
"""

import os
import threading
import time

LOG_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")), "WinTokenMon", "logs"
)
LOG_FILE = os.path.join(LOG_DIR, "wintokenmon.log")
_MAX_LOG_BYTES = 1_000_000

_lock = threading.Lock()
_logged_once: set[str] = set()

os.makedirs(LOG_DIR, exist_ok=True)


def log_error(message: str):
    """Appends a timestamped line to the log file, rotating when oversized."""
    try:
        with _lock:
            if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > _MAX_LOG_BYTES:
                backup = LOG_FILE + ".1"
                if os.path.exists(backup):
                    os.remove(backup)
                os.replace(LOG_FILE, backup)
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception:
        pass


def log_once(key: str, message: str):
    """Like log_error but only the first occurrence of `key` is recorded.

    Use for recurring background failures (scanners, downloads) that would
    otherwise spam the log on every polling tick.
    """
    if key in _logged_once:
        return
    with _lock:
        if key in _logged_once:
            return
        _logged_once.add(key)
    log_error(f"[{key}] {message}")
