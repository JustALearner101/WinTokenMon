# 📋 Product Requirement Document (PRD): WinTokenMon

> **Language / Bahasa**: [**English**](../PRD.md) | [**Bahasa Indonesia**](PRD.id.md)

---

## 1. Ringkasan Eksekutif

**WinTokenMon** adalah aplikasi desktop produktivitas developer berbasis open-source yang memantau penggunaan token AI coding (Antigravity CLI, Claude Code, Cursor IDE, Codex CLI, GitHub Copilot CLI) secara real-time. Dengan mengubah konsumsi token pasif menjadi pendamping Pokémon interaktif yang dapat berjalan, bereaksi, menetas dari telur, dan berevolusi, para developer mendapatkan visualisasi konsumsi AI mereka secara menyenangkan dan intuitif.

Berbeda dari versi macOS yang terbatas pada Menu Bar, **WinTokenMon** mengadopsi paradigma native Windows:
- **Floating Desktop Pet (Gaya Shimeji)** transparan tanpa bingkai yang dapat menjelajah desktop secara otomatis dengan fisika langkah kaki nyata.
- **Windows System Tray** dengan penghitung token langsung dan notifikasi Windows Toast untuk batas anggaran.
- **Dashboard CustomTkinter** dengan analitik 7 hari, Pokédex lengkap, dan toko item.

---

## 2. Kebutuhan Fungsional Utama (FR)

### 2.1 Modul Pembaca Token Multi-Provider
- **FR-01: Deteksi Otomatis**: Secara otomatis memindai dan mengakumulasikan log token lokal dari:
  - **Antigravity CLI**: `~/.gemini/antigravity-cli/conversations/*.db` (Parsing biner Protobuf).
  - **Claude Code**: `~/.claude/projects/**/*.jsonl`.
  - **Cursor IDE**: `%APPDATA%\Cursor\User\globalStorage\state.vscdb` (SQLite mode `mode=ro`).
  - **Codex CLI**: `~/.codex/sessions/**/rollout-*.jsonl`.
  - **GitHub Copilot CLI**: `~/.copilot/session-store.db`.
- **FR-02: Performa Tanpa Kunci (Zero-Locking)**: Semua pembacaan file bersifat read-only. Cache status file $(mtime, size)$ memastikan pembacaan cepat $O(1)$ untuk file yang tidak berubah.

### 2.2 Progresi Pendamping & Ekonomi Game
- **FR-03: Penetasan Telur Bertingkat**:
  - `Standard Egg`: 2.5M token.
  - `Uncommon Egg`: 6M token.
  - `Rare Egg`: 15M token.
  - `Legendary Egg`: 35M token.
- **FR-04: Formula Progresi Evolusi Aritmatika**:
  $$\text{Ambang Batas Stage} = \text{round}\left( \text{Total Kelulusan}(\text{Rarity}) \times \frac{i}{k(k+1)/2} \right)$$
- **FR-05: Ekonomi Toko**:
  - Poin belanja diperoleh 1:1 untuk setiap token AI yang dibakar.
  - Item tersedia: *Rare Candy* (+100M EXP), *Nature Mint* (acak ulang sifat/nature), *Shiny Charm* (meningkatkan peluang shiny dari 1/129 menjadi 1/40).

### 2.3 Presentasi Desktop Pet Interaktif
- **FR-06: Transparansi Frameless**: Dirender pada layered window menggunakan colorkey Windows (`-transparentcolor`).
- **FR-07: Fisika Langkah Kaki & Animasi Berjalan**:
  - Loncatan langkah kaki vertikal: $Y = -|6 \cdot \sin(t)|$.
  - Pergantian frame dipercepat 2x saat berjalan (50ms saat jalan vs 100ms saat diam).
  - Partikel kepulan debu (`💨`) setiap 7 langkah.
  - Loncatan kecil berbalik arah (*turnaround jump*).
- **FR-08: Status Interaktif**:
  - Pembedaan Klik / Geser: Klik menghasilkan pantulan gembira + emoji reaksi.
  - Mode Tidur: Menampilkan `💤` setelah 20 menit tidak ada aktivitas.
  - Mode Koding Terbakar: Menampilkan `🔥` saat menerima ledakan $>500\text{k}$ token.

### 2.4 Subsistem Audio & SFX
- **FR-09: Pengunduh Suara Asli (Cry)**: Otomatis mengunduh dan menyimpan suara resmi `.ogg` dari PokéAPI.
- **FR-10: Synthesizer Chiptune**: Menghasilkan arpeggio level-up 8-bit retro ($C_5 \to E_5 \to G_5 \to C_6 \to E_6 \to G_6$) secara in-memory tanpa perlu menyertakan file audio eksternal.

---

## 3. Kebutuhan Non-Fungsional (NFR)

- **NFR-01: Privasi 100% Lokal**: Tidak ada data token, teks prompt, atau potongan kode yang dikirim ke internet.
- **NFR-02: Bebas Aset Berhak Cipta**: Mematuhi aturan hukum fair use dengan mengunduh aset secara on-demand saat aplikasi berjalan.
- **NFR-03: Efisiensi CPU & Memori**: Penggunaan CPU di latar belakang harus $\le 0.1\%$ dan RAM $<60\text{MB}$ saat idle.
- **NFR-04: Kompatibilitas Multi-Monitor**: Koordinasi posisi pet harus selalu terkunci dalam batas layar di berbagai resolusi.
- **NFR-05: Kemudahan Toolchain & Standar Packaging Modern**: Mematuhi standar PEP 621 di `pyproject.toml`, mendukung setup virtual environment 1-perintah via `uv`, pemformatan dan linting otomatis via `Ruff`, serta penimpaan flag lingkungan developer via `.env`.

