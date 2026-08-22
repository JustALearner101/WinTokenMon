# 🛠️ Developer Operations & How-To Playbook: WinTokenMon

> **Language / Bahasa**: [**English**](HOWTO.md) | [**Bahasa Indonesia**](id/HOWTO.id.md)

Welcome to the **WinTokenMon Developer Playbook**! This document provides clear, copy-pasteable instructions for common developer tasks: running locally, testing, adding new tabs/modals, adding Pokémon species, compiling binaries, and building Windows setup installers.

---

## 📑 Table of Contents

1. [🚀 Running the Application Locally](#1--running-the-application-locally)
2. [🛠️ Debugging & Environment Configuration via `.env`](#2-️-debugging--environment-configuration-via-env)
3. [🧪 Running Unit Tests & Linters](#3--running-unit-tests--linters)
4. [🧩 Extending the Modular Dashboard Architecture](#4--extending-the-modular-dashboard-architecture)
5. [🌿 Adding New Pokémon Evolution Lines & Species](#5--adding-new-pokémon-evolution-lines--species)
6. [📦 Compiling Standalone Portable Executable (`.exe`)](#6--compiling-standalone-portable-executable-exe)
7. [🧙‍♂️ Compiling Windows Setup Wizard Installer (`Setup.exe`)](#7-️-compiling-windows-setup-wizard-installer-setupexe)
8. [🧹 Testing the Installer & Uninstaller](#8--testing-the-installer--uninstaller)
9. [🔄 Resetting State for Clean Onboarding Testing](#9--resetting-state-for-clean-onboarding-testing)
10. [❓ Troubleshooting & FAQ](#10--troubleshooting--faq)

---

## 1. 🚀 Running the Application Locally

### Using `uv` (Recommended — Ultra Fast)
```powershell
# 1. Sync dependencies automatically
uv sync --all-extras

# 2. Run the application
uv run main.py
```

### Using Standard Python Virtual Environment (`venv` + `pip`)
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 3. Run the application
python main.py
```

---

## 2. 🛠️ Debugging & Environment Configuration via `.env`

WinTokenMon includes developer ergonomics for testing:

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` to configure your testing parameters:
   ```ini
   # Enable verbose terminal logging
   WINTOKENMON_DEBUG=1

   # Accelerate polling interval (e.g., 5 seconds instead of 10s)
   WINTOKENMON_POLL_INTERVAL=5
   ```

3. Run `uv run main.py`.

---

## 3. 🧪 Running Unit Tests & Linters

### Run Unit Tests (`pytest`)
```powershell
# Run full test suite (31 tests)
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_token_reader.py
```

### Run Linter & Formatter (`Ruff`)
```powershell
# Check for lint errors
ruff check .

# Automatically fix lint errors
ruff check --fix .

# Verify formatting without modifying files
ruff format --check .

# Auto-format all files
ruff format .
```

---

## 4. 🧩 Extending the Modular Dashboard Architecture

The dashboard is structured into lightweight, isolated tab views and modal dialogs:

```
ui/
├── dashboard.py                  # Window Coordinator (< 200 lines)
├── dashboard_theme.py            # Themes, palettes, and lore
├── modals/
│   ├── nature_modal.py           # NatureSelectorModal
│   └── pokedex_inspector_modal.py # PokedexInspectorModal
└── tabs/
    ├── home_tab.py               # HomeTabView (HUD & 7-Day Chart)
    ├── pokedex_tab.py            # PokedexTabView (Pokédex & Catch Log)
    ├── shop_tab.py               # ShopTabView (Shop & Bag)
    └── settings_tab.py           # SettingsTabView (Preferences)
```

### Adding a New Tab:
1. Create `ui/tabs/my_feature_tab.py` with a class `MyFeatureTabView`:
   ```python
   import customtkinter as ctk


   class MyFeatureTabView:
       def __init__(self, parent: ctk.CTkFrame, dashboard):
           self.parent = parent
           self.dashboard = dashboard
           self._build_ui()

       def _build_ui(self):
           ctk.CTkLabel(
               self.parent, text="🚀 My Feature", font=ctk.CTkFont(size=16, weight="bold")
           ).pack(pady=10)

       def refresh(self):
           pass
   ```
2. Export it in `ui/tabs/__init__.py`.
3. In `ui/dashboard.py`, add a new tab to `self.tabview` and lazy-load it inside `_on_tab_change()`.

---

## 5. 🌿 Adding New Pokémon Evolution Lines & Species

All Pokémon evolution lines and metadata are pre-indexed in `core/poke_api.py`:

1. Add your evolution chain to `CURATED_EVOLUTION_LINES` in `core/poke_api.py`:
   ```python
   {
       "chain": [447, 448],
       "names": ["Riolu", "Lucario"],
       "stages": 2,
       "rarity": "rare",
   }
   ```
2. The precomputed dictionary `SPECIES_INDEX` will automatically index each species ID for $O(1)$ lookup throughout the entire application.
3. Place animated `.gif` sprites under `assets/sprites/<id>.gif` (e.g. `assets/sprites/447.gif`).

---

## 6. 📦 Compiling Standalone Portable Executable (`.exe`)

To compile the single-file, zero-install portable executable:

```powershell
uv run python scripts/build_exe.py
```

### Output Target:
- 🚀 **`dist/WinTokenMon-v<version>-Portable.exe`** (~28.9 MB)

You can copy this file to any USB drive or folder and run it directly without installing!

---

## 7. 🧙‍♂️ Compiling Windows Setup Wizard Installer (`Setup.exe`)

To build the official Windows Setup Wizard installer (Inno Setup 6):

### Step 1: Ensure Inno Setup 6 is Installed
```powershell
winget install --id JRSoftware.InnoSetup --accept-source-agreements --accept-package-agreements --silent
```

### Step 2: Run the Automated Build Pipeline
```powershell
uv run python scripts/build_installer.py
```

### What this script does automatically:
1. Compiles the latest standalone executable using PyInstaller.
2. Automatically resolves `ISCC.exe` from standard Windows paths (`Program Files` or `%LOCALAPPDATA%`).
3. Injects the live version from `core.__version__` into the Inno Setup script (`/DMyAppVersion`) and **refuses to compile** if the version-matched portable executable is missing — stale binaries can never be packaged.
4. Compiles `installer.iss` and embeds license agreements, desktop icons, and uninstall prompt scripts.

### Output Target:
- 📦 **`dist/WinTokenMon-Setup-v<version>.exe`** (~30 MB)

---

## 8. 🧹 Testing the Installer & Uninstaller

### Testing the Installation:
1. Double-click `dist/WinTokenMon-Setup-v<version>.exe`.
2. Test the **Browse...** button to install to a custom folder (e.g. `D:\TestWinTokenMon`).
3. Check the **Desktop Shortcut** and **Start on Windows Boot** checkboxes.
4. Finish installation and verify that the app launches and floats on your desktop.

### Testing the Uninstaller:
1. Open **Windows Settings** $\to$ **Apps** $\to$ **Installed Apps** (or Control Panel).
2. Search for **WinTokenMon (Beta)** and click **Uninstall**.
3. Notice the interactive prompt:
   - Clicking **`[No]` (Default)** keeps your save game in `%APPDATA%\WinTokenMon` (ideal for updates).
   - Clicking **`[Yes]`** completely wipes all application data and cache.

---

## 9. 🔄 Resetting State for Clean Onboarding Testing

To test the **First-Launch Starter Selection Ceremony (Gen 1 to Gen 9)** from a clean state:

```powershell
# Close any running WinTokenMon instances first
Stop-Process -Name "WinTokenMon*" -ErrorAction SilentlyContinue

# Delete saved state file
Remove-Item "$env:APPDATA\WinTokenMon\state.json" -Force -ErrorAction SilentlyContinue

# Launch application to trigger Starter Wizard
uv run main.py
```

The **Starter Selection Grid Modal** will immediately greet you!

---

## 10. ❓ Troubleshooting & FAQ

### Q1: `customtkinter` or asset missing error after PyInstaller build?
**Fix**: `scripts/build_exe.py` and `scripts/build_installer.py` automatically detect and bundle the `customtkinter/` package assets via `--add-data`. Make sure you run builds via `uv run python scripts/build_installer.py`.

### Q2: Audio cry / SFX does not play?
**Fix**: Verify that your Windows audio output device is active. Pygame mixer initializes non-blockingly; if no sound card is active, it silently degrades without crashing the application.

### Q3: My AI tool token usage is not showing up?
**Fix**: Ensure your tool has generated tokens today. WinTokenMon checks standard paths:
- Antigravity CLI: `~/.gemini/antigravity-cli/conversations/*.db`
- Claude Code: `~/.claude/projects/**/*.jsonl`
- Cursor IDE: `%APPDATA%/Cursor/User/globalStorage/state.vscdb`
- Codex CLI: `~/.codex/sessions/**/rollout-*.jsonl`
- GitHub Copilot: `~/.copilot/session-store.db`
- Koma: `~/.koma/sessions/*.json` and `~/.koma/ledger/*.jsonl`
