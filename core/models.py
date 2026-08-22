"""
Data models and progression balance for WinTokenMon Windows
"""

import time
from dataclasses import dataclass, field
from enum import Enum


class Rarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"


class PokemonNature(str, Enum):
    HARDY = "Hardy"
    LONELY = "Lonely"
    BRAVE = "Brave"
    ADAMANT = "Adamant"
    NAUGHTY = "Naughty"
    BOLD = "Bold"
    DOCILE = "Docile"
    RELAXED = "Relaxed"
    IMPISH = "Impish"
    LAX = "Lax"
    TIMID = "Timid"
    HASTY = "Hasty"
    SERIOUS = "Serious"
    JOLLY = "Jolly"
    NAIVE = "Naive"
    MODEST = "Modest"
    MILD = "Mild"
    QUIET = "Quiet"
    BASHFUL = "Bashful"
    RASH = "Rash"
    CALM = "Calm"
    GENTLE = "Gentle"
    SASSY = "Sassy"
    CAREFUL = "Careful"
    QUIRKY = "Quirky"


class ItemKind(str, Enum):
    RARE_CANDY = "rareCandy"
    ORAN_BERRY = "oranBerry"
    MINT = "mint"
    SHINY_CHARM = "shinyCharm"

    @property
    def title(self) -> str:
        names = {
            ItemKind.RARE_CANDY: "Rare Candy",
            ItemKind.ORAN_BERRY: "Oran Berry",
            ItemKind.MINT: "Nature Mint",
            ItemKind.SHINY_CHARM: "Shiny Charm",
        }
        return names.get(self, self.value)

    @property
    def description(self) -> str:
        descs = {
            ItemKind.RARE_CANDY: "Grants 100M bonus token EXP immediately and +15 Friendship.",
            ItemKind.ORAN_BERRY: "A sweet berry that grants 10M token EXP and +10 Friendship.",
            ItemKind.MINT: "Re-rolls your active Pokémon's nature.",
            ItemKind.SHINY_CHARM: "Permanently boosts shiny egg hatch probability (1/129 → 1/40).",
        }
        return descs.get(self, "")

    @property
    def price_tokens(self) -> int:
        prices = {
            ItemKind.RARE_CANDY: 25_000_000,  # 25M tokens
            ItemKind.ORAN_BERRY: 5_000_000,  # 5M tokens
            ItemKind.MINT: 50_000_000,  # 50M tokens
            ItemKind.SHINY_CHARM: 500_000_000,  # 500M tokens
        }
        return prices.get(self, 0)

    @property
    def emoji(self) -> str:
        emojis = {
            ItemKind.RARE_CANDY: "🍬",
            ItemKind.ORAN_BERRY: "🫐",
            ItemKind.MINT: "🌿",
            ItemKind.SHINY_CHARM: "✨",
        }
        return emojis.get(self, "📦")


class EggTier(str, Enum):
    STANDARD = "standard"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"

    @property
    def price_tokens(self) -> int:
        prices = {
            EggTier.STANDARD: 0,
            EggTier.UNCOMMON: 50_000_000,  # 50M tokens
            EggTier.RARE: 200_000_000,  # 200M tokens
            EggTier.LEGENDARY: 600_000_000,  # 600M tokens
        }
        return prices.get(self, 0)

    @property
    def hatch_threshold(self) -> int:
        """Dynamic hatch threshold in tokens based on egg tier."""
        thresholds = {
            EggTier.STANDARD: 2_500_000,  # 2.5M tokens (Fast early reward for starters)
            EggTier.UNCOMMON: 6_000_000,  # 6.0M tokens
            EggTier.RARE: 15_000_000,  # 15.0M tokens
            EggTier.LEGENDARY: 35_000_000,  # 35.0M tokens
        }
        return thresholds.get(self, 2_500_000)


class PokemonBalance:
    @staticmethod
    def graduation_total(rarity: Rarity) -> int:
        """Total lifetime token requirement for a companion to reach graduation."""
        totals = {
            Rarity.COMMON: 250_000_000,  # 250M tokens
            Rarity.UNCOMMON: 750_000_000,  # 750M tokens
            Rarity.RARE: 2_000_000_000,  # 2.0B tokens
            Rarity.LEGENDARY: 5_000_000_000,  # 5.0B tokens
        }
        return totals.get(rarity, 500_000_000)

    @staticmethod
    def phase_threshold(rarity: Rarity, total_forms: int, stage_index: int) -> int:
        """Calculates arithmetic progression threshold for each evolutionary stage."""
        k = max(1, total_forms)
        i = stage_index + 1
        total = float(PokemonBalance.graduation_total(rarity))
        denom = float(k * (k + 1)) / 2.0
        return int(round(total * float(i) / denom))


