"""
PokéAPI client and offline cache for WinTokenMon
"""

import os
import shutil
import sys
import urllib.error
import urllib.request

# Local directory for cached assets and species data
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "WinTokenMon")
SPRITES_DIR = os.path.join(DATA_DIR, "sprites")
CACHE_FILE = os.path.join(DATA_DIR, "pokedex_cache.json")

os.makedirs(SPRITES_DIR, exist_ok=True)

# Bundled assets directory (PyInstaller _MEIPASS or source tree)
_BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUNDLED_SPRITES_DIR = os.path.join(_BASE_DIR, "assets", "sprites")

# Curated popular starter evolution lines (Species ID -> [Stage 1, Stage 2, Stage 3, ...])
# With Gen 1 - Gen 5 starters and fan-favorites
CURATED_EVOLUTION_LINES = [
    {
        "name": "Bulbasaur",
        "chain": [1, 2, 3],
        "names": ["Bulbasaur", "Ivysaur", "Venusaur"],
        "rarity": "uncommon",
    },
    {
        "name": "Charmander",
        "chain": [4, 5, 6],
        "names": ["Charmander", "Charmeleon", "Charizard"],
        "rarity": "uncommon",
    },
    {
        "name": "Squirtle",
        "chain": [7, 8, 9],
        "names": ["Squirtle", "Wartortle", "Blastoise"],
        "rarity": "uncommon",
    },
    {
        "name": "Caterpie",
        "chain": [10, 11, 12],
        "names": ["Caterpie", "Metapod", "Butterfree"],
        "rarity": "common",
    },
    {
        "name": "Weedle",
        "chain": [13, 14, 15],
        "names": ["Weedle", "Kakuna", "Beedrill"],
        "rarity": "common",
    },
    {
        "name": "Pidgey",
        "chain": [16, 17, 18],
        "names": ["Pidgey", "Pidgeotto", "Pidgeot"],
        "rarity": "common",
    },
    {
        "name": "Pikachu",
        "chain": [172, 25, 26],
        "names": ["Pichu", "Pikachu", "Raichu"],
        "rarity": "uncommon",
    },
    {
        "name": "Eevee",
        "chain": [133, 134, 135, 136, 196, 197, 470, 471],
        "names": [
            "Eevee",
            "Vaporeon",
            "Jolteon",
            "Flareon",
            "Espeon",
            "Umbreon",
            "Leafeon",
            "Glaceon",
        ],
        "rarity": "rare",
    },
    {
        "name": "Dratini",
        "chain": [147, 148, 149],
        "names": ["Dratini", "Dragonair", "Dragonite"],
        "rarity": "rare",
    },
    {"name": "Mewtwo", "chain": [150], "names": ["Mewtwo"], "rarity": "legendary"},
    {"name": "Mew", "chain": [151], "names": ["Mew"], "rarity": "legendary"},
    {
        "name": "Chikorita",
        "chain": [152, 153, 154],
        "names": ["Chikorita", "Bayleef", "Meganium"],
        "rarity": "uncommon",
    },
    {
        "name": "Cyndaquil",
        "chain": [155, 156, 157],
        "names": ["Cyndaquil", "Quilava", "Typhlosion"],
        "rarity": "uncommon",
    },
    {
        "name": "Totodile",
        "chain": [158, 159, 160],
        "names": ["Totodile", "Croconaw", "Feraligatr"],
        "rarity": "uncommon",
    },
    {
        "name": "Larvitar",
        "chain": [246, 247, 248],
        "names": ["Larvitar", "Pupitar", "Tyranitar"],
        "rarity": "rare",
    },
    {"name": "Lugia", "chain": [249], "names": ["Lugia"], "rarity": "legendary"},
    {"name": "Ho-Oh", "chain": [250], "names": ["Ho-Oh"], "rarity": "legendary"},
    {
        "name": "Treecko",
        "chain": [252, 253, 254],
        "names": ["Treecko", "Grovyle", "Sceptile"],
        "rarity": "uncommon",
    },
    {
        "name": "Torchic",
        "chain": [255, 256, 257],
        "names": ["Torchic", "Combusken", "Blaziken"],
        "rarity": "uncommon",
    },
    {
        "name": "Mudkip",
        "chain": [258, 259, 260],
        "names": ["Mudkip", "Marshtomp", "Swampert"],
        "rarity": "uncommon",
    },
    {
        "name": "Ralts",
        "chain": [280, 281, 282],
        "names": ["Ralts", "Kirlia", "Gardevoir"],
        "rarity": "rare",
    },
    {
        "name": "Bagon",
        "chain": [371, 372, 373],
        "names": ["Bagon", "Shelgon", "Salamence"],
        "rarity": "rare",
    },
    {
        "name": "Beldum",
        "chain": [374, 375, 376],
        "names": ["Beldum", "Metang", "Metagross"],
        "rarity": "rare",
    },
    {"name": "Rayquaza", "chain": [384], "names": ["Rayquaza"], "rarity": "legendary"},
    {
        "name": "Turtwig",
        "chain": [387, 388, 389],
        "names": ["Turtwig", "Grotle", "Torterra"],
        "rarity": "uncommon",
    },
    {
        "name": "Chimchar",
        "chain": [390, 391, 392],
        "names": ["Chimchar", "Monferno", "Infernape"],
        "rarity": "uncommon",
    },
    {
        "name": "Piplup",
        "chain": [393, 394, 395],
        "names": ["Piplup", "Prinplup", "Empoleon"],
        "rarity": "uncommon",
    },
    {
        "name": "Gible",
        "chain": [443, 444, 445],
        "names": ["Gible", "Gabite", "Garchomp"],
        "rarity": "rare",
    },
    {"name": "Riolu", "chain": [447, 448], "names": ["Riolu", "Lucario"], "rarity": "rare"},
    {"name": "Dialga", "chain": [483], "names": ["Dialga"], "rarity": "legendary"},
    {"name": "Palkia", "chain": [484], "names": ["Palkia"], "rarity": "legendary"},
    {
        "name": "Snivy",
        "chain": [495, 496, 497],
        "names": ["Snivy", "Servine", "Serperior"],
        "rarity": "uncommon",
    },
    {
        "name": "Tepig",
        "chain": [498, 499, 500],
        "names": ["Tepig", "Pignite", "Emboar"],
        "rarity": "uncommon",
    },
    {
        "name": "Oshawott",
        "chain": [501, 502, 503],
        "names": ["Oshawott", "Dewott", "Samurott"],
        "rarity": "uncommon",
    },
    {"name": "Zorua", "chain": [570, 571], "names": ["Zorua", "Zoroark"], "rarity": "rare"},
    {
        "name": "Axew",
        "chain": [610, 611, 612],
        "names": ["Axew", "Fraxure", "Haxorus"],
        "rarity": "rare",
    },
    {
        "name": "Deino",
        "chain": [633, 634, 635],
        "names": ["Deino", "Zweilous", "Hydreigon"],
        "rarity": "rare",
    },
    {"name": "Reshiram", "chain": [643], "names": ["Reshiram"], "rarity": "legendary"},
    {"name": "Zekrom", "chain": [644], "names": ["Zekrom"], "rarity": "legendary"},
    # Gen 6 (Kalos) Starters
    {
        "name": "Chespin",
        "chain": [650, 651, 652],
        "names": ["Chespin", "Quilladin", "Chesnaught"],
        "rarity": "uncommon",
    },
    {
        "name": "Fennekin",
        "chain": [653, 654, 655],
        "names": ["Fennekin", "Braixen", "Delphox"],
        "rarity": "uncommon",
    },
    {
        "name": "Froakie",
        "chain": [656, 657, 658],
        "names": ["Froakie", "Frogadier", "Greninja"],
        "rarity": "uncommon",
    },
    # Gen 7 (Alola) Starters
    {
        "name": "Rowlet",
        "chain": [722, 723, 724],
        "names": ["Rowlet", "Dartrix", "Decidueye"],
        "rarity": "uncommon",
    },
    {
        "name": "Litten",
        "chain": [725, 726, 727],
        "names": ["Litten", "Torracat", "Incineroar"],
        "rarity": "uncommon",
    },
    {
        "name": "Popplio",
        "chain": [728, 729, 730],
        "names": ["Popplio", "Brionne", "Primarina"],
        "rarity": "uncommon",
    },
    # Gen 8 (Galar) Starters
    {
        "name": "Grookey",
        "chain": [810, 811, 812],
        "names": ["Grookey", "Thwackey", "Rillaboom"],
        "rarity": "uncommon",
    },
    {
        "name": "Scorbunny",
        "chain": [813, 814, 815],
        "names": ["Scorbunny", "Raboot", "Cinderace"],
        "rarity": "uncommon",
    },
    {
        "name": "Sobble",
        "chain": [816, 817, 818],
        "names": ["Sobble", "Drizzile", "Inteleon"],
        "rarity": "uncommon",
    },
    # Gen 9 (Paldea) Starters
    {
        "name": "Sprigatito",
        "chain": [906, 907, 908],
        "names": ["Sprigatito", "Floragato", "Meowscarada"],
        "rarity": "uncommon",
    },
    {
        "name": "Fuecoco",
        "chain": [909, 910, 911],
        "names": ["Fuecoco", "Crocalor", "Skeledirge"],
        "rarity": "uncommon",
    },
    {
        "name": "Quaxly",
        "chain": [912, 913, 914],
        "names": ["Quaxly", "Quaxwell", "Quaquaval"],
        "rarity": "uncommon",
    },
]

