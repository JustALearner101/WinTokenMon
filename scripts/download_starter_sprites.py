"""
Download all curated starter Pokémon sprites into assets/sprites/ for pre-bundling.
Ensures WinTokenMon has instant, offline-ready starter previews on first launch.
"""

import os
import sys
import urllib.error
import urllib.request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_SPRITES_DIR = os.path.join(ROOT_DIR, "assets", "sprites")
os.makedirs(ASSETS_SPRITES_DIR, exist_ok=True)

# Curated starter species IDs across Gen 1 to Gen 9 + Special starters
STARTER_SPECIES_IDS = [
    # Gen 1 (Kanto)
    1, 4, 7,
    # Gen 2 (Johto)
    152, 155, 158,
    # Gen 3 (Hoenn)
    252, 255, 258,
    # Gen 4 (Sinnoh)
    387, 390, 393,
    # Gen 5 (Unova)
    495, 498, 501,
    # Gen 6 (Kalos)
    650, 653, 656,
    # Gen 7 (Alola)
    722, 725, 728,
    # Gen 8 (Galar)
    810, 813, 816,
    # Gen 9 (Paldea)
    906, 909, 912,
    # Special ★ (Pikachu, Eevee, Riolu)
    25, 133, 447,
]


def download_sprite(species_id: int) -> bool:
    local_gif = os.path.join(ASSETS_SPRITES_DIR, f"{species_id}.gif")
    local_png = os.path.join(ASSETS_SPRITES_DIR, f"{species_id}.png")

    if os.path.exists(local_gif) and os.path.getsize(local_gif) > 0:
        print(f"  [✓] #{species_id:03d} already cached ({os.path.basename(local_gif)})")
        return True
    if os.path.exists(local_png) and os.path.getsize(local_png) > 0:
        print(f"  [✓] #{species_id:03d} already cached ({os.path.basename(local_png)})")
        return True

    headers = {"User-Agent": "WinTokenMon-AssetFetcher/1.0"}

    # 1. Try Showdown animated GIF
    gif_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/{species_id}.gif"
    try:
        req = urllib.request.Request(gif_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            if len(data) > 0:
                with open(local_gif, "wb") as f:
                    f.write(data)
                print(f"  [+] #{species_id:03d} downloaded GIF ({len(data) / 1024:.1f} KB)")
                return True
    except Exception:
        pass

    # 2. Fallback to PNG sprite
    png_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{species_id}.png"
    try:
        req = urllib.request.Request(png_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            if len(data) > 0:
                with open(local_png, "wb") as f:
                    f.write(data)
                print(f"  [+] #{species_id:03d} downloaded PNG fallback ({len(data) / 1024:.1f} KB)")
                return True
    except Exception as e:
        print(f"  Failed to download #{species_id:03d}: {e}")
        return False

    return False


def main():
    print("==================================================")
    print("[*] Downloading Starter Pokémon Sprites for Bundling")
    print(f"[*] Target Directory: {ASSETS_SPRITES_DIR}")
    print(f"[*] Total Starters: {len(STARTER_SPECIES_IDS)}")
    print("==================================================")

    success_count = 0
    for sid in STARTER_SPECIES_IDS:
        if download_sprite(sid):
            success_count += 1

    print("-" * 50)
    print(f"[*] Completed: {success_count}/{len(STARTER_SPECIES_IDS)} sprites ready.")
    if success_count < len(STARTER_SPECIES_IDS):
        sys.exit(1)


if __name__ == "__main__":
    main()
