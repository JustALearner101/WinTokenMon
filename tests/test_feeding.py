"""
Unit tests for v0.3.0 Interactive Desktop Feeding & Friendship Mechanics
"""

import json
import os
import tempfile
import time

import pytest

from core.companion_store import CompanionStore
from core.models import ActivePokemon, ItemKind, PokemonNature, Rarity


@pytest.fixture
def clean_store(monkeypatch):
    """Provides an isolated CompanionStore with a clean temp state file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = os.path.join(tmp_dir, "state.json")
        monkeypatch.setattr("core.companion_store.STATE_FILE", tmp_file)
        store = CompanionStore()
        # Initialize an active Pokémon (Charmander)
        store.active = ActivePokemon(
            species_id=4,
            species_name="Charmander",
            stage_index=0,
            total_forms=3,
            used_at_stage=0,
            rarity=Rarity.UNCOMMON,
            nature=PokemonNature.ADAMANT,
            is_shiny=False,
            hatched_at=time.time(),
            evolution_chain_ids=[4, 5, 6],
            friendship=50,
            last_pet_date="",
            daily_pet_count=0,
            treats_eaten_today=0,
            last_treat_date="",
        )
        yield store


def test_friendship_initialization_and_migration(monkeypatch):
    """Verifies default friendship value is 50 for new hatches and backward compatibility."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = os.path.join(tmp_dir, "state.json")
        monkeypatch.setattr("core.companion_store.STATE_FILE", tmp_file)

        # 1. Write legacy state without friendship field
        legacy_data = {
            "active": {
                "species_id": 1,
                "species_name": "Bulbasaur",
                "stage_index": 0,
                "total_forms": 3,
                "used_at_stage": 500,
                "rarity": "uncommon",
                "nature": "Modest",
                "is_shiny": False,
                "hatched_at": time.time(),
                "evolution_chain_ids": [1, 2, 3],
            },
            "inventory": {"rareCandy": 2, "mint": 0, "shinyCharm": 0},
            "spendable_tokens": 1000,
        }
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        store = CompanionStore()
        assert store.active is not None
        assert store.active.friendship == 50
        assert store.active.daily_pet_count == 0
        assert store.active.treats_eaten_today == 0
        assert ItemKind.ORAN_BERRY.value in store.inventory


def test_petting_daily_limit_and_reset(clean_store):
    """Verifies petting increases friendship by +5 per pet, max 4 times/day (+20%), and resets on a new day."""
    store = clean_store
    initial_f = store.active.friendship  # 50

    # Pet 1
    ok, f1, _ = store.pet_companion()
    assert ok is True
    assert f1 == initial_f + 5  # 55
    assert store.active.daily_pet_count == 1

    # Pet 2, 3, 4
    store.pet_companion()
    store.pet_companion()
    ok4, f4, _ = store.pet_companion()
    assert ok4 is True
    assert f4 == initial_f + 20  # 70
    assert store.active.daily_pet_count == 4

    # 5th pet on same day should be rejected (daily cap hit)
    ok5, f5, msg = store.pet_companion()
    assert ok5 is False
    assert f5 == 70
    assert "Daily limit reached" in msg

    # Simulate next day
    store.active.last_pet_date = "2020-01-01"
    ok_next, f_next, _ = store.pet_companion()
    assert ok_next is True
    assert f_next == 75
    assert store.active.daily_pet_count == 1


def test_feed_treat_rare_candy_and_oran_berry(clean_store):
    """Verifies feeding treats consumes inventory, grants correct EXP, and increases friendship."""
    store = clean_store
    store.inventory[ItemKind.RARE_CANDY.value] = 2
    store.inventory[ItemKind.ORAN_BERRY.value] = 3
    store.active.used_at_stage = 0
    store.active.friendship = 50

    # Feed Oran Berry: +10M EXP, +10 Friendship
    ok_berry, xp_b, f_b = store.feed_treat(ItemKind.ORAN_BERRY)
    assert ok_berry is True
    assert xp_b == 10_000_000
    assert f_b == 60
    assert store.inventory[ItemKind.ORAN_BERRY.value] == 2
    assert store.active.used_at_stage == 10_000_000
    assert store.active.treats_eaten_today == 1

    # Feed Rare Candy: +100M EXP, +15 Friendship
    ok_candy, xp_c, f_c = store.feed_treat(ItemKind.RARE_CANDY)
    assert ok_candy is True
    assert xp_c == 100_000_000
    assert f_c == 75
    assert store.inventory[ItemKind.RARE_CANDY.value] == 1
    assert store.active.used_at_stage == 110_000_000
    assert store.active.treats_eaten_today == 2


def test_friendship_capped_at_100(clean_store):
    """Verifies friendship cannot exceed 100."""
    store = clean_store
    store.active.friendship = 95
    store.inventory[ItemKind.RARE_CANDY.value] = 1

    ok, _, f_val = store.feed_treat(ItemKind.RARE_CANDY)
    assert ok is True
    assert f_val == 100
    assert store.active.friendship == 100


def test_high_friendship_exp_boost(clean_store):
    """Verifies that companions with >=80% friendship get +10% bonus EXP on token consumption."""
    store = clean_store
    store.active.used_at_stage = 0

    # Normal friendship (<80%)
    store.active.friendship = 60
    store.add_tokens(100_000)
    assert store.active.used_at_stage == 100_000

    # High friendship (>=80%) -> +10% bonus EXP
    store.active.friendship = 85
    store.active.used_at_stage = 0
    store.add_tokens(100_000)
    assert store.active.used_at_stage == 110_000  # 100_000 * 1.1


def test_use_item_with_oran_berry(clean_store):
    """Verifies use_item supports ItemKind.ORAN_BERRY."""
    store = clean_store
    store.inventory[ItemKind.ORAN_BERRY.value] = 1
    store.active.friendship = 50

    success = store.use_item(ItemKind.ORAN_BERRY)
    assert success is True
    assert store.inventory[ItemKind.ORAN_BERRY.value] == 0
    assert store.active.friendship == 60


def test_buy_oran_berry(clean_store):
    """Verifies purchasing Oran Berry from shop deducts spendable tokens and adds item to bag."""
    store = clean_store
    store.spendable_tokens = 20_000_000
    store.inventory[ItemKind.ORAN_BERRY.value] = 0

    bought = store.buy_item(ItemKind.ORAN_BERRY)
    assert bought is True
    assert store.spendable_tokens == 15_000_000  # 20M - 5M
    assert store.inventory[ItemKind.ORAN_BERRY.value] == 1
