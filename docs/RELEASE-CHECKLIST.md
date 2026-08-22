# 🚀 Release Checklist — v1.0.0 GA

> Pemegang kendali: **repo owner**. Merge & tag sengaja dieksekusi manual.
> Semua item di bawah ini adalah langkah terakhir setelah Fasa 1–5 RFC v1.0.0 selesai dikerjakan.

---

## 1. QA Manual (jalankan dari branch `preview`)

| # | Skenario | Cara Uji | Kriteria Lulus |
| :-- | :--- | :--- | :--- |
| 1 | Smoke run dasar | `python main.py`, biarkan 2 menit | Pet muncul, tidak ada error di `%APPDATA%\WinTokenMon\logs\wintokenmon.log` |
| 2 | Upgrade-install aman | Instal versi lama → burn token → instal versi baru | `state.json` utuh; companion & progres tidak reset |
| 3 | Recovery save korup | Korupkan `state.json` manual → jalankan app | File dikarantina `.corrupt-*`, state pulih dari `.bak` |
| 4 | Exit via tray | Klik Exit pada tray icon | Proses benar-benar mati (cek Task Manager), tanpa zombie |
| 5 | Auto-update toggle | Settings → matikan "Automatic Update Checks" → restart | Switch tetap OFF; tidak ada request ke `api.github.com` |
| 6 | Dialog update | Set `last_update_check_time = 0` + buat release dummy lebih tinggi, atau tunggu rilis asli | Dialog tampil; *Remind Me Later* & *Skip This Version* berfungsi |
| 7 | Offline first-run | Putus internet, hapus folder `%APPDATA%\WinTokenMon`, jalankan app | Tidak crash; sprite fallback egg; log mencatat cooldown download |
| 8 | Autostart | Toggle "Launch on Windows Startup" | Registry HKCU Run key dibuat/dihapus sesuai toggle |
| 9 | Uninstall bersih | Jalankan uninstaller Inno Setup | Folder instalasi bersih; `%APPDATA%` (save game) dipertahankan |

## 2. Merge & Tag

```powershell
# 1. Pastikan preview hijau (ruff + pytest)
ruff check .
pytest -q

# 2. Merge preview -> main (no-ff agar riwayat fitur terlihat)
git checkout main
git pull origin main
git merge --no-ff preview -m "release: v1.0.0 production GA"
git push origin main

# 3. Tag memicu .github/workflows/release.yml
git tag -a v1.0.0 -m "WinTokenMon v1.0.0 — Production GA"
git push origin v1.0.0
```

CI akan otomatis: lint → pytest → PyInstaller + Inno Setup → SHA256 checksums → publish GitHub Release dengan artefak:
- `dist/WinTokenMon-v1.0.0-Portable.exe`
- `dist/WinTokenMon-Setup-v1.0.0.exe`
- `dist/*.exe.sha256`

## 3. Winget Submission

```powershell
# Ambil hash aktual dari file .sha256 hasil CI (atau hitung lokal):
python scripts/generate_winget_manifest.py --version 1.0.0 `
    --sha256 <HEX_DARI_RELEASE>

# Commit manifest lalu submit PR ke microsoft/winget-pkgs:
# manifests/j/JustALearner101/WinTokenMon/1.0.0/
```

Verifikasi setelah merge PR winget:

```powershell
winget search WinTokenMon
winget install JustALearner101.WinTokenMon
```

## 4. Pasca-Rilis

- [ ] Update badge/download link di README jika perlu
- [ ] Arsipkan issue/PR template feedback untuk bug v1.0.0
- [ ] Jadwalkan patch v1.0.x bila ditemukan regression kritis

---
*Checklist ini melengkapi Fasa 1–5 di `v1.0.0-production-release-and-winget.md` yang sudah Implemented.*
