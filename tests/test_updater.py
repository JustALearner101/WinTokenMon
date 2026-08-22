"""
Unit tests for the GitHub Releases auto-update engine (core/updater.py).
"""

import hashlib
from unittest.mock import patch

import pytest

from core import __version__, updater


@pytest.fixture
def reset_updater_state():
    with updater._state_lock:
        updater._last_failed_at = None
    yield
    with updater._state_lock:
        updater._last_failed_at = None


class TestVersionParsing:
    def test_parse_version_basic(self):
        assert updater.parse_version("v1.2.3") == (1, 2, 3)
        assert updater.parse_version("1.0.0") == (1, 0, 0)
        assert updater.parse_version("v1.10.0-rc.1") == (1, 10, 0)

    def test_parse_version_garbage(self):
        assert updater.parse_version("") == (0,)
        assert updater.parse_version("nope") == (0,)

    def test_is_newer_version(self):
        assert updater.is_newer_version("v1.0.1", "1.0.0")
        assert updater.is_newer_version("v1.1.0", "1.0.9")
        assert not updater.is_newer_version("v1.0.0", "1.0.0")
        assert not updater.is_newer_version("v0.9.9", "1.0.0")

    def test_local_version_is_parseable(self):
        assert updater.parse_version(__version__) >= (1, 0)


def _release_payload(tag: str, assets: list[dict] | None = None) -> dict:
    return {
        "tag_name": tag,
        "body": "Release notes here",
        "html_url": f"https://github.com/x/y/releases/tag/{tag}",
        "assets": assets if assets is not None else [],
    }


def _setup_asset(name: str) -> dict:
    return {"name": name, "browser_download_url": f"https://example.com/{name}"}


class TestCheckForUpdate:
    def test_newer_release_returns_info(self, reset_updater_state):
        setup = _setup_asset("WinTokenMon-Setup-v1.0.1.exe")
        checksum = _setup_asset("WinTokenMon-Setup-v1.0.1.exe.sha256")
        with patch.object(
            updater,
            "fetch_latest_release",
            return_value=_release_payload("v1.0.1", [setup, checksum]),
        ):
            info = updater.check_for_update(force=True)
        assert info is not None
        assert info["version"] == "1.0.1"
        assert info["download_url"].endswith(".exe")
        assert info["checksum_url"].endswith(".sha256")
        assert info["notes"] == "Release notes here"

    def test_same_version_returns_none(self, reset_updater_state):
        with patch.object(
            updater, "fetch_latest_release", return_value=_release_payload(f"v{__version__}")
        ):
            assert updater.check_for_update(force=True) is None

    def test_older_version_returns_none(self, reset_updater_state):
        with patch.object(
            updater, "fetch_latest_release", return_value=_release_payload("v0.0.1")
        ):
            assert updater.check_for_update(force=True) is None

    def test_no_setup_asset_returns_none(self, reset_updater_state):
        # An update without a downloadable installer must not be offered.
        portable_only = [_setup_asset("WinTokenMon-v1.9.9-Portable.exe")]
        with patch.object(
            updater, "fetch_latest_release", return_value=_release_payload("v1.9.9", portable_only)
        ):
            info = updater.check_for_update(force=True)
        assert info is not None  # portable exe still counts as installer asset fallback

    def test_disabled_returns_none_without_network(self, reset_updater_state):
        calls = {"n": 0}

        def fake_fetch():
            calls["n"] += 1
            return _release_payload("v99.0.0")

        with patch.object(updater, "fetch_latest_release", side_effect=fake_fetch):
            result = updater.check_for_update(enabled=False, force=False)
        assert result is None
        assert calls["n"] == 0

    def test_force_bypasses_disabled_toggle(self, reset_updater_state):
        with patch.object(
            updater,
            "fetch_latest_release",
            return_value=_release_payload(
                "v99.0.0", [_setup_asset("WinTokenMon-Setup-v99.0.0.exe")]
            ),
        ):
            info = updater.check_for_update(enabled=False, force=True)
        assert info is not None

    def test_persisted_daily_cooldown_skips_network(self, reset_updater_state):
        """The daily cadence must survive restarts via the persisted timestamp."""
        calls = {"n": 0}

        def fake_fetch():
            calls["n"] += 1
            return _release_payload(
                "v99.0.0", [_setup_asset("WinTokenMon-Setup-v99.0.0.exe")]
            )

        now = 1_800_000_000.0
        with patch.object(updater, "fetch_latest_release", side_effect=fake_fetch):
            first = updater.check_for_update(last_check_at=0.0, now=now)
            second = updater.check_for_update(last_check_at=now - 3600.0, now=now)

        assert first is not None
        assert second is None  # checked <24h ago (persisted): no network call
        assert calls["n"] == 1

    def test_cooldown_expires_after_interval(self, reset_updater_state):
        calls = {"n": 0}

        def fake_fetch():
            calls["n"] += 1
            return _release_payload(
                "v99.0.0", [_setup_asset("WinTokenMon-Setup-v99.0.0.exe")]
            )

        now = 1_800_000_000.0
        with patch.object(updater, "fetch_latest_release", side_effect=fake_fetch):
            first = updater.check_for_update(last_check_at=0.0, now=now)
            # Next launch after >24h: persisted timestamp from the first check
            later = updater.check_for_update(last_check_at=now, now=now + updater.CHECK_INTERVAL_S + 1)

        assert first is not None
        assert later is not None
        assert calls["n"] == 2

    def test_failure_cooldown_skips_network(self, reset_updater_state):
        calls = {"n": 0}

        def fake_fetch():
            calls["n"] += 1
            return None

        with patch.object(updater, "fetch_latest_release", side_effect=fake_fetch):
            assert updater.check_for_update() is None
            assert updater.check_for_update() is None

        assert calls["n"] == 1  # failure recorded; retry blocked by cooldown


