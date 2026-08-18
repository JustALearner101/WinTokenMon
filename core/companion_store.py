"""
Game state and mechanics engine for WinTokenMon Windows
"""

import json
import os
import random
import time
from collections import deque
from dataclasses import dataclass

from .models import (
    ActivePokemon,
    EggTier,
    ItemKind,
    PokemonBalance,
    PokemonNature,
    Rarity,
)
from .poke_api import CURATED_EVOLUTION_LINES, SPECIES_INDEX

DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "WinTokenMon")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
os.makedirs(DATA_DIR, exist_ok=True)

# Backward-compatible migration from legacy PokeTokenBar directory
OLD_DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "PokeTokenBar")
OLD_STATE_FILE = os.path.join(OLD_DATA_DIR, "state.json")
if not os.path.exists(STATE_FILE) and os.path.exists(OLD_STATE_FILE):
    try:
        import shutil

        shutil.copy2(OLD_STATE_FILE, STATE_FILE)
    except Exception:
        pass


@dataclass
class CeremonyEvent:
    """Represents a pending visual ceremony event for UI playback."""

    HATCH = "hatch"
    EVOLVE = "evolve"
    GRADUATE = "graduate"
    CANDY_XP = "candy_xp"
    MINT_CHANGE = "mint_change"

    event_type: str
    species_id: int = 0
    species_name: str = ""
    is_shiny: bool = False
    xp_amount: int = 0
    new_nature: str = ""


