# 🛡️ Security & Privacy Policy

> **Language / Bahasa**: [**English**](SECURITY.md) | [**Bahasa Indonesia**](docs/id/SECURITY.id.md)

## 🔒 Privacy Philosophy
**WinTokenMon** is built with an absolute privacy-first architecture:

1. **Local-Only Execution**: The application runs entirely on your local Windows operating system.
2. **Zero External Data Exfiltration**:
   - Your source code, repositories, API keys, terminal outputs, and chat prompts are **NEVER** transmitted over the internet.
   - WinTokenMon only inspects numeric token usage metadata (`input_tokens`, `output_tokens`, `cache_tokens`) and timestamps.
3. **Read-Only Inspection**:
   - All SQLite queries (such as Cursor `state.vscdb` and Copilot `session-store.db`) are executed strictly in immutable read-only mode (`mode=ro`).
   - WinTokenMon never modifies or writes to your IDE or CLI state files.

---

## 🌐 External Network Activity
The application only establishes outbound network connections in these specific scenarios:
- **Sprite Download**: Downloading animated GIF/PNG sprites from the public PokeAPI/Showdown GitHub CDN (`raw.githubusercontent.com/PokeAPI/sprites`) upon hatching/evolving a newly encountered Pokémon species.
- **Audio Cry Download**: Downloading public `.ogg` audio files from `raw.githubusercontent.com/PokeAPI/cries` upon encountering a species.

Both asset types are cached permanently in `%APPDATA%\WinTokenMon\`, requiring zero network calls for subsequent viewings.

---

## 🐛 Reporting a Vulnerability
If you discover a security issue or unexpected behavior:
1. Please open a private Security Advisory on GitHub or email the maintainers directly.
2. We strive to address all security inquiries within 48 hours.
