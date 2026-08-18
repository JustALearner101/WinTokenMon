# 🎮 WinTokenMon — Kurva Progresi & Ekonomi Token

> **Language / Bahasa**: [**English**](../BALANCE.md) | [**Bahasa Indonesia**](BALANCE.id.md)

Dokumen ini menguraikan keseimbangan progresi matematika, syarat penetasan telur, harga toko item, dan mekanisme game di **WinTokenMon**.

---

## 1. Penetasan Telur & Ambang Batas Inkubasi

Setiap tier telur memiliki syarat inkubasi berbeda (dihitung dari akumulasi token yang dibakar saat koding):

| Tier Telur | Harga (Token Belanja) | Syarat Menetas (Token Dibakar) | Daftar Calon Spesies |
| :--- | :--- | :--- | :--- |
| **Standard Starter Egg** | Gratis (Telur awal / saat reset) | **2,500,000** (2.5M) | Semua Starter Gen 1–5 (Bulbasaur, Charmander, Squirtle, Totodile, Cyndaquil, Treecko, Piplup, Snivy, dll.) |
| **Uncommon Egg** | **50,000,000** (50M) | **6,000,000** (6.0M) | Dijamin spesies Uncommon, Rare, atau Legendary |
| **Rare Egg** | **200,000,000** (200M) | **15,000,000** (15.0M) | Dijamin spesies Rare atau Legendary (Dratini, Bagon, Larvitar, Riolu, Beldum, Ralts, dll.) |
| **Legendary Egg** | **600,000,000** (600M) | **35,000,000** (35.0M) | Dijamin spesies Legendary (Mewtwo, Rayquaza, Dialga, Palkia, Reshiram, Zekrom, dll.) |

---

## 2. Siklus Hidup Evolusi & Kelulusan

Setelah menetas, Pokémon membutuhkan token tambahan untuk berevolusi melalui stage-stage berikutnya hingga lulus (*graduate*).

### Total Token Kelulusan Berdasarkan Kelangkaan:
- **Common**: $250\text{M}$ token
- **Uncommon**: $750\text{M}$ token
- **Rare**: $2\text{B}$ token
- **Legendary**: $5\text{B}$ token

### Formula Progresi Aritmatika:
Untuk garis evolusi dengan total $k$ tahap dan tahap aktif ke-$i$ ($1$-indexed):
$$\text{Ambang Batas Stage}(i) = \text{round}\left( \text{Total Kelulusan}(\text{Kelangkaan}) \times \frac{i}{\frac{k(k+1)}{2}} \right)$$

#### Contoh: Garis Starter 3 Tahap (Bulbasaur $\to$ Ivysaur $\to$ Venusaur) [Uncommon, Total = 750M]:
- **Stage 1 (Bulbasaur)**: $750\text{M} \times \frac{1}{6} = \mathbf{125\text{M}}\text{ token}$ $\to$ Berevolusi ke Ivysaur
- **Stage 2 (Ivysaur)**: $750\text{M} \times \frac{2}{6} = \mathbf{250\text{M}}\text{ token}$ $\to$ Berevolusi ke Venusaur
- **Stage 3 (Venusaur)**: $750\text{M} \times \frac{3}{6} = \mathbf{375\text{M}}\text{ token}$ $\to$ **Lulus (Senior Trainer)**

---

## 3. Toko Item & Mekanisme Penggunaan

Token belanja diperoleh dengan rasio **1:1** untuk setiap token AI lokal yang dibakar.

| Item | Harga | Efek & Manfaat |
| :--- | :--- | :--- |
| **🍬 Rare Candy** | **25,000,000** (25M) | Langsung memberikan **+100,000,000 (+100M)** EXP instan ke Pokémon aktif, mempercepat evolusi secara drastis. |
| **🌿 Nature Mint** | **50,000,000** (50M) | Mengacak ulang sifat (*Nature*) Pokémon aktif ke salah satu dari 25 varian canonical Pokémon. |
| **✨ Shiny Charm** | **500,000,000** (500M) | Meningkatkan peluang penetasan varian Shiny secara permanen dari **1 / 129 ($\approx 0.77\%$)** menjadi **1 / 40 ($2.50\%$)**. |

---

## 4. Peluang Varian Shiny

- **Peluang Dasar**: `1 / 129` ($\approx 0.77\%$).
- **Dengan Shiny Charm**: `1 / 40` ($2.5\%$).
- Varian Shiny memiliki palet warna alternatif langka dan memunculkan animasi bintang berkilau (*sparkles*) saat berinteraksi.
