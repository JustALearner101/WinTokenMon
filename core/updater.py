"""
GitHub Releases auto-update checker for WinTokenMon.

Non-blocking by design: all network work runs on caller-provided worker
threads; failures are silent-but-logged with session cooldowns so an offline
machine never hammers the API.
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
import time
import urllib.request

from . import __version__
from .applog import log_error, log_once

REPO_OWNER = "JustALearner101"
REPO_NAME = "WinTokenMon"
RELEASES_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
RELEASES_PAGE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases"

CHECK_INTERVAL_S = 24 * 3600  # check at most once a day
_FAILURE_COOLDOWN_S = 300  # retry 5 minutes after a network failure
_HTTP_TIMEOUT_S = 5

_state_lock = threading.Lock()
_last_check_at: float | None = None
_last_failed_at: float | None = None


def parse_version(version: str) -> tuple[int, ...]:
    """Extracts the numeric core of a version string: 'v1.2.3-rc.1' -> (1, 2, 3)."""
    match = re.search(r"\d+(?:\.\d+)*", version or "")
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(0).split("."))


def is_newer_version(remote: str, local: str) -> bool:
    """True when the remote release tag is strictly newer than the local one."""
    try:
        return parse_version(remote) > parse_version(local)
    except ValueError:
        return False


def pick_setup_asset(assets: list[dict]) -> dict | None:
    """Selects the Inno Setup installer asset (prefers it over the portable exe)."""
    setup = [a for a in assets if "setup" in (a.get("name") or "").lower()]
    exes = [a for a in assets if (a.get("name") or "").lower().endswith(".exe")]
    candidates = sorted(setup or exes, key=lambda a: a.get("name") or "")
    return candidates[0] if candidates else None


def fetch_latest_release(timeout: float = _HTTP_TIMEOUT_S) -> dict | None:
    """Fetches the latest release payload from GitHub. Returns None on failure."""
    global _last_failed_at
    try:
        req = urllib.request.Request(
            RELEASES_API_URL, headers={"User-Agent": f"WinTokenMon/{__version__}"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        with _state_lock:
            _last_failed_at = None
        return data
    except Exception as exc:
        log_once("updater.fetch", f"release check failed: {exc}")
        with _state_lock:
            _last_failed_at = time.monotonic()
        return None


def check_for_update(force: bool = False) -> dict | None:
    """Checks for a newer release, honoring the daily / failure cooldowns.

    Returns an update info dict when a newer version exists:
        {"version", "notes", "download_url", "checksum_url", "release_url"}
    Returns None when up-to-date, in cooldown, or on failure.
    """
    global _last_check_at
    with _state_lock:
        now = time.monotonic()
        if not force and _last_check_at is not None:
            if now - _last_check_at < CHECK_INTERVAL_S:
                return None
        failed = _last_failed_at
        if failed is not None and now - failed < _FAILURE_COOLDOWN_S:
            return None
        _last_check_at = now

    release = fetch_latest_release()
    if not release:
        return None

    tag = release.get("tag_name") or ""
    if not is_newer_version(tag, __version__):
        return None

    assets = release.get("assets") or []
    installer = pick_setup_asset(assets)
    checksum_asset = next(
        (
            a
            for a in assets
            if installer and (a.get("name") or "") == f"{installer.get('name')}.sha256"
        ),
        None,
    )

    info = {
        "version": tag.lstrip("v"),
        "notes": (release.get("body") or "").strip(),
        "download_url": (installer or {}).get("browser_download_url") or "",
        "checksum_url": (checksum_asset or {}).get("browser_download_url") or "",
        "release_url": release.get("html_url") or RELEASES_PAGE_URL,
    }
    if not info["download_url"]:
        log_error(f"updater.no_installer_asset for {tag}")
        return None
    return info


def verify_sha256(path: str, expected_hex: str) -> bool:
    """Streams the file through SHA256 and compares against expected (any case)."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().lower() == (expected_hex or "").strip().lower()


def download_file(url: str, dest_path: str) -> str | None:
    """Downloads url to dest_path on the calling thread. Returns path or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"WinTokenMon/{__version__}"})
        tmp_path = dest_path + ".part"
        with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, "wb") as out:
            while True:
                chunk = resp.read(1 << 15)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp_path, dest_path)
        return dest_path
    except Exception as exc:
        log_error(f"updater.download_failed ({url}): {exc}")
        try:
            os.remove(dest_path + ".part")
        except OSError:
            pass
        return None


def download_and_verify_update(info: dict) -> str | None:
    """Downloads the new Setup installer to %TEMP% and verifies its SHA256.

    Returns the verified installer path, or None on any failure.
    """
    url = info["download_url"]
    filename = os.path.basename(url.split("?")[0]) or "WinTokenMon-Setup.exe"
    dest_path = os.path.join(tempfile.gettempdir(), filename)

    if download_file(url, dest_path) is None:
        return None

    expected = ""
    if info.get("checksum_url"):
        checksum_text_path = dest_path + ".sha256"
        downloaded = download_file(info["checksum_url"], checksum_text_path)
        if downloaded:
            try:
                with open(checksum_text_path, encoding="utf-8") as f:
                    expected = f.read().split()[0]
            except (OSError, IndexError):
                expected = ""

    # No published checksum -> trust over HTTPS only; with one -> enforce it.
    if expected and not verify_sha256(dest_path, expected):
        log_error(f"updater.checksum_mismatch for {filename}; discarding")
        try:
            os.remove(dest_path)
        except OSError:
            pass
        return None
    return dest_path


def launch_installer(installer_path: str) -> bool:
    """Launches the Inno Setup installer with the silent switch."""
    try:
        subprocess.Popen([installer_path, "/SILENT"], close_fds=True)
        return True
    except Exception as exc:
        log_error(f"updater.launch_failed: {exc}")
        return False


def start_background_check(on_update_available) -> threading.Thread:
    """Runs one cooldown-aware update check on a daemon thread.

    `on_update_available(info)` is invoked on completion when an update exists;
    wrap it so it marshals back to your UI thread.
    """
    def _run():
        info = check_for_update()
        if info:
            try:
                on_update_available(info)
            except Exception as exc:
                log_error(f"updater.callback_failed: {exc}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