# Precomputed O(1) index: Species ID -> Evolution Line dictionary
SPECIES_INDEX: dict[int, dict] = {
    sid: line for line in CURATED_EVOLUTION_LINES for sid in line["chain"]
}

# Canonical starter generation grouping for onboarding selection
STARTER_GENERATIONS = {
    "Gen 1 (Kanto)": [1, 4, 7],  # Bulbasaur, Charmander, Squirtle
    "Gen 2 (Johto)": [152, 155, 158],  # Chikorita, Cyndaquil, Totodile
    "Gen 3 (Hoenn)": [252, 255, 258],  # Treecko, Torchic, Mudkip
    "Gen 4 (Sinnoh)": [387, 390, 393],  # Turtwig, Chimchar, Piplup
    "Gen 5 (Unova)": [495, 498, 501],  # Snivy, Tepig, Oshawott
    "Gen 6 (Kalos)": [650, 653, 656],  # Chespin, Fennekin, Froakie
    "Gen 7 (Alola)": [722, 725, 728],  # Rowlet, Litten, Popplio
    "Gen 8 (Galar)": [810, 813, 816],  # Grookey, Scorbunny, Sobble
    "Gen 9 (Paldea)": [906, 909, 912],  # Sprigatito, Fuecoco, Quaxly
    "Special ★": [25, 133, 447],  # Pikachu, Eevee, Riolu
}