@dataclass
class ActivePokemon:
    species_id: int
    species_name: str
    stage_index: int  # 0-indexed (e.g. 0 = Bulbasaur, 1 = Ivysaur, 2 = Venusaur)
    total_forms: int
    used_at_stage: int
    rarity: Rarity
    nature: PokemonNature
    is_shiny: bool
    hatched_at: float = field(default_factory=time.time)
    evolution_chain_ids: list[int] = field(default_factory=list)
    friendship: int = 50  # 0 to 100
    last_pet_date: str = ""
    daily_pet_count: int = 0
    treats_eaten_today: int = 0
    last_treat_date: str = ""


class BadgeTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

    @property
    def color_hex(self) -> str:
        colors = {
            BadgeTier.BRONZE: "#CD7F32",
            BadgeTier.SILVER: "#C0C0C0",
            BadgeTier.GOLD: "#F1C40F",
            BadgeTier.PLATINUM: "#A0B2C6",
        }
        return colors.get(self, "#C0C0C0")

    @property
    def title(self) -> str:
        return self.value.capitalize()


@dataclass
class AchievementDef:
    id: str
    title: str
    description: str
    tier: BadgeTier
    icon_emoji: str
    reward_tokens: int = 0
    reward_item: ItemKind | None = None
    reward_item_count: int = 0
    category: str = "General"


ACHIEVEMENT_DEFINITIONS: dict[str, AchievementDef] = {
    "first_hatch": AchievementDef(
        id="first_hatch",
        title="First Hatch",
        description="Hatch your very first Pokémon companion from an egg.",
        tier=BadgeTier.BRONZE,
        icon_emoji="🐣",
        reward_tokens=10_000_000,
        category="Milestone",
    ),
    "night_owl": AchievementDef(
        id="night_owl",
        title="Night Owl Coder",
        description="Burn >100k tokens between 00:00 and 05:00 local time.",
        tier=BadgeTier.SILVER,
        icon_emoji="🦉",
        reward_tokens=5_000_000,
        category="Habit",
    ),
    "overclock": AchievementDef(
        id="overclock",
        title="Token Overclock",
        description="Burn >1M tokens in a 1-hour rolling window.",
        tier=BadgeTier.SILVER,
        icon_emoji="⚡",
        reward_item=ItemKind.RARE_CANDY,
        reward_item_count=1,
        category="Speed",
    ),
    "multi_tool": AchievementDef(
        id="multi_tool",
        title="Multi-Tool Wizard",
        description="Burn tokens across 3+ different AI tools in a single day.",
        tier=BadgeTier.SILVER,
        icon_emoji="🧙‍♂️",
        reward_item=ItemKind.MINT,
        reward_item_count=2,
        category="Versatility",
    ),
    "100m_burn_club": AchievementDef(
        id="100m_burn_club",
        title="100M Burn Club",
        description="Accumulate 100M total lifetime AI tokens burned.",
        tier=BadgeTier.GOLD,
        icon_emoji="💯",
        reward_tokens=25_000_000,
        category="Endurance",
    ),
    "shiny_hunter": AchievementDef(
        id="shiny_hunter",
        title="Shiny Hunter",
        description="Hatch a rare shiny Pokémon variant.",
        tier=BadgeTier.GOLD,
        icon_emoji="✨",
        reward_item=ItemKind.SHINY_CHARM,
        reward_item_count=1,
        category="Luck",
    ),
    "senior_professor": AchievementDef(
        id="senior_professor",
        title="Senior Professor",
        description="Graduate 5 fully-evolved Pokémon to Senior status.",
        tier=BadgeTier.GOLD,
        icon_emoji="🎓",
        reward_item=ItemKind.RARE_CANDY,
        reward_item_count=5,
        category="Mastery",
    ),
    "egg_hoarder": AchievementDef(
        id="egg_hoarder",
        title="Egg Hoarder",
        description="Adopt Uncommon, Rare, and Legendary egg tiers from the shop.",
        tier=BadgeTier.PLATINUM,
        icon_emoji="🥚",
        reward_tokens=50_000_000,
        category="Economy",
    ),
}