class CompanionStore:
    def __init__(self):
        self.active: ActivePokemon | None = None
        self.egg_usage: int = 0
        self.egg_tier: EggTier = EggTier.STANDARD
        self.pokedex: dict[
            str, dict
        ] = {}  # str(species_id) -> {"name": str, "shiny": bool, "caught_at": float}
        self.catch_log: list[dict] = []
        self.inventory: dict[str, int] = {
            ItemKind.RARE_CANDY.value: 1,
            ItemKind.MINT.value: 0,
            ItemKind.SHINY_CHARM.value: 0,
        }
        self.spendable_tokens: int = 0
        self.total_tokens_burned_lifetime: int = 0

        # Notification & Limit settings
        self.daily_token_limit: int = 20_000_000  # Default 20M tokens limit
        self.notified_80_today: bool = False
        self.notified_100_today: bool = False
        self.last_notification_date: str = ""

        # UI & Animation preferences
        self.pet_size_preset: str = "medium"  # "small" (80), "medium" (110), "large" (150)
        self.pet_opacity: int = 100  # 50 - 100%
        self.taskbar_snap: bool = False
        self.sound_enabled: bool = True
        self.roaming_enabled: bool = True  # Autonomous wandering on desktop

        # 7-day token history: {"YYYY-MM-DD": tokens}
        self.daily_history: dict[str, int] = {}

        # In-memory ceremony event queue for UI playback
        self.ceremony_queue: deque = deque(maxlen=20)

        # Event callbacks / UI notifications
        self.on_hatch_callbacks = []
        self.on_evolve_callbacks = []
        self.on_graduate_callbacks = []

        # Starter selection flag for first launch
        self.starter_chosen: bool = False

        self.load()

        # If existing state already has an active companion or pokedex entry, mark starter as chosen
        if self.active is not None or bool(self.pokedex):
            self.starter_chosen = True

    def save(self):
        data = {
            "active": {
                "species_id": self.active.species_id,
                "species_name": self.active.species_name,
                "stage_index": self.active.stage_index,
                "total_forms": self.active.total_forms,
                "used_at_stage": self.active.used_at_stage,
                "rarity": self.active.rarity.value,
                "nature": self.active.nature.value,
                "is_shiny": self.active.is_shiny,
                "hatched_at": self.active.hatched_at,
                "evolution_chain_ids": self.active.evolution_chain_ids,
            }
            if self.active
            else None,
            "egg_usage": self.egg_usage,
            "egg_tier": self.egg_tier.value,
            "pokedex": self.pokedex,
            "catch_log": self.catch_log,
            "inventory": self.inventory,
            "spendable_tokens": self.spendable_tokens,
            "total_tokens_burned_lifetime": self.total_tokens_burned_lifetime,
            "daily_token_limit": self.daily_token_limit,
            "notified_80_today": self.notified_80_today,
            "notified_100_today": self.notified_100_today,
            "last_notification_date": self.last_notification_date,
            "pet_size_preset": self.pet_size_preset,
            "pet_opacity": self.pet_opacity,
            "taskbar_snap": self.taskbar_snap,
            "sound_enabled": self.sound_enabled,
            "roaming_enabled": self.roaming_enabled,
            "starter_chosen": self.starter_chosen,
            "daily_history": self.daily_history,
        }
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
        except Exception:
            pass

    def load(self):
        if not os.path.exists(STATE_FILE):
            return
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)

            act_data = data.get("active")
            if act_data:
                self.active = ActivePokemon(
                    species_id=act_data["species_id"],
                    species_name=act_data["species_name"],
                    stage_index=act_data["stage_index"],
                    total_forms=act_data["total_forms"],
                    used_at_stage=act_data["used_at_stage"],
                    rarity=Rarity(act_data["rarity"]),
                    nature=PokemonNature(act_data["nature"]),
                    is_shiny=act_data["is_shiny"],
                    hatched_at=act_data.get("hatched_at", time.time()),
                    evolution_chain_ids=act_data.get("evolution_chain_ids", []),
                )
            else:
                self.active = None

            self.egg_usage = data.get("egg_usage", 0)
            self.egg_tier = EggTier(data.get("egg_tier", "standard"))
            self.pokedex = data.get("pokedex", {})
            self.catch_log = data.get("catch_log", [])
            self.inventory = data.get(
                "inventory",
                {
                    ItemKind.RARE_CANDY.value: 1,
                    ItemKind.MINT.value: 0,
                    ItemKind.SHINY_CHARM.value: 0,
                },
            )
            self.spendable_tokens = data.get("spendable_tokens", 0)
            self.total_tokens_burned_lifetime = data.get("total_tokens_burned_lifetime", 0)
            self.daily_token_limit = data.get("daily_token_limit", 20_000_000)
            self.notified_80_today = data.get("notified_80_today", False)
            self.notified_100_today = data.get("notified_100_today", False)
            self.last_notification_date = data.get("last_notification_date", "")
            self.pet_size_preset = data.get("pet_size_preset", "medium")
            self.pet_opacity = data.get("pet_opacity", 100)
            self.taskbar_snap = data.get("taskbar_snap", False)
            self.sound_enabled = data.get("sound_enabled", True)
            self.roaming_enabled = data.get("roaming_enabled", True)
            self.starter_chosen = data.get("starter_chosen", self.active is not None)
            self.daily_history = data.get("daily_history", {})
        except Exception:
            pass

    @property
    def is_egg(self) -> bool:
        return self.active is None

    @property
    def display_name(self) -> str:
        if self.is_egg:
            return "Pokémon Egg"
        return self.active.species_name

    @property
    def current_threshold(self) -> int:
        if self.is_egg:
            return self.egg_tier.hatch_threshold
        return PokemonBalance.phase_threshold(
            self.active.rarity, self.active.total_forms, self.active.stage_index
        )

    @property
    def progress_percentage(self) -> float:
        thresh = self.current_threshold
        if thresh <= 0:
            return 1.0
        if self.is_egg:
            return min(1.0, self.egg_usage / float(thresh))
        return min(1.0, self.active.used_at_stage / float(thresh))

    @property
    def is_final_stage(self) -> bool:
        if self.is_egg:
            return False
        return self.active.stage_index >= (self.active.total_forms - 1)

    def record_daily_tokens(self, today_tokens: int):
        """Records today's token count in the 7-day rolling history, skipping disk write if unchanged."""
        today_str = time.strftime("%Y-%m-%d")
        if self.daily_history.get(today_str) == today_tokens:
            return
        self.daily_history[today_str] = today_tokens
        # Prune older entries to keep last 7-14 days
        sorted_keys = sorted(self.daily_history.keys())
        while len(sorted_keys) > 7:
            del self.daily_history[sorted_keys.pop(0)]
        self.save()

    def add_tokens(self, delta: int):
        """Adds burned tokens to spendable currency and companion progress."""
        if delta <= 0:
            return

        self.spendable_tokens += delta
        self.total_tokens_burned_lifetime += delta
        self._add_companion_exp(delta)
        self.save()

    def _add_companion_exp(self, delta: int):
        """Internal helper to progress egg or active companion EXP without re-crediting spendable tokens."""
        if delta <= 0:
            return

        thresh = self.current_threshold
        if self.is_egg:
            self.egg_usage += delta
            if self.egg_usage >= thresh:
                overflow = self.egg_usage - thresh
                self.hatch_egg()
                if overflow > 0 and self.active:
                    self._add_companion_exp(overflow)
        else:
            self.active.used_at_stage += delta
            if self.active.used_at_stage >= thresh:
                overflow = self.active.used_at_stage - thresh
                if not self.is_final_stage:
                    self.evolve()
                    if overflow > 0:
                        self._add_companion_exp(overflow)
                else:
                    self.graduate()
                    if overflow > 0:
                        self._add_companion_exp(overflow)

    def hatch_egg(self):
        """Hatches the egg into a new companion."""
        # Filter candidate lines based on egg tier
        candidates = CURATED_EVOLUTION_LINES
        if self.egg_tier == EggTier.UNCOMMON:
            candidates = [
                c
                for c in CURATED_EVOLUTION_LINES
                if c["rarity"] in ("uncommon", "rare", "legendary")
            ]
        elif self.egg_tier == EggTier.RARE:
            candidates = [
                c for c in CURATED_EVOLUTION_LINES if c["rarity"] in ("rare", "legendary")
            ]
        elif self.egg_tier == EggTier.LEGENDARY:
            candidates = [c for c in CURATED_EVOLUTION_LINES if c["rarity"] == "legendary"]

        selected_line = random.choice(candidates if candidates else CURATED_EVOLUTION_LINES)

        # Shiny chance: 1 in 129 base (or 1 in 40 if shiny charm owned)
        has_shiny_charm = self.inventory.get(ItemKind.SHINY_CHARM.value, 0) > 0
        shiny_odds = 40 if has_shiny_charm else 129
        is_shiny = random.randint(1, shiny_odds) == 1

        # Roll nature
        nature = random.choice(list(PokemonNature))

        first_species_id = selected_line["chain"][0]
        first_species_name = selected_line["names"][0]

        self.active = ActivePokemon(
            species_id=first_species_id,
            species_name=first_species_name,
            stage_index=0,
            total_forms=len(selected_line["chain"]),
            used_at_stage=0,
            rarity=Rarity(selected_line["rarity"]),
            nature=nature,
            is_shiny=is_shiny,
            hatched_at=time.time(),
            evolution_chain_ids=selected_line["chain"],
        )
        self.egg_usage = 0
        self.egg_tier = EggTier.STANDARD

        # Register in Pokédex immediately
        self._record_pokedex(self.active.species_id, self.active.species_name, self.active.is_shiny)

        # Queue Ceremony Event
        self.ceremony_queue.append(
            CeremonyEvent(
                event_type=CeremonyEvent.HATCH,
                species_id=self.active.species_id,
                species_name=self.active.species_name,
                is_shiny=self.active.is_shiny,
            )
        )

        for cb in self.on_hatch_callbacks:
            cb(self.active)
        self.save()

    def choose_starter(self, species_id: int, is_shiny: bool = False) -> bool:
        """Initializes and activates the user-selected Starter Pokémon on onboarding."""
        selected_line = SPECIES_INDEX.get(species_id)
        if not selected_line:
            return False

        idx = (
            selected_line["chain"].index(species_id) if species_id in selected_line["chain"] else 0
        )
        target_id = selected_line["chain"][idx]
        target_name = selected_line["names"][idx]

        nature = random.choice(list(PokemonNature))

        self.active = ActivePokemon(
            species_id=target_id,
            species_name=target_name,
            stage_index=idx,
            total_forms=len(selected_line["chain"]),
            used_at_stage=0,
            rarity=Rarity(selected_line["rarity"]),
            nature=nature,
            is_shiny=is_shiny,
            hatched_at=time.time(),
            evolution_chain_ids=selected_line["chain"],
        )
        self.egg_usage = 0
        self.egg_tier = EggTier.STANDARD
        self.starter_chosen = True

        # Register in Pokédex immediately
        self._record_pokedex(self.active.species_id, self.active.species_name, self.active.is_shiny)

        # Queue Ceremony Event for onboarding celebration
        self.ceremony_queue.append(
            CeremonyEvent(
                event_type=CeremonyEvent.HATCH,
                species_id=self.active.species_id,
                species_name=self.active.species_name,
                is_shiny=self.active.is_shiny,
            )
        )

        for cb in self.on_hatch_callbacks:
            cb(self.active)
        self.save()
        return True

    def evolve(self):
        """Evolves active Pokémon to the next stage in its evolution chain."""
        if not self.active or self.is_final_stage:
            return

        self.active.stage_index += 1
        self.active.used_at_stage = 0

        next_id = self.active.evolution_chain_ids[self.active.stage_index]
        line = SPECIES_INDEX.get(next_id)
        if line and next_id in line["chain"]:
            idx = line["chain"].index(next_id)
            self.active.species_id = next_id
            self.active.species_name = line["names"][idx]

        self._record_pokedex(self.active.species_id, self.active.species_name, self.active.is_shiny)

        # Queue Ceremony Event
        self.ceremony_queue.append(
            CeremonyEvent(
                event_type=CeremonyEvent.EVOLVE,
                species_id=self.active.species_id,
                species_name=self.active.species_name,
                is_shiny=self.active.is_shiny,
            )
        )

        for cb in self.on_evolve_callbacks:
            cb(self.active)
        self.save()

    def graduate(self):
        """Graduates final form Pokémon into Pokédex and archives in Catch Log."""
        if not self.active:
            return

        caught = {
            "species_id": self.active.species_id,
            "species_name": self.active.species_name,
            "rarity": self.active.rarity.value,
            "nature": self.active.nature.value,
            "is_shiny": self.active.is_shiny,
            "caught_at": time.time(),
            "total_tokens_spent": PokemonBalance.graduation_total(self.active.rarity),
        }
        self.catch_log.append(caught)
        self._record_pokedex(self.active.species_id, self.active.species_name, self.active.is_shiny)

        # Reward 1 Rare Candy for graduating!
        self.inventory[ItemKind.RARE_CANDY.value] = (
            self.inventory.get(ItemKind.RARE_CANDY.value, 0) + 1
        )

        graduated_pokemon = self.active
        self.active = None
        self.egg_usage = 0
        self.egg_tier = EggTier.STANDARD

        # Queue Ceremony Event
        self.ceremony_queue.append(
            CeremonyEvent(
                event_type=CeremonyEvent.GRADUATE,
                species_id=graduated_pokemon.species_id,
                species_name=graduated_pokemon.species_name,
                is_shiny=graduated_pokemon.is_shiny,
            )
        )

        for cb in self.on_graduate_callbacks:
            cb(graduated_pokemon)
        self.save()

    def use_item(self, item: ItemKind) -> bool:
        """Uses an item from the inventory."""
        count = self.inventory.get(item.value, 0)
        if count <= 0:
            return False

        if item == ItemKind.RARE_CANDY:
            self.inventory[item.value] -= 1
            # Add 100M EXP
            self.ceremony_queue.append(
                CeremonyEvent(event_type=CeremonyEvent.CANDY_XP, xp_amount=100_000_000)
            )
            self.add_tokens(100_000_000)
            self.save()
            return True
        elif item == ItemKind.SHINY_CHARM:
            # Passive item, already active when owned
            return True
        return False

    def use_mint_with_nature(self, nature: PokemonNature | str) -> bool:
        """Uses a Nature Mint to change the active Pokémon to a specific desired nature."""
        if not self.active:
            return False
        if self.inventory.get(ItemKind.MINT.value, 0) <= 0:
            return False

        if isinstance(nature, str):
            try:
                nature = PokemonNature(nature)
            except ValueError:
                return False

        self.inventory[ItemKind.MINT.value] -= 1
        self.active.nature = nature
        self.ceremony_queue.append(
            CeremonyEvent(event_type=CeremonyEvent.MINT_CHANGE, new_nature=self.active.nature.value)
        )
        self.save()
        return True

    def set_active_from_pokedex(self, species_id: int) -> bool:
        """Switches the active desktop companion to a previously caught Pokémon from the Pokédex."""
        key = str(species_id)
        if key not in self.pokedex:
            return False

        poke_data = self.pokedex[key]
        is_shiny = poke_data.get("shiny", False)

        line_info = SPECIES_INDEX.get(species_id)
        if not line_info:
            return False

        stage_idx = line_info["chain"].index(species_id)
        rarity_val = Rarity(line_info.get("rarity", "uncommon"))
        default_nature = random.choice(list(PokemonNature))

        self.active = ActivePokemon(
            species_id=species_id,
            species_name=line_info["names"][stage_idx],
            stage_index=stage_idx,
            total_forms=len(line_info["chain"]),
            used_at_stage=0,
            rarity=rarity_val,
            nature=default_nature,
            is_shiny=is_shiny,
            hatched_at=time.time(),
            evolution_chain_ids=line_info["chain"],
        )
        self.save()
        return True

    def get_trainer_rank(self) -> tuple[str, str, float]:
        """
        Returns (Rank Title, Tier Badge, Progress to next rank [0.0 - 1.0])
        based on total_tokens_burned_lifetime.
        """
        tokens = self.total_tokens_burned_lifetime
        if tokens < 5_000_000:
            pct = min(1.0, tokens / 5_000_000)
            return "🌱 Novice Coder", "Rank I", pct
        elif tokens < 25_000_000:
            pct = min(1.0, (tokens - 5_000_000) / 20_000_000)
            return "⚡ Prompt Enthusiast", "Rank II", pct
        elif tokens < 100_000_000:
            pct = min(1.0, (tokens - 25_000_000) / 75_000_000)
            return "🔥 AI Specialist", "Rank III", pct
        elif tokens < 300_000_000:
            pct = min(1.0, (tokens - 100_000_000) / 200_000_000)
            return "💎 Model Master", "Rank IV", pct
        else:
            return "👑 Legendary Architect", "Master", 1.0

    def get_active_streak(self) -> int:
        """Calculates consecutive active days with recorded token usage."""
        if not self.daily_history:
            return 1 if self.active is not None else 0

        streak = 0
        from datetime import datetime, timedelta

        today = datetime.now()
        for i in range(14):
            day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            tokens = self.daily_history.get(day_str, 0)
            if tokens > 0 or i == 0:
                if tokens > 0:
                    streak += 1
            else:
                break
        return max(1, streak)

    def buy_item(self, item: ItemKind) -> bool:
        price = item.price_tokens
        if self.spendable_tokens < price:
            return False
        if item == ItemKind.SHINY_CHARM and self.inventory.get(item.value, 0) >= 1:
            return False  # Only 1 shiny charm allowed

        self.spendable_tokens -= price
        self.inventory[item.value] = self.inventory.get(item.value, 0) + 1
        self.save()
        return True

    def buy_egg(self, tier: EggTier) -> bool:
        price = tier.price_tokens
        if self.spendable_tokens < price:
            return False

        self.spendable_tokens -= price
        self.active = None
        self.egg_usage = 0
        self.egg_tier = tier
        self.save()
        return True

    def reset_to_fresh_egg(self):
        """Resets active companion to a fresh starter egg."""
        self.active = None
        self.egg_usage = 0
        self.egg_tier = EggTier.STANDARD
        self.save()

    def _record_pokedex(self, species_id: int, name: str, is_shiny: bool, rarity: str | None = None):
        key = str(species_id)
        current = self.pokedex.get(key, {})
        shiny_owned = current.get("shiny", False) or is_shiny

        # Lookup rarity from curated index if not provided
        if not rarity:
            line = SPECIES_INDEX.get(species_id)
            if line:
                rarity = line.get("rarity", "uncommon")
        if not rarity:
            rarity = current.get("rarity", "uncommon")

        self.pokedex[key] = {
            "id": species_id,
            "name": name,
            "shiny": shiny_owned,
            "rarity": rarity,
            "caught_at": current.get("caught_at", time.time()),
        }

    def get_dex_species(self) -> list[dict]:
        """
        Returns all unique registered Pokémon species (graduated + currently raising)
        sorted by species ID using O(1) index lookup.
        """
        species_map = {}

        # 1. Add all entries saved in pokedex
        for sid_str, data in self.pokedex.items():
            try:
                sid = int(sid_str)
            except ValueError:
                continue

            rarity = data.get("rarity")
            if not rarity:
                line = SPECIES_INDEX.get(sid)
                if line:
                    rarity = line.get("rarity", "uncommon")

            species_map[sid] = {
                "id": sid,
                "name": data.get("name", f"Pokémon #{sid}"),
                "rarity": rarity or "uncommon",
                "is_shiny": data.get("shiny", False),
                "is_raising": False,
                "caught_at": data.get("caught_at", 0),
            }

        # 2. Add current active Pokémon and all reached stages in its evolution chain
        if self.active:
            reached_ids = self.active.evolution_chain_ids[: self.active.stage_index + 1]
            for sid in reached_ids:
                sp_name = self.active.species_name if sid == self.active.species_id else None
                if not sp_name:
                    line = SPECIES_INDEX.get(sid)
                    if line:
                        idx = line["chain"].index(sid)
                        sp_name = line["names"][idx]

                if sid not in species_map:
                    species_map[sid] = {
                        "id": sid,
                        "name": sp_name or f"Pokémon #{sid}",
                        "rarity": self.active.rarity.value,
                        "is_shiny": self.active.is_shiny,
                        "is_raising": (sid == self.active.species_id),
                        "caught_at": self.active.hatched_at,
                    }
                else:
                    if sid == self.active.species_id:
                        species_map[sid]["is_raising"] = True
                        if self.active.is_shiny:
                            species_map[sid]["is_shiny"] = True

        return sorted(species_map.values(), key=lambda x: x["id"])

    def set_daily_token_limit(self, limit: int):
        """Sets the daily token limit and saves state."""
        self.daily_token_limit = max(0, limit)
        self.save()

    def check_and_trigger_notifications(self, today_tokens: int) -> tuple[str, str] | None:
        """
        Evaluates daily token usage against the configured limit.
        Returns (title, message) tuple if an 80% or 100% threshold alert should be fired.
        """
        today_date = time.strftime("%Y-%m-%d")
        # Daily reset of notification flags
        if self.last_notification_date != today_date:
            self.last_notification_date = today_date
            self.notified_80_today = False
            self.notified_100_today = False
            self.save()

        if self.daily_token_limit <= 0:
            return None

        # 100% threshold
        if today_tokens >= self.daily_token_limit:
            if not self.notified_100_today:
                self.notified_100_today = True
                self.notified_80_today = True
                self.save()
                return (
                    "🚨 Token Limit Reached (100%)",
                    f"You have reached 100% of your daily limit: {today_tokens:,} / {self.daily_token_limit:,} tokens!",
                )
            return None

        # 80% threshold
        limit_80 = int(self.daily_token_limit * 0.8)
        if today_tokens >= limit_80:
            if not self.notified_80_today:
                self.notified_80_today = True
                self.save()
                return (
                    "⚠️ Token Warning (80%)",
                    f"You have reached 80% of your daily limit: {today_tokens:,} / {self.daily_token_limit:,} tokens.",
                )
            return None

        return None
