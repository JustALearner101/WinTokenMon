# 🧪 Internal Beta Testing & Feedback Guide: WinTokenMon

Panduan lengkap untuk menjalankan pengujian beta internal bersama teman-teman tester sebelum peluncuran publik resmi.

---

## 📦 1. Cara Mendistribusikan File ke Teman Tester

Teman tester Anda **tidak perlu meng-install Python atau Git** sama sekali.

1. Buka folder `dist/` di komputer Anda:
   `dist/WinTokenMon-v0.1.0-beta-Portable.exe` (Ukuran $\approx 28\text{MB}$).
2. Kirimkan file `.exe` tersebut ke teman-teman tester (melalui Google Drive, Discord, Telegram, atau flashdisk).
3. Instruksi ke tester:
   > *"Tinggal download file `.exe`-nya, double click untuk jalankan. Kalau muncul popup biru Windows SmartScreen ('Windows protected your PC'), klik 'More info' lalu klik 'Run anyway' ya!"*

---

## 📝 2. Cara Membuat Google Form Rekap Feedback Otomatis

Script otomatis generator Google Form sudah tersedia di [`scripts/generate_feedback_form.js`](../scripts/generate_feedback_form.js).

### Langkah Menjalankan (Hanya butuh 30 Detik):
1. Buka browser dan pergi ke **[script.google.com](https://script.google.com)** (pastikan login dengan akun Google Anda).
2. Klik tombol **"New Project"** (Proyek Baru) di pojok kiri atas.
3. Hapus teks `function myFunction() {}` yang ada di editor.
4. Buka file [`scripts/generate_feedback_form.js`](../scripts/generate_feedback_form.js), copy seluruh isinya, dan **Paste** ke editor Google Apps Script.
5. Klik tombol **Save** (💾) atau tekan `Ctrl + S`.
6. Klik tombol **Run** (▶️ Jalankan) di bagian atas.
   *(Jika pertama kali, Google akan meminta izin otorisasi `Review permissions` $\to$ pilih akun Anda $\to$ klik `Advanced` $\to$ klik `Go to Untitled project (unsafe)` $\to$ klik `Allow`).*
7. Buka tab **Execution log** di bagian bawah editor. Anda akan melihat:
   - 📝 **Link Edit & Kelola Form**: Link untuk Anda melihat grafik jawaban & spreadsheet.
   - 🔗 **Link Publik**: Link yang siap Anda bagikan ke teman-teman tester!

---

## 📊 3. Struktur Pertanyaan yang Dibuat

Formulir otomatis ini dibagi menjadi 4 bagian terstruktur:

1. **💻 Profil Tester & Setup Perangkat**:
   - Nama tester, versi Windows (Win 11 / Win 10), setup monitor (Single / Dual DPI), dan AI tools yang aktif dipakai (Antigravity, Cursor, Claude, Codex, Copilot).
2. **🛠️ First Launch & Kestabilan**:
   - Rating kelancaran buka `.exe` (Skala 1–5), popup Windows SmartScreen, riwayat crash/freeze, dan kronologi error.
3. **🎮 Fitur, Animasi & Visual UX**:
   - Rating kelucuan animasi melangkah (Skala 1–5), fitur paling favorit, akurasi pertambahan token saat koding, dan kenyamanan posisi pet di layar.
4. **💡 Wishlist Fitur Mendatang & Net Promoter Score**:
   - Pilihan fitur yang paling ditunggu (Achievements, Minigame lempar makan, Pertarungan LAN, HUD Pill), kolom saran bebas/kritik, dan Net Promoter Score (Skala 1–10).

---

## 🎯 4. Hal yang Perlu Diperhatikan Saat Menganalisis Feedback

- **Jika token tidak bertambah**: Tanyakan apakah tester sudah mengetik prompt dan menunggu tool AI selesai merespons (karena token di-flush ke file log lokal saat giliran chat selesai).
- **Jika ada yang mengeluhkan pet menutupi tombol**: Ingatkan bahwa pet bisa di-drag bebas dengan klik kiri tahan, atau klik kanan di icon tray taskbar lalu pilih *Snap to Taskbar*.

---

## 🛠️ 5. Tips Pengujian untuk Tester Developer (Source Code & Debug Flags)

Bagi tester yang ingin menguji langsung dari repositori source code:
1. Jalankan langsung dengan `uv`:
   ```powershell
   uv sync
   uv run main.py
   ```
2. Buat file `.env` dari `.env.example` untuk menguji skenario ekstrem tanpa harus menunggu:
   - `WINTOKENMON_MOCK_DELTA=2500000`: Langsung menetaskan starter egg pada tick pertama!
   - `WINTOKENMON_POLL_INTERVAL=2`: Mempercepat responsivitas polling untuk pengujian cepat.
   - `WINTOKENMON_DEBUG=1`: Melihat trace output error langsung di terminal.

