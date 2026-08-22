"""
Game state and mechanics engine for WinTokenMon Windows
"""

import json
import os
import random
import shutil
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from .applog import log_error
from .autostart import is_autostart_enabled
from .autostart import set_autostart as reg_set_autostart
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

DEFAULT_INVENTORY = lambda: {  # noqa: E731
    ItemKind.RARE_CANDY.value: 1,
    ItemKind.ORAN_BERRY.value: 0,
    ItemKind.MINT.value: 0,
    ItemKind.SHINY_CHARM.value: 0,
}

# Scalar/JSON-ready settings persisted verbatim between save() and load()
_SIMPLE_FIELDS = {
    "egg_usage": 0,
    "spendable_tokens": 0,
    "total_tokens_burned_lifetime": 0,
    "daily_token_limit": 20_000_000,
    "notified_80_today": False,
    "notified_100_today": False,
    "last_notification_date": "",
    "pet_size_preset": "medium",
    "pet_opacity": 100,
    "taskbar_snap": False,
    "sound_enabled": True,
    "roaming_enabled": True,
    "spawn_intro_enabled": True,
    "auto_evolve_enabled": False,
    "autostart_enabled": False,
    "display_mode": "full_pet",
    "hud_position": None,
    "hud_opacity": 90,
    "starter_chosen": False,
    # Auto-update preferences (RFC v1.0.0 §4)
    "auto_check_updates_enabled": True,
    "skipped_update_version": "",
    "last_update_check_time": 0.0,
}

# Backward-compatible migration from legacy PokeTokenBar directory
OLD_DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "PokeTokenBar")
OLD_STATE_FILE = os.path.join(OLD_DATA_DIR, "state.json")
if not os.path.exists(STATE_FILE) and os.path.exists(OLD_STATE_FILE):
    try:
        shutil.copy2(OLD_STATE_FILE, STATE_FILE)
    except Exception as exc:
        log_error(f"legacy_state_migration_failed: {exc}")


@dataclass
class CeremonyEvent:
    """Represents a pending visual ceremony event for UI playback."""

    HATCH = "hatch"
    EVOLVE = "evolve"
    GRADUATE = "graduate"
    CANDY_XP = "candy_xp"
    MINT_CHANGE = "mint_change"
    FRIENDSHIP_UP = "friendship_up"

    event_type: str
    species_id: int = 0
    species_name: str = ""
    is_shiny: bool = False
    xp_amount: int = 0
    new_nature: str = ""
    friendship_amount: int = 0
    item_kind: str = ""


