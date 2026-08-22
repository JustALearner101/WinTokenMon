"""
Unit tests for Evolution System and Developer Debug Helpers
"""

import pytest

from core.companion_store import CompanionStore
from core.models import EggTier, ItemKind


@pytest.fixture
def store(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr("core.companion_store.STATE_FILE", str(state_file))
    s = CompanionStore()
    s.load()
    return s


def test_starter_choice_and_ready_to_evolve(store):
    # Choose Treecko (ID 252)
    assert store.choose_starter(252, is_shiny=False)
    assert store.active.species_name == "Treecko"
    assert store.active.stage_index == 0
    assert not store.is_ready_to_evolve
    assert not store.is_final_stage

    next_info = store.next_species_info
    assert next_info is not None
    assert next_info[1] == "Grovyle"

    # Add tokens just below threshold
    thresh = store.current_threshold
    store.add_tokens(thresh - 100)
    assert not store.is_ready_to_evolve

    # Add tokens reaching threshold (auto_evolve is False by default)
    store.add_tokens(100)
    assert store.is_ready_to_evolve
    # Should still be Treecko waiting for manual trigger!
    assert store.active.species_name == "Treecko"

    # Now trigger manual evolve
    store.evolve()
    assert store.active.species_name == "Grovyle"
    assert store.active.stage_index == 1
    assert not store.is_ready_to_evolve


def test_auto_evolve_toggle(store):
    store.choose_starter(1, is_shiny=False)  # Bulbasaur
    store.auto_evolve_enabled = True
    assert store.active.species_name == "Bulbasaur"

    thresh = store.current_threshold
    store.add_tokens(thresh + 500)

    # Since auto_evolve_enabled is True, it automatically evolves to Ivysaur
    assert store.active.species_name == "Ivysaur"
    assert store.active.stage_index == 1
    assert store.active.used_at_stage >= 500  # Overflow EXP preserved!


def test_debug_methods(store):
    # 1. Debug set species
    assert store.debug_set_species(252, is_shiny=True, stage_index=1)
    assert store.active.species_name == "Grovyle"
    assert store.active.is_shiny is True

    # 2. Debug set friendship
    store.debug_set_friendship(95)
    assert store.active.friendship == 95

    # 3. Debug set progress pct
    store.debug_set_progress_pct(0.99)
    assert store.progress_percentage == pytest.approx(0.99, abs=0.01)

    # 4. Debug add all items
    store.debug_add_all_items(10)
    assert store.inventory[ItemKind.RARE_CANDY.value] >= 10
    assert store.inventory[ItemKind.SHINY_CHARM.value] == 1
    assert store.spendable_tokens >= 100_000_000

    # 5. Debug instant hatch
    store.debug_instant_hatch(EggTier.LEGENDARY)
    assert store.active is not None
    assert store.total_hatches >= 1

    # 6. Debug reset all
    store.debug_reset_all()
    assert store.active is None
    assert store.starter_chosen is False
    assert store.spendable_tokens == 0
