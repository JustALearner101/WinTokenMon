# 🛠️ Panduan Operasional & How-To Developer: WinTokenMon

> **Language / Bahasa**: [**English**](../HOWTO.md) | [**Bahasa Indonesia**](HOWTO.id.md)

Selamat datang di **Buku Panduan Developer WinTokenMon**! Dokumen ini menyediakan instruksi langkah-demi-langkah (*step-by-step*) yang siap Anda salin untuk menjalankan aplikasi, konfigurasi lingkungan, menambah tab/modal baru, menambah spesies Pokémon, menjalankan test/linter, mengompilasi binary portable `.exe`, hingga membuat installer wizard resmi Windows.

---

## 📑 Daftar Isi

1. [🚀 Menjalankan Aplikasi Secara Lokal (Dev Mode)](#1--menjalankan-aplikasi-secara-lokal-dev-mode)
2. [🛠️ Debugging & Konfigurasi Lingkungan (.env)](#2-️-debugging--konfigurasi-lingkungan-env)
3. [🧪 Menjalankan Unit Test & Linter](#3--menjalankan-unit-test--linter)
4. [🧩 Mengembangkan Arsitektur Dashboard Modular](#4--mengembangkan-arsitektur-dashboard-modular)
5. [🌿 Menambahkan Garis Evolusi & Spesies Pokémon Baru](#5--menambahkan-garis-evolusi--spesies-pokémon-baru)
6. [📦 Mengompilasi Single-File Portable Executable (`.exe`)](#6--mengompilasi-single-file-portable-executable-exe)
7. [🧙‍♂️ Mengompilasi Setup Wizard Installer Resmi (`Setup.exe`)](#7-️-mengompilasi-setup-wizard-installer-resmi-setupexe)
8. [🧹 Menguji Installer & Uninstaller di Windows](#8--menguji-installer--uninstaller-di-windows)
9. [🔄 Reset Data State untuk Menguji Wizard First-Launch](#9--reset-data-state-untuk-menguji-wizard-first-launch)
10. [❓ Tanya Jawab & Troubleshooting Masalah Umum](#10--tanya-jawab--troubleshooting-masalah-umum)

---

## 1. 🚀 Menjalankan Aplikasi Secara Lokal (Dev Mode)

### Menggunakan `uv` (Direkomendasikan — Cepat & Otomatis)
```powershell
# 1. Sinkronisasi dependencies otomatis
uv sync --all-extras

# 2. Jalankan aplikasi
uv run main.py
```

### Menggunakan Python Virtual Environment Standar (`venv` + `pip`)
```powershell
# 1. Buat dan aktifkan virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Pasang dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 3. Jalankan aplikasi
python main.py
```

---

## 2. 🛠️ Debugging & Konfigurasi Lingkungan (.env)

WinTokenMon menyediakan flag developer untuk pengujian:

1. Salin `.env.example` menjadi `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Buka `.env` dan atur parameter pengujian:
   ```ini
   # Aktifkan log verbose di terminal
   WINTOKENMON_DEBUG=1

   # Percepat interval polling (misal: 5 detik alih-alih 10 detik)
   WINTOKENMON_POLL_INTERVAL=5
   ```

3. Jalankan `uv run main.py`.

---

## 3. 🧪 Menjalankan Unit Test & Linter

### Jalankan Unit Test (`pytest`)
```powershell
# Jalankan seluruh test suite (31 unit tests)
pytest

# Jalankan dengan output verbose detail
pytest -v

# Jalankan file test tertentu
pytest tests/test_token_reader.py
```

### Jalankan Linter & Formatter (`Ruff`)
```powershell
# Cek kesalahan linter
ruff check .

# Perbaiki kesalahan linter otomatis
ruff check --fix .

# Verifikasi formatting tanpa mengubah file
ruff format --check .

# Format seluruh file otomatis
ruff format .
```

---

## 4. 🧩 Mengembangkan Arsitektur Dashboard Modular

Dashboard tersusun atas view tab dan dialog modal yang terisolasi dan ringan:

```
ui/
├── dashboard.py                  # Window Coordinator (< 200 baris)
├── dashboard_theme.py            # Palet warna, tema tipe, dan lore
├── modals/
│   ├── nature_modal.py           # NatureSelectorModal
│   └── pokedex_inspector_modal.py # PokedexInspectorModal
└── tabs/
    ├── home_tab.py               # HomeTabView (HUD & Grafik 7 Hari)
    ├── pokedex_tab.py            # PokedexTabView (Pokédex & Catch Log)
    ├── shop_tab.py               # ShopTabView (Toko & Tas)
    └── settings_tab.py           # SettingsTabView (Preferensi & Limit)
```

### Menambahkan Tab Baru:
1. Buat file `ui/tabs/fitur_baru_tab.py` dengan class `FiturBaruTabView`:
   ```python
   import customtkinter as ctk

   class FiturBaruTabView:
       def __init__(self, parent: ctk.CTkFrame, dashboard):
           self.parent = parent
           self.dashboard = dashboard
           self._build_ui()

       def _build_ui(self):
           ctk.CTkLabel(self.parent, text="🚀 Fitur Baru", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

       def refresh(self):
           pass
   ```
2. Ekspor di `ui/tabs/__init__.py`.
3. Di `ui/dashboard.py`, tambahkan tab ke `self.tabview` dan muat secara *lazy* di dalam `_on_tab_change()`.

---

## 5. 🌿 Menambahkan Garis Evolusi & Spesies Pokémon Baru

Seluruh garis evolusi dan metadata Pokémon diindeks di `core/poke_api.py`:

1. Tambahkan rantai evolusi ke `CURATED_EVOLUTION_LINES` di `core/poke_api.py`:
   ```python
   {
       "chain": [447, 448],
       "names": ["Riolu", "Lucario"],
       "stages": 2,
       "rarity": "rare",
   }
   ```
2. Dictionary `SPECIES_INDEX` otomatis mengindeks setiap ID spesies untuk pencarian $O(1)$ di seluruh aplikasi.
3. Letakkan file animasi `.gif` di `assets/sprites/<id>.gif` (contoh: `assets/sprites/447.gif`).

---

## 6. 📦 Mengompilasi Single-File Portable Executable (`.exe`)

Untuk mengompilasi binary portable satu file tanpa instalasi:

```powershell
uv run python scripts/build_exe.py
```

### Output File:
- 🚀 **`dist/WinTokenMon-v0.1.0-beta-Portable.exe`** (~28.9 MB)

---

## 7. 🧙‍♂️ Mengompilasi Setup Wizard Installer Resmi (`Setup.exe`)

Untuk membuat installer wizard resmi Windows (Inno Setup 6):

### Langkah 1: Pastikan Inno Setup 6 Terpasang
```powershell
winget install --id JRSoftware.InnoSetup --accept-source-agreements --accept-package-agreements --silent
```

### Langkah 2: Jalankan Pipeline Build Otomatis
```powershell
uv run python scripts/build_installer.py
```

### Output File:
- 📦 **`dist/WinTokenMon-Setup-v0.1.0-beta.exe`** (~30.6 MB)

---

## 8. 🧹 Menguji Installer & Uninstaller di Windows

### Menguji Instalasi:
1. Klik ganda `dist/WinTokenMon-Setup-v0.1.0-beta.exe`.
2. Klik tombol **Browse...** untuk menguji instalasi ke folder kustom.
3. Centang opsi **Desktop Shortcut** dan **Start on Windows Boot**.
4. Selesaikan instalasi dan pastikan aplikasi langsung berjalan dan melayang di desktop.

### Menguji Uninstaller:
1. Buka **Windows Settings** $\to$ **Apps** $\to$ **Installed Apps** (atau Control Panel).
2. Cari **WinTokenMon (Beta)** dan klik **Uninstall**.
3. Perhatikan dialog konfirmasi:
   - Memilih **`[No]` (Default)** akan mempertahankan file save di `%APPDATA%\WinTokenMon` (aman untuk update versi).
   - Memilih **`[Yes]`** akan menghapus bersih seluruh data aplikasi dan cache.

---

## 9. 🔄 Reset Data State untuk Menguji Wizard First-Launch

Untuk menguji **Pemilihan Starter Gen 1 - Gen 9** dari kondisi bersih (*clean state*):

```powershell
# Tutup aplikasi WinTokenMon jika sedang berjalan
Stop-Process -Name "WinTokenMon*" -ErrorAction SilentlyContinue

# Hapus file save state
Remove-Item "$env:APPDATA\WinTokenMon\state.json" -Force -ErrorAction SilentlyContinue

# Jalankan aplikasi untuk memicu wizard starter
uv run main.py
```

---

## 10. ❓ Tanya Jawab & Troubleshooting Masalah Umum

### Q1: Error `customtkinter` atau aset hilang setelah build PyInstaller?
**Solusi**: `scripts/build_exe.py` dan `scripts/build_installer.py` secara otomatis mendeteksi dan membundel aset `customtkinter/` via `--add-data`. Pastikan Anda melakukan build via `uv run python scripts/build_installer.py`.

### Q2: Suara cry / SFX tidak bersuara?
**Solusi**: Pastikan perangkat audio Windows aktif. Pygame mixer diinisialisasi secara non-blocking; jika tidak ada output audio aktif, mixer akan terdegradasi secara diam-diam tanpa menyebabkan aplikasi crash.

### Q3: Penggunaan token AI lokal tidak muncul?
**Solusi**: Pastikan alat AI Anda telah membakar token hari ini. WinTokenMon memindai path standar berikut:
- Antigravity CLI: `~/.gemini/antigravity-cli/conversations/*.db`
- Claude Code: `~/.claude/projects/**/*.jsonl`
- Cursor IDE: `%APPDATA%/Cursor/User/globalStorage/state.vscdb`
- Codex CLI: `~/.codex/sessions/**/rollout-*.jsonl`
- GitHub Copilot: `~/.copilot/session-store.db`
- Koma: `~/.koma/sessions/*.json` dan `~/.koma/ledger/*.jsonl`
