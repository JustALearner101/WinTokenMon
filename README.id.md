# 🐾 WinTokenMon — PokeTokenBar untuk Windows

<div align="center">

🌐 [**English**](README.md) • **Bahasa Indonesia**

<br/>

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Version](https://img.shields.io/badge/Version-v0.1.0--beta-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Lokal-2EA44F?style=for-the-badge&logo=shield&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

**Ubah konsumsi token AI harianmu menjadi teman Pokémon hidup di desktop Windows!**  
*Porting desktop Windows asli terinspirasi dari [PokeTokenBar (macOS)](https://github.com/chattymin/PokeTokenBar) (lihat [Kredit](reference/README.md)).*

</div>

---

## ✨ Fitur Utama

### 1. 🤖 Pembaca Token AI Multi-Provider Lokal (Hemat Sumber Daya & Inkremental)
- **Tanpa Konfigurasi & Tanpa API Key**: Otomatis mendeteksi dan menjumlahkan konsumsi token langsung dari file log lokal:
  - **Antigravity CLI** (`~/.gemini/antigravity-cli/conversations/*.db`)
  - **Claude Code** (`~/.claude/projects/**/*.jsonl`)
  - **Cursor IDE** (`%APPDATA%/Cursor/User/globalStorage/state.vscdb`)
  - **Codex CLI** (`~/.codex/sessions/**/rollout-*.jsonl`)
  - **GitHub Copilot CLI** (`~/.copilot/session-store.db`)
  - **Koma (aula-id/koma)** (`~/.koma/sessions/*.json` & `~/.koma/ledger/*.jsonl`)
- **Pemindaian Ekor Inkremental (Incremental Tail Scanning)**: Hanya memproses baris log baru dalam waktu $O(\Delta)$, memangkas beban CPU background hingga >85%.
- **100% Privat & Offline**: Hanya membaca metadata jumlah token. Kode program dan prompt Anda tidak pernah dibaca, disimpan, atau dikirim ke internet.

### 2. 🐾 Desktop Pet Interaktif & Animasi Melangkah
- **Jendela Transparan Frameless**: Bergerak bebas di desktop Windows tanpa batas jendela hitam.
- **👣 Fisika Berjalan Realistis**:
  - Langkah kaki berirama meloncat ke atas ($Y = -|6 \cdot \sin(t)|$) dan bergoyang alami.
  - Pergantian frame GIF **2x lebih cepat** saat berjalan (50ms vs 100ms saat diam).
  - Kepulan partikel debu kecil (`💨`) di belakang tumit kaki saat melangkah.
  - Loncatan kecil berbalik arah (*turnaround jump*) saat berganti haluan.
- **Interaksi Sentuh & Mood**:
  - Klik / Elus: Menghasilkan loncatan ceria dan emoji reaksi (`💖`, `✨`, `🎉`, `🎵`, `🔥`).
  - Mode Tidur: Menampilkan gelembung `💤` jika tidak ada aktivitas koding selama 20 menit.
  - Mode Koding Terbakar: Menampilkan nyala api `🔥` saat membakar $>500\text{k}$ token dalam waktu singkat.
  - Goyangan Telur: Telur mulai bergoyang saat progress mencapai $\ge 90\%$.

### 3. 🐣 Pemilihan Starter (Gen 1–9), Evolusi & Upacara
- **Pilih Starter Pokémon Favorit**: Saat pertama kali install, pilih starter dari Generasi 1 hingga Generasi 9 (Bulbasaur, Charmander, Squirtle, Cyndaquil, Torchic, Mudkip, Piplup, Froakie, Rowlet, Sprigatito, Fuecoco, Quaxly, Pikachu, Eevee, Riolu) lengkap dengan modal konfirmasi!
- **Suara Asli Pokémon (Cry)**: Diunduh secara on-demand dari PokéAPI dan disimpan di cache lokal.
- **Synthesizer Fanfare Level-Up 8-Bit**: Arpeggio retro chiptune yang disintesis secara in-memory tanpa memerlukan file audio eksternal.
- **Berburu Varian Shiny (`✨`)**: Peluang dasar 1 banding 129 untuk mendapatkan varian Shiny, bisa ditingkatkan menjadi 1 banding 40 dengan Shiny Charm!

### 4. 📊 Dashboard Modular & Pokédex Dual-View
- **Buka Instan (< 50ms)**: Arsitektur modular (`ui/tabs/` dan `ui/modals/`) dengan pemuatan tab secara *lazy*.
- **Tema Aksen Elemen Dinamis**: Warna latar dan border otomatis beradaptasi dengan elemen Pokémon aktif (Grass 🌿, Fire 🔥, Water 💧, Electric ⚡, Psychic 🔮, Dragon 🐉, Fighting 🥋, Normal ⭐).
- **Pokédex & Catch Log Dual-View**:
  - **📖 Grid Pokédex**: Tampilan kartu ringan spesies terdaftar yang dimiliki.
  - **📜 Catch Log**: Riwayat kronologis kelulusan dan penetasan lengkap dengan catatan waktu dan kepribadian (Nature).
- **Toko Item & Tier Telur**: Beli Rare Candy (+100M EXP), Nature Mint (20 kepribadian), Shiny Charm, dan Telur Tier Tinggi.

### 5. 🪟 Integrasi Native Windows System Tray & Notifikasi
- **System Tray Tooltip**: Lihat total token hari ini dan persentase hatching langsung dari taskbar.
- **Windows Native Toast**: Peringatan batas anggaran token harian pada $80\%$ dan $100\%$.

---

## 🚀 Panduan Memulai

### 1. Prasyarat
- Windows 10 atau Windows 11 (64-bit)
- Python 3.10, 3.11, 3.12, atau 3.14+

### 2. Instalasi & Menjalankan

1. **Clone repositori**:
   ```powershell
   git clone https://github.com/YourUsername/WinTokenMon.git
   cd WinTokenMon
   ```

2. **Jalankan (Opsi A: Cepat dengan `uv` — Direkomendasikan)**:
   ```powershell
   # Setup virtual environment & dependensi otomatis
   uv sync
   uv run main.py
   ```

3. **Jalankan (Opsi B: Standar dengan `pip`)**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python main.py
   ```

4. **Jalankan di Background**:
   - Double-click `run.bat` atau `run_silent.vbs` (aplikasi berjalan senyap di background tray).

### 🛠️ Mode Pengembangan & Variabel Lingkungan (.env)

WinTokenMon mendukung konfigurasi developer opsional melalui file `.env`. Cukup salin template:
```powershell
Copy-Item .env.example .env
```
Flags yang tersedia:
- `WINTOKENMON_DEBUG=1`: Menampilkan log debug verbose di konsol/terminal.
- `WINTOKENMON_POLL_INTERVAL=5`: Mengatur interval polling token (dalam detik).

---

## 🎮 Kontrol & Interaksi

| Aksi | Efek |
| :--- | :--- |
| **Klik Kiri Pet** | Memicu animasi melompat + emoji reaksi |
| **Klik & Tahan (Drag)** | Memindahkan posisi Pokémon di layar |
| **Hover Kursor** | Menampilkan tooltip ringkasan token |
| **Double-Click Pet / Ikon Tray** | Membuka Dashboard & Pokédex |
| **Klik Kanan Ikon Tray** | Menu cepat (Dashboard, Auto-Roaming, Taskbar Snap, Keluar) |

---

## 🤖 AI Coding Tools yang Didukung

| AI Assistant | Lokasi File di Windows | Mode Pembacaan |
| :--- | :--- | :--- |
| **Antigravity CLI** | `~/.gemini/antigravity-cli/conversations/*.db` | Protobuf Read-only |
| **Claude Code** | `~/.claude/projects/**/*.jsonl` | Ekor Inkremental JSONL |
| **Cursor IDE** | `%APPDATA%/Cursor/User/globalStorage/state.vscdb` | SQLite Read-only (`mode=ro`) |
| **Codex CLI** | `~/.codex/sessions/**/rollout-*.jsonl` | Ekor Inkremental JSONL |
| **GitHub Copilot CLI** | `~/.copilot/session-store.db` | SQLite Read-only (`mode=ro`) |
| **Koma** | `~/.koma/sessions/*.json` & `~/.koma/ledger/*.jsonl` | Ekor Inkremental JSONL / JSON |

---

## 📚 Dokumentasi Teknis

- 🛠️ [**Panduan Operasional & HOWTO**](docs/id/HOWTO.id.md): Panduan langkah-demi-langkah menjalankan lokal, debugging dengan `.env`, kompilasi `.exe`, dan membuat installer wizard.
- 🏗️ [**Arsitektur & Desain Sistem**](docs/id/ARCHITECTURE.id.md): Penjelasan alur parser token, arsitektur dashboard modular, dan loop UI.
- 🎮 [**Panduan Balance & Ekonomi Game**](docs/id/BALANCE.id.md): Kurva progresi matematika, tier telur, dan ekonomi shop.
- 🗺️ [**Roadmap & Rencana Masa Depan**](docs/id/FUTURE-WORKS.md): Fitur achievements, minigame memberi makan, dan HUD compact.
- ⚠️ [**Batasan Teknis & FAQ**](docs/id/KNOWN-LIMITATIONS.id.md): Penjelasan transparansi colorkey, multi-monitor, dan solusinya.
- 🛡️ [**Kebijakan Keamanan & Privasi**](docs/id/SECURITY.id.md): Jaminan privasi 100% lokal.
<!-- - 🤝 [**Panduan Kontribusi**](docs/id/CONTRIBUTING.id.md): Cara menambahkan scanner tool AI baru. -->

---

## ⚖️ Pemberitahuan Hak Cipta & Fair Use

**WinTokenMon** adalah proyek penggemar independen, open-source, dan non-komersial untuk produktivitas developer di bawah prinsip Fair Use.

- Pokémon dan nama-nama karakter Pokémon adalah merek dagang terdaftar milik **Nintendo**, **Creatures Inc.**, dan **GAME FREAK inc.**
- **Kepatuhan Aset NFR-01**: Repositori ini tidak mendistribusikan ROM game berhak cipta, artwork proprietary, atau audio komersial. Semua sprite dan suara cry diunduh saat aplikasi berjalan dari endpoint publik komunitas dan di-cache secara lokal oleh pengguna.
- Lihat [`DISCLAIMER.md`](DISCLAIMER.md) ([Versi Indonesia](docs/id/DISCLAIMER.id.md)) untuk pemberitahuan hukum lengkap.

---

<div align="center">
Dibuat dengan ❤️ untuk para developer yang koding bersama AI.
</div>
