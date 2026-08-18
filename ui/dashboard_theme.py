"""
Dynamic Elemental Type Themes, Palettes, and Bio Details for WinTokenMon Dashboard
"""

from core.models import PokemonNature
from core.poke_api import POKEMON_TYPES

# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC ELEMENTAL TYPE THEMES & PALETTES
# ─────────────────────────────────────────────────────────────────────────────
TYPE_THEMES = {
    "grass": {
        "primary": "#2ECC71",
        "secondary": "#27AE60",
        "card_bg": "#14261C",
        "border": "#27AE60",
        "badge_bg": "#1E3D2B",
        "badge_text": "#A9DFBF",
        "icon": "🌿",
    },
    "fire": {
        "primary": "#E67E22",
        "secondary": "#D35400",
        "card_bg": "#2B1A13",
        "border": "#D35400",
        "badge_bg": "#442417",
        "badge_text": "#F5CBA7",
        "icon": "🔥",
    },
    "water": {
        "primary": "#3498DB",
        "secondary": "#2980B9",
        "card_bg": "#122232",
        "border": "#2980B9",
        "badge_bg": "#1A354C",
        "badge_text": "#AED6F1",
        "icon": "💧",
    },
    "electric": {
        "primary": "#F1C40F",
        "secondary": "#D4AC0D",
        "card_bg": "#2B2610",
        "border": "#D4AC0D",
        "badge_bg": "#443A14",
        "badge_text": "#F9E79F",
        "icon": "⚡",
    },
    "psychic": {
        "primary": "#AF52DE",
        "secondary": "#8E44AD",
        "card_bg": "#241432",
        "border": "#8E44AD",
        "badge_bg": "#3B1C52",
        "badge_text": "#E8DAEF",
        "icon": "🔮",
    },
    "dragon": {
        "primary": "#9B59B6",
        "secondary": "#705898",
        "card_bg": "#211831",
        "border": "#705898",
        "badge_bg": "#362750",
        "badge_text": "#D7BDE2",
        "icon": "🐉",
    },
    "fighting": {
        "primary": "#E74C3C",
        "secondary": "#C0392B",
        "card_bg": "#2A1515",
        "border": "#C0392B",
        "badge_bg": "#431F1F",
        "badge_text": "#FADBD8",
        "icon": "🥋",
    },
    "normal": {
        "primary": "#89B4FA",
        "secondary": "#585B70",
        "card_bg": "#181825",
        "border": "#45475A",
        "badge_bg": "#313244",
        "badge_text": "#CDD6F4",
        "icon": "⭐",
    },
}

NATURE_DETAILS = {
    PokemonNature.ADAMANT: ("+10% Attack / Physical", "-10% Sp. Atk", "🗡️ High-velocity raw prompt tokens"),
    PokemonNature.MODEST: ("+10% Sp. Atk / Reasoning", "-10% Attack", "🔮 Precision logic & deep reasoning models"),
    PokemonNature.JOLLY: ("+10% Speed / Cadence", "-10% Sp. Atk", "⚡ Rapid iterative prompt sessions"),
    PokemonNature.TIMID: ("+10% Speed / Fast Stream", "-10% Attack", "💨 High token streaming throughput"),
    PokemonNature.BOLD: ("+10% Defense / Bug Resilience", "-10% Attack", "🛡️ Rock-solid unit tests & refactoring"),
    PokemonNature.CALM: ("+10% Sp. Def / Error Recovery", "-10% Attack", "🧘 Graceful stacktrace debugging"),
    PokemonNature.BRAVE: ("+10% Attack / Heavy Context", "-10% Speed", "⚔️ Massive multi-file codebase contexts"),
    PokemonNature.QUIET: ("+10% Sp. Atk / Deep Thinking", "-10% Speed", "🌙 Complex mathematical & algorithmic focus"),
    PokemonNature.CAREFUL: ("+10% Sp. Def / Clean Arch", "-10% Sp. Atk", "🎯 Strict type-safety and architectural design"),
    PokemonNature.IMPISH: ("+10% Defense / Zero Bugs", "-10% Sp. Atk", "🛡️ Defensive coding & edge-case guards"),
    PokemonNature.HARDY: ("Balanced Stats (All-round)", "No stat penalties", "⚖️ Reliable daily coding companion"),
    PokemonNature.DOCILE: ("Balanced Stats (All-round)", "No stat penalties", "⚖️ Consistent versatile token burn"),
    PokemonNature.SERIOUS: ("Balanced Stats (All-round)", "No stat penalties", "⚖️ Focused high-productivity sprints"),
    PokemonNature.BASHFUL: ("Balanced Stats (All-round)", "No stat penalties", "⚖️ Quiet and steady token accumulation"),
    PokemonNature.QUIRKY: ("Balanced Stats (All-round)", "No stat penalties", "⚖️ Creative multi-agent exploration"),
    PokemonNature.NAIVE: ("+10% Speed / Quick Prototyping", "-10% Sp. Def", "🎨 Experimental fast MVP prototyping"),
    PokemonNature.HASTY: ("+10% Speed / Hot Reloads", "-10% Defense", "🚀 Rapid frontend refresh cycles"),
    PokemonNature.LONELY: ("+10% Attack / Solo Dev", "-10% Defense", "💻 Independent solo project sprints"),
    PokemonNature.NAUGHTY: ("+10% Attack / Experimental", "-10% Sp. Def", "🧪 Frontier bleeding-edge experimentation"),
    PokemonNature.MILD: ("+10% Sp. Atk / Code Craft", "-10% Defense", "✨ Elegant clean syntax & formatting"),
}

