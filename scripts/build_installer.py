"""
Automated Build Pipeline for WinTokenMon for Windows
1. Builds the Standalone Portable Executable via PyInstaller
2. Compiles the Setup Installer Wizard via Inno Setup 6 (ISCC.exe)
"""

import os
import shutil
import subprocess
import sys

# Set UTF-8 encoding for stdout on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)
sys.path.insert(0, ROOT_DIR)

from core import __version__
from scripts.build_exe import build as build_portable_exe

INSTALLER_ISS = os.path.join(ROOT_DIR, "installer.iss")
DIST_DIR = os.path.join(ROOT_DIR, "dist")
OUTPUT_SETUP_EXE = os.path.join(DIST_DIR, f"WinTokenMon-Setup-v{__version__}.exe")


def find_iscc() -> str | None:
    """Locates the Inno Setup Compiler executable (ISCC.exe)."""
    # 1. Check if ISCC is on system PATH
    on_path = shutil.which("ISCC.exe") or shutil.which("iscc")
    if on_path:
        return on_path

    # 2. Check common standard installation locations on Windows
    candidate_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
        os.path.expandvars(r"%ProgramFiles%\Inno Setup 6\ISCC.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"),
    ]

    for p in candidate_paths:
        if os.path.exists(p):
            return p

    return None


def main():
    print("==================================================")
    print(f"[*] WinTokenMon v{__version__} — Automated Installer Build Pipeline")
    print("==================================================")

    # Step 1: Build Portable Executable
    print("\n--- STEP 1: Building Standalone Executable (PyInstaller) ---")
    build_portable_exe()

    # Step 2: Compile Inno Setup Script
    print("\n--- STEP 2: Compiling Windows Setup Installer (Inno Setup 6) ---")
    if not os.path.exists(INSTALLER_ISS):
        print(f"❌ Error: {INSTALLER_ISS} not found!")
        sys.exit(1)

    # Guard against packaging a stale executable from an older build
    expected_exe = os.path.join(DIST_DIR, f"WinTokenMon-v{__version__}-Portable.exe")
    if not os.path.exists(expected_exe):
        print(f"❌ Error: {expected_exe} not found — refusing to package a stale binary.")
        sys.exit(1)

    iscc_bin = find_iscc()
    if not iscc_bin:
        print(" Inno Setup Compiler (ISCC.exe) was not detected on this machine.")
        print("\n To build the Windows Setup Wizard locally, install Inno Setup 6:")
        print("   winget install JRSoftware.InnoSetup")
        print("   - or -")
        print("   choco install innosetup")
        print("\n Note: Portable executable was built successfully in dist/.")
        print(
            "   GitHub Actions CI will automatically compile the Setup Wizard upon release tagging."
        )
        return

    print(f"[*] Found Inno Setup Compiler: {iscc_bin}")
    print(f"[*] Compiling script: {INSTALLER_ISS}")

    # Inject the live version from core.__version__ so the Setup wizard can
    # never package a stale, hardcoded version of the portable executable.
    cmd = [iscc_bin, f"/DMyAppVersion={__version__}", INSTALLER_ISS]
    res = subprocess.run(cmd, cwd=ROOT_DIR)

    if res.returncode == 0:
        print("=" * 50)
        print("[+] SETUP INSTALLER BUILD SUCCEEDED!")
        if os.path.exists(OUTPUT_SETUP_EXE):
            size_mb = os.path.getsize(OUTPUT_SETUP_EXE) / (1024 * 1024)
            print(f"[+] Setup Installer Output: {OUTPUT_SETUP_EXE}")
            print(f"[+] Setup Installer Size  : {size_mb:.2f} MB")
        print("=" * 50)
    else:
        print(f" Inno Setup compilation failed with exit code {res.returncode}")
        sys.exit(res.returncode)


if __name__ == "__main__":
    main()
