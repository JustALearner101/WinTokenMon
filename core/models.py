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

    @property
    def sort_rank(self) -> int:
        ranks = {Rarity.COMMON: 0, Rarity.UNCOMMON: 1, Rarity.RARE: 2, Rarity.LEGENDARY: 3}
        return ranks.get(self, 0)

    @classmethod
    def from_capture_rate(
        cls, capture_rate: int, is_legendary: bool = False, is_mythical: bool = False
    ) -> "Rarity":
        if is_legendary or is_mythical:
            return cls.LEGENDARY
        if capture_rate <= 45:
            return cls.RARE
        if capture_rate <= 120:
            return cls.UNCOMMON
        return cls.COMMON


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
    MINT = "mint"
    SHINY_CHARM = "shinyCharm"

    @property
    def title(self) -> str:
        names = {
            ItemKind.RARE_CANDY: "Rare Candy",
            ItemKind.MINT: "Nature Mint",
            ItemKind.SHINY_CHARM: "Shiny Charm",
        }
        return names.get(self, self.value)

    @property
    def description(self) -> str:
        descs = {
            ItemKind.RARE_CANDY: "Grants 100M bonus token EXP immediately.",
            ItemKind.MINT: "Re-rolls your active Pokémon's nature.",
            ItemKind.SHINY_CHARM: "Permanently boosts shiny egg hatch probability (1/129 → 1/40).",
        }
        return descs.get(self, "")

    @property
    def price_tokens(self) -> int:
        prices = {
            ItemKind.RARE_CANDY: 25_000_000,  # 25M tokens
            ItemKind.MINT: 50_000_000,  # 50M tokens
            ItemKind.SHINY_CHARM: 500_000_000,  # 500M tokens
        }
        return prices.get(self, 0)

    @property
    def emoji(self) -> str:
        emojis = {ItemKind.RARE_CANDY: "🍬", ItemKind.MINT: "🌿", ItemKind.SHINY_CHARM: "✨"}
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


@dataclass
class CaughtPokemon:
    species_id: int
    species_name: str
    rarity: Rarity
    nature: PokemonNature
    is_shiny: bool
    caught_at: float
    total_tokens_spent: int
