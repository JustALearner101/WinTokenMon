"""
Stability tests: atomic state save, corrupt-file recovery, and value clamping.
"""

import json

import pytest

from core.companion_store import CompanionStore


@pytest.fixture
def isolated_store(tmp_path, monkeypatch) -> CompanionStore:
    monkeypatch.setattr("core.companion_store.STATE_FILE", str(tmp_path / "state.json"))
    return CompanionStore()


def _minimal_active() -> dict:
    return {
        "species_id": 1,
        "species_name": "Bulbasaur",
        "stage_index": 0,
        "total_forms": 3,
        "used_at_stage": -5,
        "rarity": "uncommon",
        "nature": "Hardy",
        "is_shiny": False,
        "friendship": 150,
    }


def test_save_load_roundtrip(isolated_store):
    isolated_store.spendable_tokens = 123_456
    isolated_store.total_tokens_burned_lifetime = 999_999
    isolated_store.choose_starter(4)

    reloaded = CompanionStore()
    assert reloaded.active is not None
    assert reloaded.active.species_name == "Charmander"
    assert reloaded.spendable_tokens == 123_456
    assert reloaded.total_tokens_burned_lifetime == 999_999


def test_save_is_atomic_no_tmp_leftover(isolated_store, tmp_path):
    (tmp_path / "state.json.tmp").write_text("stale garbage", encoding="utf-8")
    isolated_store.save()

    assert not (tmp_path / "state.json.tmp").exists()
    assert json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))["spendable_tokens"] == 0


def test_backup_created_on_save(isolated_store, tmp_path):
    isolated_store.save()  # first save: no previous file to back up
    isolated_store.spendable_tokens = 42
    isolated_store.save()  # second save backs up the previous valid state

    bak = tmp_path / "state.json.bak"
    assert bak.exists()
    assert json.loads(bak.read_text(encoding="utf-8"))["spendable_tokens"] == 0


def test_corrupt_primary_recovers_from_backup(isolated_store, tmp_path):
    isolated_store.choose_starter(1)
    isolated_store.save()

    # Simulate a crash mid-write leaving a half-written primary file
    (tmp_path / "state.json").write_text('{ "spendable_tok', encoding="utf-8")

    reloaded = CompanionStore()
    assert reloaded.active is not None
    assert reloaded.active.species_name == "Bulbasaur"


def test_corrupt_state_quarantined_not_silently_overwritten(isolated_store, tmp_path):
    primary = tmp_path / "state.json"
    primary.write_text("not json at all", encoding="utf-8")

    fresh = CompanionStore()
    assert fresh.active is None
    assert fresh.spendable_tokens == 0

    quarantined = list(tmp_path.glob("state.json.corrupt-*"))
    assert len(quarantined) == 1
    assert quarantined[0].read_text(encoding="utf-8") == "not json at all"

    # A subsequent save writes a fresh valid file without touching the evidence
    fresh.save()
    json.loads(primary.read_text(encoding="utf-8"))
    assert len(list(tmp_path.glob("state.json.corrupt-*"))) == 1


def test_negative_values_clamped_on_load(isolated_store, tmp_path):
    payload = {
        "spendable_tokens": -500,
        "total_tokens_burned_lifetime": -1,
        "egg_usage": -10,
        "daily_token_limit": -99,
        "active": _minimal_active(),
    }
    (tmp_path / "state.json").write_text(json.dumps(payload), encoding="utf-8")

    store = CompanionStore()
    assert store.spendable_tokens == 0
    assert store.total_tokens_burned_lifetime == 0
    assert store.egg_usage == 0
    assert store.daily_token_limit == 0
    assert store.active.friendship == 100
    assert store.active.used_at_stage == 0


def test_invalid_egg_tier_falls_back_to_standard(isolated_store, tmp_path):
    payload = {"egg_tier": "ultra-mega-does-not-exist"}
    (tmp_path / "state.json").write_text(json.dumps(payload), encoding="utf-8")

    store = CompanionStore()
    assert store.egg_tier.value == "standard"


def test_non_object_root_uses_defaults(isolated_store, tmp_path):
    (tmp_path / "state.json").write_text("[1, 2, 3]", encoding="utf-8")

    store = CompanionStore()
    assert store.active is None
    assert store.spendable_tokens == 0
