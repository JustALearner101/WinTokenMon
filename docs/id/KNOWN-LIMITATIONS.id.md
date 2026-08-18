# ⚠️ Batasan Teknis, Karakteristik Platform & Solusi Komunitas

> **Language / Bahasa**: [**English**](../KNOWN-LIMITATIONS.md) | [**Bahasa Indonesia**](KNOWN-LIMITATIONS.id.md)

Dokumen ini menguraikan batasan teknis, perilaku khusus pada platform Windows, dan solusi praktis untuk **WinTokenMon (`v0.1.0-beta`)**.

---

## 📋 Ringkasan Batasan Teknis

| Area | Batasan | Penyebab Teknis | Solusi / Rekomendasi |
| :--- | :--- | :--- | :--- |
| **🪟 Transparansi** | Piksel garis tepi tipis pada beberapa tema gelap | Tkinter di Windows menggunakan transparansi biner colorkey (`-transparentcolor`), bukan saluran alpha 8-bit per-piksel. | Kami menerapkan scaling piksel `NEAREST` yang tajam. Menyesuaikan wallpaper desktop atau mengatur opacity di Settings dapat meminimalkan halo piksel. |
| **🖥️ Multi-Monitor** | Potensi lompatan ukuran pada monitor beda DPI | Proses Tkinter mewarisi faktor skala DPI monitor utama (misal 150% 4K utama vs 100% 1080p sekunder). | Sistem pengunci batas layar menjaga pet tetap aman di dalam monitor. Menyamakan skala DPI di Windows Display Settings memberikan hasil terbaik. |
| **🎮 Game Fullscreen** | Pet tertutup saat bermain game 3D eksklusif | DirectX / Vulkan "Exclusive Fullscreen" mengambil alih framebuffer GPU utama, melewati manajer jendela desktop. | Jalankan game atau aplikasi fullscreen dalam mode **"Borderless Windowed"** jika ingin Pokémon tetap terlihat. |
| **⏱️ Latensi Ingesti** | Jeda 0–10 detik pada pembaruan jumlah token | Polling berjalan pada siklus sweep 10 detik dengan cache status file $O(1)$ untuk memastikan **0% beban CPU di background**. | Normal sesuai desain. Token akan diperbarui pada siklus sweep berikutnya setelah IDE menulis log ke disk. |
| **🌐 Mode Offline** | Spesies baru yang baru menetas menampilkan telur fallback | Sprite GIF dan suara cry diunduh secara on-demand dari PokéAPI / Showdown CDN agar bebas dari bundel ROM berhak cipta. | Pokémon yang pernah menetas tersimpan permanen di `%APPDATA%\WinTokenMon\`. Spesies baru saat offline otomatis fallback ke sprite Telur & synthesizer chiptune 8-bit tanpa crash. |
| **🎨 Variasi Sprite** | Sprite bawaan API hanya memiliki animasi diam battle | Endpoint publik PokéAPI/Showdown hanya menyediakan GIF pose bertarung diam (tidak ada sprite sheet animasi jalan/tidur bawaan). | Fisika berjalan prosedural (loncatan langkah vertikal, frame rate lebih cepat, goyangan beban, dan partikel debu) mensimulasikan gerakan langkah nyata. |
| **📌 Taskbar Snap** | Sedikit tumpang tindih dengan Taskbar Auto-Hide | Penempelan ke taskbar menggunakan konstanta tinggi taskbar standar Windows (48px). | Jika menggunakan "Auto-Hide Taskbar", geser pet beberapa piksel lebih tinggi di layar. |

---

## 🔍 Penjelasan Mendalam

### 1. Batasan Sprite Battle Showdown vs. Fisika Berjalan Prosedural
Repositori komunitas PokéAPI dan Pokémon Showdown secara eksklusif hanya menyediakan **animasi idle bertarung** dari game Nintendo DS Generasi V. Tidak ada sprite sheet resmi untuk berjalan, berlari, tidur, atau makan yang disediakan oleh API publik tersebut.
- **Bagaimana WinTokenMon Mensimulasikan Gerakan Nyata**: Daripada sekadar menggeser animasi diam seperti meluncur di atas es, mesin animasi kustom kami memprogram gerakan secara prosedural:
  1. Mempercepat pergantian frame GIF dari $100\text{ms}$ (saat diam) menjadi $50\text{ms}$ (saat melangkah) agar anggota badan bergerak lebih aktif.
  2. Menerapkan kurva pantulan langkah kaki vertikal berirama ($Y = -|6 \cdot \sin(t)|$) dan ayunan beban langkah ($X = 2.5 \cdot \sin(t)$).
  3. Memunculkan kepulan partikel debu (`💨`) dan loncatan kecil saat berbalik arah (*turnaround jump*).

---

### 2. Transparansi Colorkey vs. Alpha Per-Piksel Nyata
Di Windows, jendela Tkinter standar mencapai transparansi menggunakan masking colorkey (`wm_attributes("-transparentcolor", colorkey)`). Setiap piksel yang warnanya cocok (misal `#000001`) menjadi 100% tembus pandang.
- **Mengapa ini penting**: Antialiasing semi-transparan (misal bayangan 50% opacity) tercampur dengan warna colorkey sebelum dipotong Windows, sehingga dapat memunculkan garis tepi tipis 1px.
- **Solusi Kami**: Kami memproses ulang frame GIF animasi Showdown menggunakan Pillow dengan kuantisasi *nearest-neighbor* yang ketat (`Image.Resampling.NEAREST`), menjaga estetika pixel-art retro Generasi V tetap tajam tanpa artefak blur.

---

## 💡 Ajakan Solusi & Pull Request Komunitas

Apakah Anda menemukan solusi yang lebih baik, atau berpengalaman dengan Windows Win32 API / C-extensions? Kami sangat menyambut kontribusi dan Pull Request dari komunitas!

### 🌟 Tantangan Terbuka yang Siap Digarap:
1. **🚀 True Per-Pixel Alpha Blitting (`UpdateLayeredWindow`)**:
   - Implementasi renderer layered window Win32 / `ctypes` Direct2D untuk antialiasing 32-bit ARGB halus dan bayangan nyata di Windows.
2. **🖥️ Dynamic Per-Monitor DPI Awareness (v2)**:
   - Menambahkan hook Win32 `SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)` untuk kalkulasi geometri dinamis saat digeser melintasi monitor dengan DPI berbeda.
3. **⚡ File System Event Watcher Real-Time (`ReadDirectoryChangesW`)**:
   - Integrasi watcher notifikasi perubahan direktori non-blocking untuk mendeteksi penulisan log secara instan bersamaan dengan polling 10 detik.
4. **🔌 Parser Tool AI Baru**:
   - Menambahkan scanner untuk tools AI baru (Aider, Windsurf/Cascade, Roo Code, Cline).

### Cara Berkontribusi
- Baca [Panduan Operasional & HOWTO](HOWTO.id.md) kami.
- Buka GitHub Issue untuk mendiskusikan usulan arsitektur Anda, atau langsung ajukan Pull Request!
