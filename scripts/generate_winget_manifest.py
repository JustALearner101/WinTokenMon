"""
Generates WinGet manifest YAML files for a WinTokenMon release.

Usage:
    python scripts/generate_winget_manifest.py --version 1.0.0 \
        [--repo JustALearner101/WinTokenMon] \
        [--installer-url URL | derived from tag] \
        [--sha256 HEX | computed from dist/WinTokenMon-Setup-v<version>.exe]

Writes the three-part manifest into winget/ by default.
"""

import argparse
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(HERE)
DEFAULT_OUT_DIR = os.path.join(ROOT_DIR, "winget")
PACKAGE_ID = "JustALearner101.WinTokenMon"
PACKAGE_NAME = "WinTokenMon"
DEFAULT_REPO = "JustALearner101/WinTokenMon"

VERSION_SCHEMA = "https://aka.ms/winget-manifest.version.1.6.0.schema.json"
INSTALLER_SCHEMA = "https://aka.ms/winget-manifest.installer.1.6.0.schema.json"
LOCALE_SCHEMA = "https://aka.ms/winget-manifest.defaultLocale.1.6.0.schema.json"


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_manifests(repo: str, version: str, installer_url: str, installer_sha256: str) -> dict[str, str]:
    homepage = f"https://github.com/{repo}"
    tag = f"v{version}"
    setup_name = f"{PACKAGE_NAME}-Setup-{tag}.exe"

    version_yaml = f"""\
# yaml-language-server: $schema={VERSION_SCHEMA}
PackageIdentifier: {PACKAGE_ID}
PackageVersion: {version}
DefaultLocale: en-US
ManifestType: version
ManifestVersion: 1.6.0
"""

    installer_yaml = f"""\
# yaml-language-server: $schema={INSTALLER_SCHEMA}
PackageIdentifier: {PACKAGE_ID}
PackageVersion: {version}
Platform:
  - Windows.Desktop
MinimumOSVersion: 10.0.17763.0
InstallerType: inno
InstallModes:
  - interactive
  - silent
  - silentWithProgress
Installers:
  - Architecture: x64
    InstallerUrl: {installer_url or f"{homepage}/releases/download/{tag}/{setup_name}"}
    InstallerSha256: {installer_sha256}
    Scope: user
ManifestType: installer
ManifestVersion: 1.6.0
"""

    locale_yaml = f"""\
# yaml-language-server: $schema={LOCALE_SCHEMA}
PackageIdentifier: {PACKAGE_ID}
PackageVersion: {version}
PackageLocale: en-US
Publisher: {PACKAGE_NAME} Contributors
PublisherUrl: {homepage}
PublisherSupportUrl: {homepage}/issues
Author: {PACKAGE_NAME} Contributors
PackageName: {PACKAGE_NAME}
PackageUrl: {homepage}
License: MIT
LicenseUrl: {homepage}/blob/main/LICENSE
Copyright: Copyright (c) 2026 {PACKAGE_NAME} Contributors
ShortDescription: Turn your daily AI coding tokens into a living Pokémon companion on Windows!
Description: |
  {PACKAGE_NAME} is an open-source, gamified developer productivity desktop application
  that tracks local AI coding token usage (Antigravity CLI, Claude Code, Cursor IDE, Codex CLI,
  GitHub Copilot CLI, Aider, Windsurf, Cline, Roo Code) in real-time. Features Shimeji-style
  transparent desktop pet, walking physics, audio cries, 8-bit chiptune synthesizer,
  achievements, compact HUD mode, and Pokédex.
Moniker: wintokenmon
Tags:
  - pokemon
  - ai
  - token-tracker
  - developer-tools
  - desktop-pet
  - shimeji
  - windows
ReleaseNotesUrl: {homepage}/releases/tag/{tag}
ManifestType: defaultLocale
ManifestVersion: 1.6.0
"""

    return {
        f"{PACKAGE_ID}.yaml": version_yaml,
        f"{PACKAGE_ID}.installer.yaml": installer_yaml,
        f"{PACKAGE_ID}.locale.en-US.yaml": locale_yaml,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version, e.g. 1.0.0")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub owner/name")
    parser.add_argument("--installer-url", default="", help="Explicit installer download URL")
    parser.add_argument(
        "--sha256", default="", help="Installer SHA256 hex; computed from dist when omitted"
    )
    parser.add_argument("--out", default=DEFAULT_OUT_DIR, help="Output directory")
    args = parser.parse_args()

    sha256 = args.sha256.upper()
    if not sha256:
        local_setup = os.path.join(
            ROOT_DIR, "dist", f"{PACKAGE_NAME}-Setup-v{args.version}.exe"
        )
        if os.path.exists(local_setup):
            sha256 = sha256_of(local_setup)
        else:
            raise SystemExit(
                f"No --sha256 given and {local_setup} not found. "
                "Build the installer first or pass the checksum explicitly."
            )

    manifests = build_manifests(args.repo, args.version, args.installer_url, sha256)
    os.makedirs(args.out, exist_ok=True)
    for filename, content in manifests.items():
        path = os.path.join(args.out, filename)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"[+] wrote {path}")


if __name__ == "__main__":
    main()