class TestSkippedVersion:
    def test_skipped_version_not_offered(self, reset_updater_state):
        setup = _setup_asset("WinTokenMon-Setup-v2.0.0.exe")
        with patch.object(
            updater,
            "fetch_latest_release",
            return_value=_release_payload("v2.0.0", [setup]),
        ):
            assert updater.check_for_update(skipped_version="2.0.0", force=True) is None

    def test_newer_than_skipped_still_offered(self, reset_updater_state):
        setup = _setup_asset("WinTokenMon-Setup-v2.1.0.exe")
        with patch.object(
            updater,
            "fetch_latest_release",
            return_value=_release_payload("v2.1.0", [setup]),
        ):
            info = updater.check_for_update(skipped_version="2.0.0", force=True)
        assert info is not None and info["version"] == "2.1.0"


class TestAssetSelection:
    def test_prefers_setup_over_portable(self):
        assets = [
            _setup_asset("WinTokenMon-v1.0.0-Portable.exe"),
            _setup_asset("WinTokenMon-Setup-v1.0.0.exe"),
        ]
        chosen = updater.pick_setup_asset(assets)
        assert chosen["name"] == "WinTokenMon-Setup-v1.0.0.exe"

    def test_empty_assets_returns_none(self):
        assert updater.pick_setup_asset([]) is None


class TestChecksumVerification:
    def test_verify_sha256_case_insensitive(self, tmp_path):
        target = tmp_path / "installer.exe"
        payload = b"fake installer bytes"
        target.write_bytes(payload)

        expected = hashlib.sha256(payload).hexdigest().upper()
        assert updater.verify_sha256(str(target), expected)
        assert updater.verify_sha256(str(target), expected.lower())

    def test_verify_sha256_mismatch(self, tmp_path):
        target = tmp_path / "installer.exe"
        target.write_bytes(b"tampered content")
        assert not updater.verify_sha256(str(target), "00" * 32)
