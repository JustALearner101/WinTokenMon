"""
Unit tests for Windows Startup & Registry Autostart Manager
"""

import sys
from unittest.mock import MagicMock, patch

from core.autostart import (
    get_autostart_command,
    is_autostart_enabled,
    is_autostart_supported,
    set_autostart,
)
from core.companion_store import CompanionStore


def test_autostart_supported_on_windows():
    if sys.platform == "win32":
        assert is_autostart_supported() is True
    else:
        assert is_autostart_supported() is False


def test_get_autostart_command():
    cmd = get_autostart_command()
    assert isinstance(cmd, str)
    assert len(cmd) > 0
    # Should wrap executables in quotes
    assert cmd.startswith('"')


def test_set_autostart_mocked(monkeypatch):
    mock_winreg = MagicMock()
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
    mock_winreg.HKEY_CURRENT_USER = "HKCU"
    mock_winreg.KEY_SET_VALUE = 1
    mock_winreg.KEY_READ = 2
    mock_winreg.REG_SZ = 1

    monkeypatch.setattr("core.autostart.is_autostart_supported", lambda: True)
    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        # Enable
        assert set_autostart(True) is True
        mock_winreg.SetValueEx.assert_called_once()

        # Disable
        assert set_autostart(False) is True
        mock_winreg.DeleteValue.assert_called_once()


def test_is_autostart_enabled_mocked(monkeypatch):
    mock_winreg = MagicMock()
    mock_key = MagicMock()
    mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
    mock_winreg.QueryValueEx.return_value = ('"C:\\Python\\pythonw.exe" "main.py"', 1)

    monkeypatch.setattr("core.autostart.is_autostart_supported", lambda: True)
    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        assert is_autostart_enabled() is True


def test_companion_store_autostart_integration(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr("core.companion_store.STATE_FILE", str(state_file))
    monkeypatch.setattr("core.companion_store.reg_set_autostart", lambda enabled: True)

    store = CompanionStore()
    assert store.autostart_enabled is False

    assert store.set_autostart(True) is True
    assert store.autostart_enabled is True

    # Reload store from disk
    store2 = CompanionStore()
    assert store2.autostart_enabled is True
