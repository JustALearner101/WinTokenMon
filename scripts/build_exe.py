"""
Automated PyInstaller Build Script for WinTokenMon for Windows (Beta)
Builds a standalone, single-file portable executable (WinTokenMon-v0.1.0-beta-Portable.exe).
"""

import os
import subprocess
import sys

import customtkinter

# Set UTF-8 encoding for stdout on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Calculate Repository Root Directory (parent of scripts/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)
sys.path.insert(0, ROOT_DIR)

from core import __version__

DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
ICON_ICO = os.path.join(ASSETS_DIR, "icon.ico")
MAIN_PY = os.path.join(ROOT_DIR, "main.py")

APP_NAME = f"WinTokenMon-v{__version__}-Portable"


def build():
    print("==================================================")
    print(f"[*] Building {APP_NAME} for Windows...")
    print(f"[*] Project Root: {ROOT_DIR}")
    print("==================================================")

    # Ensure icon exists
    if not os.path.exists(ICON_ICO):
        print("⚠️ Icon missing! Please ensure assets/icon.ico exists.")
        sys.exit(1)

    # Ensure all starter sprites are downloaded and ready for bundling
    try:
        from scripts.download_starter_sprites import main as download_starters

        print("📦 Pre-bundling Starter Pokémon sprites...")
        download_starters()
    except Exception as e:
        print(f"⚠️ Warning: Could not pre-bundle starter sprites: {e}")

    # Locate CustomTkinter directory to bundle assets
    ctk_path = os.path.dirname(customtkinter.__file__)
    print(f"📦 CustomTkinter assets path: {ctk_path}")

    # Build pyinstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name",
        APP_NAME,
        "--icon",
        ICON_ICO,
        "--add-data",
        f"{ctk_path};customtkinter/",
        "--add-data",
        f"{ASSETS_DIR};assets/",
        "--hidden-import",
        "customtkinter",
        "--hidden-import",
        "PIL",
        "--hidden-import",
        "PIL._tkinter_finder",
        "--hidden-import",
        "pystray",
        "--hidden-import",
        "pygame",
        "--hidden-import",
        "sqlite3",
        "--hidden-import",
        "wave",
        "--clean",
        MAIN_PY,
    ]

    print("[*] Executing PyInstaller command:")
    print(" ".join(cmd))
    print("-" * 50)

    res = subprocess.run(cmd, cwd=ROOT_DIR)
    if res.returncode == 0:
        output_exe = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
        print("=" * 50)
        print("[+] BUILD SUCCEEDED!")
        print(f"[+] Standalone Executable: {output_exe}")
        if os.path.exists(output_exe):
            size_mb = os.path.getsize(output_exe) / (1024 * 1024)
            print(f"[+] Binary Size: {size_mb:.2f} MB")
        print("=" * 50)
    else:
        print(f"[-] Build failed with exit code {res.returncode}")
        sys.exit(res.returncode)


if __name__ == "__main__":
    build()
