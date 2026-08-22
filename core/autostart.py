r"""
Windows Startup & Registry Autostart Manager for WinTokenMon
Manages registry keys in HKCU\Software\Microsoft\Windows\CurrentVersion\Run
allowing WinTokenMon to start silently on user logon.
"""

import os
import sys

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "WinTokenMon"


def is_autostart_supported() -> bool:
    """Returns True if running on Windows platform with registry access."""
    return sys.platform == "win32"


def get_autostart_command() -> str:
    """
    Constructs the appropriate executable launch command string:
    - If packaged (PyInstaller frozen exe): path to executable
    - If running from source: pythonw.exe + main.py (silent without console window)
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'

    # Source code execution
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_py = os.path.join(root_dir, "main.py")

    # Prefer pythonw.exe over python.exe to prevent console pop-up
    py_dir = os.path.dirname(sys.executable)
    pyw_candidate = os.path.join(py_dir, "pythonw.exe")
    exe_to_use = pyw_candidate if os.path.exists(pyw_candidate) else sys.executable

    return f'"{exe_to_use}" "{main_py}"'


def is_autostart_enabled() -> bool:
    """Checks whether WinTokenMon is currently registered in HKCU Run key."""
    if not is_autostart_supported():
        return False

    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, APP_REG_NAME)
            return bool(val)
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_autostart(enable: bool) -> bool:
    """
    Registers or unregisters WinTokenMon from Windows Startup registry.
    Returns True on success, False on error.
    """
    if not is_autostart_supported():
        return False

    try:
        import winreg

        if enable:
            cmd = get_autostart_command()
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
            return True
        else:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE
                ) as key:
                    winreg.DeleteValue(key, APP_REG_NAME)
            except FileNotFoundError:
                pass
            return True
    except Exception as exc:
        from .applog import log_error

        log_error(f"autostart.set({enable}) failed: {exc}")
        return False