class CompanionStore:
    def __init__(self):
        self.active: ActivePokemon | None = None
        self.egg_usage: int = 0
        self.egg_tier: EggTier = EggTier.STANDARD
        self.pokedex: dict[
            str, dict
        ] = {}  # str(species_id) -> {"name": str, "shiny": bool, "caught_at": float}
        self.catch_log: list[dict] = []
        self.inventory: dict[str, int] = DEFAULT_INVENTORY()
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
        self.spawn_intro_enabled: bool = True  # Pokéball entrance intro animation on startup
        self.auto_evolve_enabled: bool = False  # Auto-evolve vs manual trigger when threshold met
        self.autostart_enabled: bool = False  # Start with Windows boot (HKCU Run key)

        # Compact HUD presentation mode (v0.4.0)
        self.display_mode: str = "full_pet"  # "full_pet" or "compact_hud"
        self.hud_position: dict | None = None  # {"x": int, "y": int}
        self.hud_opacity: int = 90  # 50 - 100%
        self.tracked_providers: dict[str, bool] = {
            "antigravity": True,
            "claude": True,
            "cursor": True,
            "codex": True,
            "copilot": True,
            "koma": True,
            "aider": True,
            "windsurf": True,
            "cline": True,
            "roo": True,
        }

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

        # Achievements & Badges tracking (v0.2.0)
        self.unlocked_achievements: dict[str, float] = {}  # badge_id -> timestamp
        self.purchased_egg_tiers: list[str] = []
        self.total_hatches: int = 0
        self.on_achievement_callbacks = []

        # Auto-update preferences (persisted via _SIMPLE_FIELDS)
        self.auto_check_updates_enabled: bool = True
        self.skipped_update_version: str = ""
        self.last_update_check_time: float = 0.0

        self.load()

        # If existing state already has an active companion or pokedex entry, mark starter as chosen
        if self.active is not None or bool(self.pokedex):
            self.starter_chosen = True

    def save(self):
        data = {f: getattr(self, f) for f in _SIMPLE_FIELDS}
        data.update(
            {
                "active": self._serialize_active() if self.active else None,
                "egg_tier": self.egg_tier.value,
                "pokedex": self.pokedex,
                "catch_log": self.catch_log,
                "inventory": self.inventory,
                "tracked_providers": self.tracked_providers,
            }
        )
        try:
            payload = json.dumps(data, separators=(",", ":"))
        except Exception as exc:
            log_error(f"state.serialize_failed: {exc}")
            return
        try:
            # Atomic write: temp file + os.replace so a crash mid-write can
            # never leave a half-written state.json behind.
            tmp_path = STATE_FILE + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(payload)
            if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 0:
                shutil.copy2(STATE_FILE, STATE_FILE + ".bak")
            os.replace(tmp_path, STATE_FILE)
        except Exception as exc:
            log_error(f"state.write_failed: {exc}")

    def _serialize_active(self) -> dict:
        a = self.active
        return {
            "species_id": a.species_id,
            "species_name": a.species_name,
            "stage_index": a.stage_index,
            "total_forms": a.total_forms,
            "used_at_stage": a.used_at_stage,
            "rarity": a.rarity.value,
            "nature": a.nature.value,
            "is_shiny": a.is_shiny,
            "hatched_at": a.hatched_at,
            "evolution_chain_ids": a.evolution_chain_ids,
            "friendship": a.friendship,
            "last_pet_date": a.last_pet_date,
            "daily_pet_count": a.daily_pet_count,
            "treats_eaten_today": a.treats_eaten_today,
            "last_treat_date": a.last_treat_date,
        }

    def load(self):
        """Loads state from the primary file, falling back to the .bak backup.

        A corrupt primary file is quarantined (never overwritten by the next
        save) before trying the backup.
        """
        candidates = [STATE_FILE]
        if os.path.exists(STATE_BAK := STATE_FILE + ".bak"):
            candidates.append(STATE_BAK)

        data = None
        for candidate in candidates:
            if not os.path.exists(candidate):
                continue
            try:
                with open(candidate, encoding="utf-8") as f:
                    data = json.load(f)
                break
            except Exception as exc:
                log_error(f"state.unreadable ({candidate}): {exc}")
                if candidate == STATE_FILE:
                    self._quarantine_corrupt_state()
                continue

        if isinstance(data, dict):
            try:
                self._apply_state(data)
            except Exception as exc:
                log_error(f"state.apply_failed: {exc}")
        elif data is not None:
            log_error("state.unexpected_format: root is not an object; using defaults")

    def _quarantine_corrupt_state(self):
        """Moves a corrupt state.json aside so the next save cannot destroy it."""
        try:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            os.replace(STATE_FILE, STATE_FILE + f".corrupt-{stamp}")
            log_error(f"state.quarantined -> {STATE_FILE}.corrupt-{stamp}")
        except Exception as exc:
            log_error(f"state.quarantine_failed: {exc}")

    def _apply_state(self, data: dict):
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
                is_shiny=bool(act_data["is_shiny"]),
                hatched_at=act_data.get("hatched_at", time.time()),
                evolution_chain_ids=act_data.get("evolution_chain_ids", []),
                friendship=act_data.get("friendship", 50),
                last_pet_date=act_data.get("last_pet_date", ""),
                daily_pet_count=act_data.get("daily_pet_count", 0),
                treats_eaten_today=act_data.get("treats_eaten_today", 0),
                last_treat_date=act_data.get("last_treat_date", ""),
            )
        else:
            self.active = None

        try:
            self.egg_tier = EggTier(data.get("egg_tier", "standard"))
        except ValueError:
            self.egg_tier = EggTier.STANDARD
            log_error(f"state.invalid_egg_tier: {data.get('egg_tier')!r}")
        self.pokedex = data.get("pokedex", {})
        self.catch_log = data.get("catch_log", [])
        self.inventory = data.get("inventory") or DEFAULT_INVENTORY()
        if ItemKind.ORAN_BERRY.value not in self.inventory:
            self.inventory[ItemKind.ORAN_BERRY.value] = 0
        for field, default in _SIMPLE_FIELDS.items():
            setattr(self, field, data.get(field, default))
        if is_autostart_enabled():
            self.autostart_enabled = True
        saved_providers = data.get("tracked_providers", {})
        for key in self.tracked_providers:
            if key in saved_providers:
                self.tracked_providers[key] = bool(saved_providers[key])
        self.daily_history = data.get("daily_history", {})
        self.unlocked_achievements = data.get("unlocked_achievements", {})
        self.purchased_egg_tiers = data.get("purchased_egg_tiers", [])
        self.total_hatches = data.get("total_hatches", len(self.catch_log))

        self._clamp_loaded_values()

        # Retro-migration for existing users without achievement records
        self._run_achievement_retro_migration()

    def _clamp_loaded_values(self):
        """Sanity-clamps numeric fields so a damaged save cannot produce
        negative balances or out-of-range stats."""
        self.spendable_tokens = max(0, int(self.spendable_tokens or 0))
        self.total_tokens_burned_lifetime = max(0, int(self.total_tokens_burned_lifetime or 0))
        self.daily_token_limit = max(0, int(self.daily_token_limit or 0))
        self.egg_usage = max(0, int(self.egg_usage or 0))
        self.total_hatches = max(0, int(self.total_hatches or 0))
        if self.active is not None:
            self.active.friendship = max(0, min(100, int(self.active.friendship)))
            self.active.used_at_stage = max(0, int(self.active.used_at_stage))
            chain = self.active.evolution_chain_ids
            if not chain or not (0 <= self.active.stage_index < len(chain)):
                self.active.stage_index = min(
                    max(0, self.active.stage_index), max(0, len(chain) - 1)
                )

    def _run_achievement_retro_migration(self):
        """Retroactively grants achievements based on existing savegame progression."""
        # 100M Burn Club
        if (
            self.total_tokens_burned_lifetime >= 100_000_000
            and "100m_burn_club" not in self.unlocked_achievements
        ):
            self.unlock_achievement("100m_burn_club")
        # First Hatch
        if (
            self.total_hatches >= 1 or len(self.catch_log) >= 1
        ) and "first_hatch" not in self.unlocked_achievements:
            self.unlock_achievement("first_hatch")
        # Shiny Hunter
        has_shiny = any(bool(entry.get("shiny")) for entry in self.pokedex.values()) or (
            self.active and self.active.is_shiny
        )
        if has_shiny and "shiny_hunter" not in self.unlocked_achievements:
            self.unlock_achievement("shiny_hunter")
        # Senior Professor
        if len(self.catch_log) >= 5 and "senior_professor" not in self.unlocked_achievements:
            self.unlock_achievement("senior_professor")
        # Egg Hoarder
        if {"uncommon", "rare", "legendary"}.issubset(
            set(self.purchased_egg_tiers)
        ) and "egg_hoarder" not in self.unlocked_achievements:
            self.unlock_achievement("egg_hoarder")

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

    @property
    def is_ready_to_evolve(self) -> bool:
        """Returns True if companion has reached token threshold for evolution and is awaiting evolution."""
        if self.is_egg or not self.active or self.is_final_stage:
            return False
        return self.active.used_at_stage >= self.current_threshold

    @property
    def next_species_info(self) -> tuple[int, str] | None:
        """Returns (next_species_id, next_species_name) if active companion can evolve."""
        if not self.active or self.is_final_stage or self.is_egg:
            return None
        next_stage_idx = self.active.stage_index + 1
        if next_stage_idx < len(self.active.evolution_chain_ids):
            next_id = self.active.evolution_chain_ids[next_stage_idx]
            line = SPECIES_INDEX.get(next_id)
            if line and next_id in line["chain"]:
                idx = line["chain"].index(next_id)
                return next_id, line["names"][idx]
        return None

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

        # High friendship (>= 80%) grants +10% bonus companion EXP
        effective_exp = delta
        if self.active and self.active.friendship >= 80:
            effective_exp = int(delta * 1.10)

        self._add_companion_exp(effective_exp)
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
                if not self.is_final_stage:
                    if self.auto_evolve_enabled:
                        self.evolve()
                else:
                    overflow = self.active.used_at_stage - thresh
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
        self.total_hatches += 1

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
        self.save()
        return True

    def evolve(self):
        """Evolves active Pokémon to the next stage in its evolution chain."""
        if not self.active or self.is_final_stage:
            return

        thresh = self.current_threshold
        overflow = max(0, self.active.used_at_stage - thresh)

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

        if overflow > 0:
            self._add_companion_exp(overflow)

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

    def pet_companion(self) -> tuple[bool, int, str]:
        """
        Interacts with (pets) the active companion.
        Grants +5 Friendship per pet up to 4 times a day (max +20% daily).
        Returns (success, current_friendship, feedback_message).
        """
        if self.is_egg or not self.active:
            return False, 0, "No active Pokémon to pet."

        today_str = time.strftime("%Y-%m-%d")
        if self.active.last_pet_date != today_str:
            self.active.last_pet_date = today_str
            self.active.daily_pet_count = 0

        if self.active.daily_pet_count >= 4:
            return (
                False,
                self.active.friendship,
                f"{self.active.species_name} is feeling plenty loved today! (Daily limit reached)",
            )

        self.active.daily_pet_count += 1
        gain = 5
        old_f = self.active.friendship
        self.active.friendship = min(100, self.active.friendship + gain)
        actual_gain = self.active.friendship - old_f

        self.ceremony_queue.append(
            CeremonyEvent(
                event_type=CeremonyEvent.FRIENDSHIP_UP,
                friendship_amount=actual_gain,
                species_name=self.active.species_name,
            )
        )
        self.save()
        return (
            True,
            self.active.friendship,
            f"Petted {self.active.species_name}! (+{gain}% Friendship, {self.active.friendship}%)",
        )

    def feed_treat(self, item_kind: ItemKind | str) -> tuple[bool, int, int]:
        """
        Feeds a treat (Rare Candy or Oran Berry) to the companion.
        Consumes 1 item, awards EXP and Friendship.
        Returns (success, xp_gained, new_friendship).
        """
        if isinstance(item_kind, str):
            try:
                item_kind = ItemKind(item_kind)
            except ValueError:
                return False, 0, 0

        if self.inventory.get(item_kind.value, 0) <= 0:
            return False, 0, 0

        self.inventory[item_kind.value] -= 1

        today_str = time.strftime("%Y-%m-%d")
        if self.active:
            if self.active.last_treat_date != today_str:
                self.active.last_treat_date = today_str
                self.active.treats_eaten_today = 0
            self.active.treats_eaten_today += 1

        if item_kind == ItemKind.RARE_CANDY:
            xp = 100_000_000
            f_gain = 15
        elif item_kind == ItemKind.ORAN_BERRY:
            xp = 10_000_000
            f_gain = 10
        else:
            xp = 0
            f_gain = 0

        if self.active and f_gain > 0:
            self.active.friendship = min(100, self.active.friendship + f_gain)

        self.ceremony_queue.append(
            CeremonyEvent(
                event_type=CeremonyEvent.CANDY_XP,
                xp_amount=xp,
                item_kind=item_kind.value,
            )
        )

        if xp > 0:
            self._add_companion_exp(xp)

        self.save()
        f_val = self.active.friendship if self.active else 0
        return True, xp, f_val

    def use_item(self, item: ItemKind) -> bool:
        """Uses an item from the inventory."""
        count = self.inventory.get(item.value, 0)
        if count <= 0:
            return False

        if item in (ItemKind.RARE_CANDY, ItemKind.ORAN_BERRY):
            success, _, _ = self.feed_treat(item)
            return success
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
        streak = 0
        today = datetime.now()
        for i in range(14):
            day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            if self.daily_history.get(day_str, 0) > 0:
                streak += 1
            elif i > 0:
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
        if tier.value not in self.purchased_egg_tiers:
            self.purchased_egg_tiers.append(tier.value)

        # Egg Hoarder: adopted all three paid egg tiers
        if {"uncommon", "rare", "legendary"}.issubset(set(self.purchased_egg_tiers)):
            self.unlock_achievement("egg_hoarder")

        self.save()
        return True

    def unlock_achievement(self, badge_id: str) -> bool:
        """
        Unlocks an achievement badge, awards tokens / items, and triggers callbacks.
        Guaranteed idempotent: returns False if already unlocked.
        """
        if badge_id in self.unlocked_achievements:
            return False

        from .models import ACHIEVEMENT_DEFINITIONS

        badge = ACHIEVEMENT_DEFINITIONS.get(badge_id)
        if not badge:
            return False

        self.unlocked_achievements[badge_id] = time.time()

        # Grant rewards
        if badge.reward_tokens > 0:
            self.spendable_tokens += badge.reward_tokens

        if badge.reward_item:
            count = max(1, badge.reward_item_count)
            self.inventory[badge.reward_item.value] = (
                self.inventory.get(badge.reward_item.value, 0) + count
            )

        self.save()

        for cb in self.on_achievement_callbacks:
            try:
                cb(badge)
            except Exception as exc:
                log_error(f"achievement_callback_failed ({badge.id}): {exc}")
        return True

    def reset_to_fresh_egg(self):
        """Resets active companion to a fresh starter egg."""
        self.active = None
        self.egg_usage = 0
        self.egg_tier = EggTier.STANDARD
        self.save()

    def _record_pokedex(
        self, species_id: int, name: str, is_shiny: bool, rarity: str | None = None
    ):
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

    def set_autostart(self, enabled: bool) -> bool:
        """Enables or disables automatic startup on Windows boot and updates state."""
        success = reg_set_autostart(enabled)
        if success:
            self.autostart_enabled = enabled
            self.save()
        return success

    # ─────────────────────────────────────────────────────────────────────────
    # DEVELOPER & DEBUG SANDBOX HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    def debug_add_tokens(self, amount: int):
        """Injects tokens immediately into progression and spendable balance."""
        self.add_tokens(amount)

    def debug_set_progress_pct(self, pct: float):
        """Sets current progress percentage (e.g. 0.99 for 99%)."""
        clamped = max(0.0, min(1.0, pct))
        target = int(self.current_threshold * clamped)
        if self.is_egg:
            self.egg_usage = target
        elif self.active:
            self.active.used_at_stage = target
        self.save()

    def debug_instant_hatch(self, tier: EggTier | None = None):
        """Hatches current egg immediately or creates a new egg of chosen tier and hatches it."""
        if not self.is_egg:
            self.active = None
            self.egg_usage = 0
        if tier:
            self.egg_tier = tier
        self.hatch_egg()

    def debug_set_species(
        self, species_id: int, is_shiny: bool = False, stage_index: int = 0
    ) -> bool:
        """Sets active Pokémon companion to any species in the database."""
        line = SPECIES_INDEX.get(species_id)
        if not line:
            return False
        total_forms = len(line["chain"])
        stg = min(stage_index, total_forms - 1)
        target_id = line["chain"][stg]
        target_name = line["names"][stg]
        nature = self.active.nature if self.active else random.choice(list(PokemonNature))
        friendship = self.active.friendship if self.active else 70

        self.active = ActivePokemon(
            species_id=target_id,
            species_name=target_name,
            stage_index=stg,
            total_forms=total_forms,
            used_at_stage=0,
            rarity=Rarity(line["rarity"]),
            nature=nature,
            is_shiny=is_shiny,
            hatched_at=time.time(),
            evolution_chain_ids=line["chain"],
            friendship=friendship,
        )
        self.egg_usage = 0
        self.starter_chosen = True
        self._record_pokedex(self.active.species_id, self.active.species_name, self.active.is_shiny)
        self.save()
        return True

    def debug_set_friendship(self, value: int):
        """Sets active companion friendship percentage."""
        if self.active:
            self.active.friendship = max(0, min(100, value))
            self.save()

    def debug_add_all_items(self, qty: int = 10):
        """Adds generous amounts of all shop items."""
        self.inventory[ItemKind.RARE_CANDY.value] = (
            self.inventory.get(ItemKind.RARE_CANDY.value, 0) + qty
        )
        self.inventory[ItemKind.ORAN_BERRY.value] = (
            self.inventory.get(ItemKind.ORAN_BERRY.value, 0) + qty
        )
        self.inventory[ItemKind.MINT.value] = self.inventory.get(ItemKind.MINT.value, 0) + qty
        self.inventory[ItemKind.SHINY_CHARM.value] = 1
        self.spendable_tokens += 100_000_000
        self.save()

    def debug_reset_all(self):
        """Resets all progression and save file to fresh onboarding state."""
        self.active = None
        self.egg_usage = 0
        self.egg_tier = EggTier.STANDARD
        self.pokedex = {}
        self.catch_log = []
        self.inventory = DEFAULT_INVENTORY()
        self.spendable_tokens = 0
        self.total_tokens_burned_lifetime = 0
        self.daily_history = {}
        self.unlocked_achievements = {}
        self.purchased_egg_tiers = []
        self.total_hatches = 0
        self.starter_chosen = False
        self.save()
