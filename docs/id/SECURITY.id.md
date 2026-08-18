# 🛡️ Kebijakan Keamanan & Privasi

> **Language / Bahasa**: [**English**](../../SECURITY.md) | [**Bahasa Indonesia**](SECURITY.id.md)

## 🔒 Filosofi Privasi
**WinTokenMon** dibangun dengan arsitektur yang mengutamakan privasi 100%:

1. **Eksekusi 100% Lokal**: Aplikasi berjalan sepenuhnya di dalam sistem operasi Windows lokal Anda.
2. **Tanpa Pengiriman Data Eksternal**:
   - Kode sumber proyek, repositori, API key, output terminal, dan teks prompt chat Anda **TIDAK PERNAH** dikirimkan melalui internet.
   - WinTokenMon hanya membaca metadata numerik jumlah token (`input_tokens`, `output_tokens`, `cache_tokens`) dan penanda waktu (*timestamp*).
3. **Pemeriksaan Hanya-Baca (Read-Only)**:
   - Semua kueri SQLite (seperti Cursor `state.vscdb` dan Copilot `session-store.db`) dieksekusi secara ketat dalam mode read-only yang tidak dapat diubah (`mode=ro`).
   - WinTokenMon tidak pernah mengubah atau menulis ke file status IDE atau tool CLI Anda.

---

## 🌐 Aktivitas Jaringan Eksternal
Aplikasi hanya melakukan koneksi internet keluar dalam skenario spesifik berikut:
- **Pengunduhan Sprite**: Mengunduh sprite GIF/PNG animasi dari CDN publik PokéAPI/Showdown GitHub (`raw.githubusercontent.com/PokeAPI/sprites`) saat pertama kali menetas/berevolusi menjadi spesies baru.
- **Pengunduhan Suara Cry**: Mengunduh file audio publik `.ogg` dari `raw.githubusercontent.com/PokeAPI/cries` saat pertama kali bertemu spesies tersebut.

Kedua jenis aset tersebut disimpan secara permanen di `%APPDATA%\WinTokenMon\`, sehingga tidak memerlukan panggilan jaringan lagi untuk pemutaran selanjutnya.

---

## 🐛 Melaporkan Kerentanan Keamanan
Jika Anda menemukan potensi celah keamanan atau bug privasi:
1. Jangan membuat GitHub Issue publik.
2. Silakan hubungi maintainer secara privat melalui repositori atau email kontak maintainer.
