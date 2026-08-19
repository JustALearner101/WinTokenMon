# 📜 Changelog — WinTokenMon

All notable changes to **WinTokenMon** will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0-preview] - 2026-08-19

### 🚀 Highlights & Major Features

#### 🏆 Developer Achievements & Badges System (v0.2.0)
- **Real-Time Milestone Engine** (`core/achievement_engine.py`): Tracks token burn milestones, coding habits, streaks, and egg hatching achievements.
- **Trophies Tab in Dashboard** (`ui/tabs/trophies_tab.py`): Visual badge collection showcasing unlocked and locked trophies with unlock timestamps and descriptions.
- **Unlock Ceremony Banners**: Particle sparkle effects and celebratory floating banners when earning new achievements.

#### 🍬 Interactive Feeding & Friendship System (v0.3.0)
- **Physics Treat Dropping Overlay** (`ui/treat_overlay.py`): Draggable treats (Oran Berries, Rare Candies) with cursor grabbing, physical dropping, eating animations, and crunch SFX.
- **Friendship & Affection Mechanics**: Daily petting/feeding caps, affection meter, and a permanent **+10% EXP Boost** when friendship reaches >= 80%.
- **Nature Mint Rerolling**: Allows customizing Pokémon nature and stat affinities directly from the companion action grid.

#### 🎨 Redesigned Desktop Pet & Hover Tooltip Card
- **Dashboard Theme Alignment**: Fully synchronized with the Catppuccin Mocha palette (`#181825` Mantle, `#313244` Surface0, `#CDD6F4` Text).
- **Dynamic Elemental Palette** (`TYPE_THEMES`): Progress bar fill color and card border accents dynamically match the Pokémon's elemental type (Grass, Fire, Water, Electric, etc.).
- **Smooth Canvas Progress Bar**: Replaced OS-native `ttk.Progressbar` with custom smooth-pill Canvas rendering, complete with dual metrics:
  - Progress percentage & title (`Evolution Progress: 25.0%` / `Incubation Progress: 50.0%`).
  - Precise token tracking (`2.5K / 10.0K Tokens`).
- **Stats Footer**: Heart-badged Friendship gauge with bonus indicators and today's token burn tracker.

#### 🔊 Audio & Visual Effects Upgrades
- **Procedural Sound Engine** (`core/audio_manager.py`): Real-time synthesized retro 8-bit sound effects (crunch, level up, heart, Pokéball bounce & release) with global volume controls.
- **Animation Particles**: Star sparkles, floating heart bubbles, and bouncy entrance animations.

#### 🧬 Battle System Architecture RFC (v1.1+)
- Comprehensive RFC document (`docs/plans/far-future-battle-ev-iv-and-movesets-rfc.md`) detailing the upcoming turn-based idle battle system, IV/EV training, moveset database, 100-floor PvE tower, and state schemas.

---

## [0.1.0-beta] - 2026-08-18

### 🐣 Initial Beta Release
- **5-in-1 Local Token Reader**: Zero-config incremental log parsers for Antigravity CLI, Claude Code, Cursor IDE, Codex CLI, and GitHub Copilot CLI.
- **Floating Shimeji Desktop Pet**: Animated 2D Pokémon sprites with autonomous roaming, dragging, idle sleep, and token burn reactions.
- **Starter Selection (Gen 1-9)**: Choose from 27 canonical starters across 9 Pokémon generations.
- **Interactive Dashboard**: Modern CustomTkinter dark-mode GUI with Home, Pokédex, and Shop tabs.
- **Egg Hatching & Evolutionary Lineage**: Multi-tiered eggs, progressive evolution stages, and graduation ceremonies.
- **Native Windows Packaging**: Standalone portable single-file executable and Inno Setup 6 installer wizard.
