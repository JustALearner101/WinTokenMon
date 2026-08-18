# 📋 Product Requirement Document (PRD): WinTokenMon

> **Language / Bahasa**: [**English**](PRD.md) | [**Bahasa Indonesia**](id/PRD.id.md)

---

## 1. Executive Summary

**WinTokenMon** is an open-source, gamified developer productivity desktop application that tracks local AI coding token usage (Antigravity CLI, Claude Code, Cursor IDE, Codex CLI, GitHub Copilot CLI) in real-time. By transforming passive token consumption into an interactive, animated Pokémon companion that walks, reacts, hatches from eggs, and evolves, developers gain immediate awareness of their AI coding activity in a fun, non-intrusive manner.

Unlike the macOS version which is confined to the Menu Bar, **WinTokenMon** adopts native Windows paradigms:
- A transparent, borderless **Floating Desktop Pet (Shimeji-style)** that autonomously roams the screen with realistic walking steps.
- A native **Windows System Tray** with live token counters and toast budget alerts.
- An interactive **CustomTkinter Dashboard** with analytics, Pokédex, and item store.

---

## 2. Core Functional Requirements (FR)

### 2.1 Multi-Provider Local Token Scanner
- **FR-01: Auto-Discovery**: Automatically scan and aggregate local token consumption from:
  - **Antigravity CLI**: `~/.gemini/antigravity-cli/conversations/*.db` (Protobuf binary parsing).
  - **Claude Code**: `~/.claude/projects/**/*.jsonl` (Tool use and assistant turns).
  - **Cursor IDE**: `%APPDATA%\Cursor\User\globalStorage\state.vscdb` (SQLite read-only WAL mode).
  - **Codex CLI**: `~/.codex/sessions/**/rollout-*.jsonl`.
  - **GitHub Copilot CLI**: `~/.copilot/session-store.db`.
- **FR-02: Zero-Locking & Performance**: All file access must be non-blocking and read-only (`mode=ro`). A file stat cache $(mtime, size)$ ensures $O(1)$ fast skips for unchanged files.

### 2.2 Companion Progression & Game Economy
- **FR-03: Tiered Egg Incubation**:
  - `Standard Egg`: 2.5M tokens.
  - `Uncommon Egg`: 6M tokens.
  - `Rare Egg`: 15M tokens.
  - `Legendary Egg`: 35M tokens.
- **FR-04: Arithmetic Stage Evolution Formula**:
  $$\text{Stage Threshold} = \text{round}\left( \text{Graduation Total}(\text{Rarity}) \times \frac{i}{k(k+1)/2} \right)$$
- **FR-05: Shop Economy**:
  - Spendable currency is awarded 1:1 for every AI token burned.
  - Items available: *Rare Candy* (+100M EXP), *Nature Mint* (reroll nature), *Shiny Charm* (boosts shiny rate from 1/129 to 1/40).

### 2.3 Interactive Desktop Pet Presentation
- **FR-06: Borderless Transparency**: Rendered on a top-level layered window with Windows colorkey masking (`-transparentcolor`).
- **FR-07: Walking Gait & Step Physics**:
  - Rhythmic vertical step hop: $Y = -|6 \cdot \sin(t)|$.
  - Dynamic frame rate acceleration (50ms while walking vs 100ms when resting).
  - Footstep dust puffs (`💨`) every 7 steps.
  - Turnaround jump when switching direction.
- **FR-08: Interactive States**:
  - Click / Drag distinction: clicking triggers joyful spring bounce + emoji.
  - Sleep mode: renders `💤` after 20 minutes of inactivity.
  - Coding Burn mode: renders `🔥` upon receiving $>500\text{k}$ token bursts.

### 2.4 Audio & SFX Subsystem
- **FR-09: Cry Downloader**: Automatically downloads and caches official `.ogg` cries from PokéAPI.
- **FR-10: Chiptune Synthesizer**: Generates in-memory 8-bit level-up arpeggios ($C_5 \to E_5 \to G_5 \to C_6 \to E_6 \to G_6$) without bundled audio files.

---

## 3. Non-Functional Requirements (NFR)

- **NFR-01: 100% Local Privacy**: Zero token data, prompt logs, or code snippets are ever transmitted over the network.
- **NFR-02: Zero Bundled Copyright Assets**: Conforms to legal fair-use by resolving assets on-demand at runtime.
- **NFR-03: Performance & CPU Efficiency**: Background polling overhead must remain $\le 0.1\%$ CPU and $<60\text{MB}$ RAM when idle.
- **NFR-04: Cross-Display Support**: Pet coordinates must clamp within screen boundaries across all resolutions.
- **NFR-05: Modern Packaging & Developer Ergonomics**: Conforms to standard PEP 621 in `pyproject.toml`, supporting 1-command virtual environment synchronization via `uv`, automated code formatting/linting via `Ruff`, and developer environment flag overrides via `.env`.

