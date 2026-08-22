# 🐾 WinTokenMon — PokeTokenBar for Windows

<div align="center">

🌐 **English** • [**Bahasa Indonesia**](README.id.md)

<br/>

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Version](https://img.shields.io/badge/Version-v0.2.0--preview-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-2EA44F?style=for-the-badge&logo=shield&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

**Turn your daily AI coding tokens into a living Pokémon companion on Windows!**  
*A native Windows desktop port inspired by [PokeTokenBar (macOS)](https://github.com/chattymin/PokeTokenBar) (see [Credits](reference/README.md)).*

</div>

---

## ✨ Features at a Glance

### 1. 🤖 Multi-Provider Local Token Reader (Low-Resource Incremental Scanning)
- **Zero Configuration & Zero API Keys**: Automatically detects and aggregates your local token consumption directly from file logs:
  - **Antigravity CLI** (`~/.gemini/antigravity-cli/conversations/*.db`)
  - **Claude Code** (`~/.claude/projects/**/*.jsonl`)
  - **Cursor IDE** (`%APPDATA%/Cursor/User/globalStorage/state.vscdb`)
  - **Codex CLI** (`~/.codex/sessions/**/rollout-*.jsonl`)
  - **GitHub Copilot CLI** (`~/.copilot/session-store.db`)
   - **Koma (aula-id/koma)** (`~/.koma/sessions/*.json` & `~/.koma/ledger/*.jsonl`)
   - **Aider** (`~/.aider.chat.history.md`)
   - **Windsurf / Cascade** (`%APPDATA%/Windsurf/User/workspaceStorage/*/state.vscdb`)
   - **Cline & Roo Code** (`%APPDATA%/Code/User/globalStorage/*` task logs)
- **Incremental Tail Scanning**: Parses only new appended log lines in $O(\Delta)$ time, cutting background CPU usage by >85%.
- **100% Private & Offline**: Reads only token count metadata. Your source code and prompts are never read, stored, or transmitted.

### 2. 🐾 Living Floating Desktop Pet
- **Transparent & Draggable**: Floats framelessly on your desktop without obstructing your work.
- **Interactive Reactions**:
  - **Click Bounce**: Pet springs up with cute reaction emojis (`❤️`, `⚡`, `✨`, `🎵`, `🔥`, `💪`) and plays authentic Pokémon cries!
  - **Sleep / Nap Mode (`💤`)**: Enters gentle slumber with floating sleep bubbles after 20 minutes of no coding. Wakes up upon activity.
  - **Coding Burn Mode (`🔥`)**: Enters excited burst state when heavy AI generation bursts (>500k tokens) occur.
  - **Egg Wobble**: The egg shakes eagerly when reaching $\ge 90\%$ hatching progress.
- **Customizable Scale & Opacity**: Choose from **Small (80px)**, **Medium (110px)**, or **Large (150px)**, adjust opacity slider (50%–100%), or click **📌 Snap Above Taskbar**.

### 3. 🐣 Starter Selection, Evolution & Ceremonies
- **Choose Your Starter (Gen 1 to Gen 9)**: On first launch, choose your favorite starter from any generation (Bulbasaur, Charmander, Squirtle, Cyndaquil, Torchic, Mudkip, Piplup, Froakie, Rowlet, Sprigatito, Fuecoco, Quaxly, Pikachu, Eevee, Riolu) with full confirmation dialog!
- **Tiered Eggs**: Incubate Common, Uncommon, Rare (Dratini, Bagon, Larvitar, Gible, Deino), or Legendary (Mewtwo, Rayquaza, Reshiram) eggs.
- **Classic Ceremony Animations**: White flash transition, spring scale pop, and star sparkle clusters on Shiny hatches and evolutions.
- **Official Pokémon Cries & 8-Bit Fanfare**: Plays authentic Pokémon sound cries from PokéAPI and retro level-up chimes (can be muted in Settings).
- **Shiny Hunting (`✨`)**: 1/129 base chance to hatch a Shiny Pokémon, boostable to 1/40 with the Shiny Charm!

### 4. 📊 Modular Dark-Mode Dashboard
- **Instant Launch & Lazy Loading**: Modular architecture (`ui/tabs/` and `ui/modals/`) with sub-50ms window open time.
- **Adaptive Elemental Theming**: Dashboard accent colors adapt to your active companion's element (Grass 🌿, Fire 🔥, Water 💧, Electric ⚡, Psychic 🔮, Dragon 🐉, Fighting 🥋, Normal ⭐).
- **7-Day Token History Chart**: Canvas-drawn bar chart visualizing your daily token burn over the past week.
- **Reference-Style Pokédex & Catch Log**:
  - **📖 Pokédex Grid**: Lightweight, dynamic rendering of all registered owned species.
  - **📜 Catch Log**: Chronological audit trail of lifetime hatches and graduations with timestamps and nature metadata.
- **Shop & Bag**: Spend tokens earned from coding on **Rare Candies 🍬 (+100M EXP)**, **Nature Mints 🌿 (20 personalities)**, and **Rare Eggs 🥚**.

### 5. 🎯 Windows Native Notifications & Daily Budget
- **Budget Alerts**: Set a daily token limit (e.g. 20M / 50M).
- **Native Toast Notifications**: Non-intrusive Windows balloons alert you at **80% (Warning)** and **100% (Limit Reached)**.
- **Start with Windows**: Optional registry-based autostart (HKCU Run key) toggled from Settings.

### 6. 🏆 Developer Achievements & Trophies
- **8 Unlockable Badges** across Bronze → Platinum tiers: *First Hatch, Night Owl Coder, Token Overclock, Multi-Tool Wizard, 100M Burn Club, Shiny Hunter, Senior Professor, Egg Hoarder* — with token/item rewards and a Trophy Cabinet tab.

### 7. 🍬 Interactive Feeding & Friendship
- **Treat Physics**: Drop Rare Candies or Oran Berries onto the desktop and watch your pet chase, munch, and sparkle.
- **Friendship Meter**: Daily petting and treats raise affection; high friendship (≥80%) grants a +10% companion EXP boost.

### 8. 📟 Compact HUD Capsule Mode
- **Minimal 220×32px Always-On-Top Pill**: Live token burn vs daily limit (%), burn velocity (tokens/min), and hatch/evolution progress — switchable instantly from the tray menu.

---

## 🚀 Quick Start

### Prerequisites
- Windows 10 or Windows 11 (64-bit)
- Python 3.10, 3.11, 3.12, or 3.14+

### Installation & Launch

1. **Clone the repository**:
   ```powershell
   git clone https://github.com/YourUsername/WinTokenMon.git
   cd WinTokenMon
   ```

2. **Run (Option A: Instant with `uv` — Recommended)**:
   ```powershell
   # Sync virtualenv and dependencies automatically
   uv sync
   uv run main.py
   ```

3. **Run (Option B: Traditional with `pip`)**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python main.py
   ```

4. **Background Execution**:
   - Double-click `run.bat` or `run_silent.vbs` (starts silently in the background).

### 🛠️ Developer Mode & Environment Flags

WinTokenMon supports optional developer override flags via `.env`. Simply copy the template:
```powershell
Copy-Item .env.example .env
```
Available flags:
- `WINTOKENMON_DEBUG=1`: Enables verbose debug logging to console.
- `WINTOKENMON_POLL_INTERVAL=5`: Sets polling interval (in seconds).

---

## 🎮 Desktop Controls & Shortcuts

| Action | Control |
| :--- | :--- |
| **Move Pet** | Click & drag sprite anywhere on screen |
| **Pet Reaction (Bounce + Emoji + Cry)** | Single left click on sprite |
| **View Quick Token Tooltip** | Hover mouse cursor over sprite |
| **Open Dashboard / Pokédex** | Double-click sprite OR right-click sprite |
| **System Tray Menu** | Right-click Pokéball icon in Windows Taskbar |
| **Snap Above Taskbar** | Click *📌 Snap Above Taskbar* in Dashboard Settings |

---

## 🤖 Supported Local AI Coding Tools

| AI Assistant | Detection Path on Windows | Mode |
| :--- | :--- | :--- |
| **Antigravity CLI** | `~/.gemini/antigravity-cli/conversations/*.db` | Read-only Protobuf |
| **Claude Code** | `~/.claude/projects/**/*.jsonl` | Incremental JSONL Tail |
| **Cursor IDE** | `%APPDATA%/Cursor/User/globalStorage/state.vscdb` | Read-only SQLite (`mode=ro`) |
| **Codex CLI** | `~/.codex/sessions/**/rollout-*.jsonl` | Incremental JSONL Tail |
| **GitHub Copilot CLI** | `~/.copilot/session-store.db` | Read-only SQLite (`mode=ro`) |
| **Koma** | `~/.koma/sessions/*.json` & `~/.koma/ledger/*.jsonl` | Incremental JSONL / JSON |

---

## 📚 Technical Documentation

- 🛠️ [**Developer Playbook & HOWTO**](docs/HOWTO.md): Step-by-step guides for running locally, debugging with `.env`, compiling `.exe`, and building the Setup Wizard installer.
- 🏗️ [**Architecture & System Design**](docs/ARCHITECTURE.md): Deep-dive into token reader pipelines, animation engine, and modular dashboard architecture.
- 🎮 [**Balance & Game Progression Guide**](docs/BALANCE.md): Mathematical progression curves, egg tiers, and shop economics.
- 🗺️ [**Roadmap & Future Works**](docs/FUTURE-WORKS.md): Upcoming achievements, desktop minigames, compact HUD, and AI scanners.
- ⚠️ [**Known Limitations & FAQ**](docs/KNOWN-LIMITATIONS.md): Windows platform quirks, colorkey transparency, and workarounds.
- 🛡️ [**Security & Privacy Policy**](SECURITY.md): Privacy guarantees and local file inspection rules.
<!-- - 🤝 [**Contributing Guide**](CONTRIBUTING.md): How to add support for new AI coding tools. -->

---

## ⚖️ Disclaimer & Fair Use

**WinTokenMon** is an independent, open-source, non-commercial fan project created for developer productivity and educational purposes under Fair Use.

- Pokémon and Pokémon character names are registered trademarks of **Nintendo**, **Creatures Inc.**, and **GAME FREAK inc.**
- **NFR-01 Asset Compliance**: This repository does not distribute any copyrighted game ROMs, proprietary artwork, or proprietary audio. All sprites and cries are requested at runtime from public community endpoints (PokéAPI / Showdown) and cached locally by the user.
- See [`DISCLAIMER.md`](DISCLAIMER.md) for full legal notices.

---

<div align="center">
Made with ❤️ for developers who code with AI.
</div>
