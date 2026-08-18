# 🎮 WinTokenMon — Progression Curves & Token Economics

> **Language / Bahasa**: [**English**](BALANCE.md) | [**Bahasa Indonesia**](id/BALANCE.id.md)

This document outlines the mathematical progression balance, egg incubation requirements, shop prices, and item mechanics in **WinTokenMon**.

---

## 1. Egg Incubation & Hatching Thresholds

Different egg tiers have different incubation requirements (measured in tokens burned during coding):

| Egg Tier | Cost (Spendable Tokens) | Hatch Threshold (Tokens Burned) | Candidate Species Pool |
| :--- | :--- | :--- | :--- |
| **Standard Starter Egg** | Free (Starting egg / on reset) | **2,500,000** (2.5M) | All Gen 1–5 Starters (Bulbasaur, Charmander, Squirtle, Totodile, Cyndaquil, Treecko, Piplup, Snivy, etc.) |
| **Uncommon Egg** | **50,000,000** (50M) | **6,000,000** (6.0M) | Guaranteed Uncommon, Rare, or Legendary species |
| **Rare Egg** | **200,000,000** (200M) | **15,000,000** (15.0M) | Guaranteed Rare or Legendary species (Dratini, Bagon, Larvitar, Riolu, Beldum, Ralts, etc.) |
| **Legendary Egg** | **600,000,000** (600M) | **35,000,000** (35.0M) | Guaranteed Legendary species (Mewtwo, Rayquaza, Dialga, Palkia, Reshiram, Zekrom, etc.) |

---

## 2. Evolution & Graduation Lifecycles

When a Pokémon hatches, it progresses through its evolutionary forms by burning additional tokens.

### A. Graduation Lifetime Totals

| Rarity | Lifetime Total Tokens for Graduation | Example Evolution Lines |
| :--- | :--- | :--- |
| **Common** | **250,000,000** (250M) | Caterpie $\to$ Metapod $\to$ Butterfree, Pidgey $\to$ Pidgeotto $\to$ Pidgeot |
| **Uncommon** | **750,000,000** (750M) | Bulbasaur $\to$ Ivysaur $\to$ Venusaur, Charmander $\to$ Charmeleon $\to$ Charizard |
| **Rare** | **2,000,000,000** (2.0B) | Dratini $\to$ Dragonair $\to$ Dragonite, Bagon $\to$ Shelgon $\to$ Salamence |
| **Legendary** | **5,000,000,000** (5.0B) | Mewtwo, Rayquaza, Dialga, Palkia |

### B. Evolutionary Stage Progression Formula

To make early forms feel accessible and late forms feel like prestigious accomplishments, thresholds scale with an arithmetic series:

$$\text{Stage Threshold} = \text{round}\left( \text{Graduation Total}(\text{Rarity}) \times \frac{i}{k(k+1)/2} \right)$$

Where:
- $k$ = Total evolutionary forms in chain (e.g. 3 for Charmander $\to$ Charmeleon $\to$ Charizard)
- $i$ = Current stage index (1 for Stage 1, 2 for Stage 2, etc.)

#### Example: 3-Stage Uncommon Line (Bulbasaur $\to$ Ivysaur $\to$ Venusaur)
- Total = 750M, Denominator = $3 \times 4 / 2 = 6$
- **Form 1 (Bulbasaur $\to$ Ivysaur)**: $750\text{M} \times 1/6 =$ **125,000,000** (125M) tokens
- **Form 2 (Ivysaur $\to$ Venusaur)**: $750\text{M} \times 2/6 =$ **250,000,000** (250M) tokens
- **Form 3 (Venusaur $\to$ Graduation)**: $750\text{M} \times 3/6 =$ **375,000,000** (375M) tokens
- *Sum = 750M tokens $\to$ Graduates into Pokédex and awards 1 Rare Candy!*

---

## 3. Shop & Item Economy

Every 1 AI token burned awards 1 spendable token into your bag.

| Item | Price | Effect |
| :--- | :--- | :--- |
| **🍬 Rare Candy** | **25,000,000** (25M) | Grants **+100M EXP** immediately to your active companion. *(Also awarded free upon every graduation!)* |
| **🌿 Nature Mint** | **50,000,000** (50M) | Re-rolls your active Pokémon's nature (Adamant, Modest, Jolly, Timid, etc.). |
| **✨ Shiny Charm** | **500,000,000** (500M) | **Permanent passive upgrade**. Increases Shiny egg hatching probability from **1 in 129** to **1 in 40**! |

---

## 4. Shiny Mechanics

- Base Shiny Probability: **1 in 129** (~0.77% chance per hatch).
- Boosted Shiny Probability (with Shiny Charm): **1 in 40** (2.5% chance per hatch).
- Shiny status is preserved through all evolutionary stages and permanently recorded with gold badge framing in your Pokédex!