# Elemental type tagging for starter cards
POKEMON_TYPES = {
    1: "🌿 Grass / Poison",
    4: "🔥 Fire",
    7: "💧 Water",
    25: "⚡ Electric",
    133: "⚪ Normal",
    152: "🌿 Grass",
    155: "🔥 Fire",
    158: "💧 Water",
    252: "🌿 Grass",
    255: "🔥 Fire",
    258: "💧 Water",
    387: "🌿 Grass",
    390: "🔥 Fire",
    393: "💧 Water",
    447: "🥋 Fighting",
    495: "🌿 Grass",
    498: "🔥 Fire",
    501: "💧 Water",
    650: "🌿 Grass",
    653: "🔥 Fire",
    656: "💧 Water",
    722: "🌿 Grass / Flying",
    725: "🔥 Fire",
    728: "💧 Water",
    810: "🌿 Grass",
    813: "🔥 Fire",
    816: "💧 Water",
    906: "🌿 Grass",
    909: "🔥 Fire",
    912: "💧 Water",
}


def get_sprite_path(species_id: int, is_shiny: bool = False) -> str:
    """Returns local path to animated GIF or PNG sprite, resolving from cache, bundle, or downloading."""
    shiny_suffix = "_shiny" if is_shiny else ""
    local_gif = os.path.join(SPRITES_DIR, f"{species_id}{shiny_suffix}.gif")
    local_png = os.path.join(SPRITES_DIR, f"{species_id}{shiny_suffix}.png")

    # 1. Check local writable cache in APPDATA
    if os.path.exists(local_gif) and os.path.getsize(local_gif) > 0:
        return local_gif
    if os.path.exists(local_png) and os.path.getsize(local_png) > 0:
        return local_png

    # 2. Check bundled assets directory
    bundled_gif = os.path.join(BUNDLED_SPRITES_DIR, f"{species_id}{shiny_suffix}.gif")
    bundled_png = os.path.join(BUNDLED_SPRITES_DIR, f"{species_id}{shiny_suffix}.png")

    if os.path.exists(bundled_gif) and os.path.getsize(bundled_gif) > 0:
        try:
            shutil.copy2(bundled_gif, local_gif)
            return local_gif
        except Exception:
            return bundled_gif

    if os.path.exists(bundled_png) and os.path.getsize(bundled_png) > 0:
        try:
            shutil.copy2(bundled_png, local_png)
            return local_png
        except Exception:
            return bundled_png

    # 3. Fallback: Try downloading Showdown animated GIF from network
    gif_url = (
        f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/shiny/{species_id}.gif"
        if is_shiny
        else f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/{species_id}.gif"
    )
    png_url = (
        f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{species_id}.png"
        if is_shiny
        else f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{species_id}.png"
    )

    headers = {"User-Agent": "WinTokenMon/1.0"}
    try:
        req = urllib.request.Request(gif_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response, open(local_gif, "wb") as out_file:
            out_file.write(response.read())
        return local_gif
    except Exception:
        pass

    # 4. Fallback: Download PNG sprite
    try:
        req = urllib.request.Request(png_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response, open(local_png, "wb") as out_file:
            out_file.write(response.read())
        return local_png
    except Exception:
        pass

    return ""