POKEMON_LORE = {
    1: "A strange seed was planted on its back at birth. The plant sprouts and grows with this Pokémon as tokens are burned.",
    4: "The flame that burns at the tip of its tail is an indication of its emotions. The flame wavers when coding sessions peak.",
    7: "Shoots water at prey while in the water. Withdraws into its shell when in danger, shielding your build pipeline.",
    25: "When it smashes its cheeks against something, it sparks with electricity. Highly energized by fast token streams.",
    133: "An irregular genetic code allows it to adapt to various environments and develop unique special evolutions.",
    152: "In battle, Chikorita waves its leaf around to keep the foe at bay. A sweet fragrance also wafts from the leaf.",
    155: "It is timid, and always curls itself up in a ball. If attacked, it flares up its back for protection with bursts of flame.",
    158: "It has the habit of biting anything with its developed jaws. Even its Trainer needs to be careful.",
    252: "It quickly scales even vertical walls. It senses humidity with its tail to predict the next developer build.",
    255: "A fire burns inside, so it feels very warm to hug. It launches fireballs of 1,800 degrees F at compiler bugs.",
    258: "The fin on its head acts as highly sensitive radar. Using this fin, it senses water currents and AI tool tokens.",
    387: "Made from soil, the shell on its back hardens when it drinks water. It performs photosynthesis throughout the day.",
    390: "It agilely scales sheer cliffs to live atop mountains. Its tail flame is stoked by gases produced in its belly.",
    393: "Because it is very proud, it hates accepting food from people. Its thick down guards it from the cold.",
    447: "It uses the aura waves it emits to communicate with its Trainer and navigate complex multi-agent workflows.",
    495: "They photosynthesize by bathing their tails in sunlight. When they are not feeling well, their tails droop.",
    498: "It can deftly dodge its foe's attacks while shooting fireballs from its nose. It roasts berries before it eats them.",
    501: "The scalchop on its stomach isn't just used for battle—it can be used like a knife to slice open tough code blocks.",
    650: "The quills on its head are usually soft. When it flexes them, the points become so stiff and sharp that they pierce armor.",
    653: "Eating twigs fills it with energy, and its roomy ears give vent to air hotter than 390 degrees Fahrenheit.",
    656: "It secretes flexible bubbles from its chest and back. The bubbles reduce the damage it would take when facing bugs.",
    722: "This wary Pokémon uses photosynthesis to store up energy during the day, while becoming active at night.",
    725: "While grooming itself, it builds up fur inside its stomach. It sets the fur alight and spews fiery attacks.",
    728: "This Pokémon snorts body fluids from its nose, blowing balloons to smash into its foes with precision.",
    810: "When it beats out a rhythm with its special stick, the sound waves produce revitalizing energy for the codebase.",
    813: "It has special pads on the backs of its feet, and one on its nose. Once it's raring to go, these pads radiate heat.",
    816: "When it gets wet, its skin changes color and this Pokémon becomes invisible as if camouflaged in the IDE.",
    906: "It washes its face regularly to keep it from drying out. The sweet scent from its fur mesmerizes developer bugs.",
    909: "It lies on warm rocks and uses the heat absorbed by its square scales to create fire energy inside its belly.",
    912: "Its feathers secrete a glossy gel that repels water and grime. It slicks the feathers on its head back with gel.",
}


def get_pokemon_element_type(species_id: int) -> str:
    """Resolves elemental type category (grass, fire, water, electric, psychic, dragon, fighting, normal)."""
    type_str = POKEMON_TYPES.get(species_id, "")
    type_lower = type_str.lower()
    if "grass" in type_lower:
        return "grass"
    if "fire" in type_lower:
        return "fire"
    if "water" in type_lower:
        return "water"
    if "electric" in type_lower:
        return "electric"
    if "psychic" in type_lower or "fairy" in type_lower:
        return "psychic"
    if "dragon" in type_lower:
        return "dragon"
    if "fighting" in type_lower:
        return "fighting"
    return "normal"
