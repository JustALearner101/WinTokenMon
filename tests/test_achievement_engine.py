"""
Unit tests for Developer Achievements & Badges Engine (v0.2.0)
"""

from core.achievement_engine import AchievementEngine
from core.companion_store import CompanionStore
from core.models import EggTier, ItemKind
from core.token_reader import TokenUsageSummary


class TestAchievementEngine:
    def _create_isolated_store(self, tmp_path, monkeypatch) -> CompanionStore:
        fake_state = tmp_path / "state.json"
        monkeypatch.setattr("core.companion_store.STATE_FILE", str(fake_state))
        store = CompanionStore()
        # Clear out state
        store.active = None
        store.pokedex = {}
        store.catch_log = []
        store.unlocked_achievements = {}
        store.purchased_egg_tiers = []
        store.total_hatches = 0
        store.spendable_tokens = 0
        store.total_tokens_burned_lifetime = 0
        return store

    def test_starter_selection_does_not_unlock_first_hatch(self, tmp_path, monkeypatch):
        store = self._create_isolated_store(tmp_path, monkeypatch)
        _engine = AchievementEngine(store)

        # Choose starter (Bulbasaur #1)
        store.choose_starter(1)
        assert store.active is not None
        assert store.active.species_name == "Bulbasaur"
        # First hatch should NOT be unlocked
        assert "first_hatch" not in store.unlocked_achievements
        assert store.total_hatches == 0

    def test_first_hatch_unlocked_on_egg_hatch(self, tmp_path, monkeypatch):
        store = self._create_isolated_store(tmp_path, monkeypatch)
        _engine = AchievementEngine(store)

        assert "first_hatch" not in store.unlocked_achievements
        store.hatch_egg()

        assert "first_hatch" in store.unlocked_achievements
        assert store.total_hatches == 1
        # Reward: 10M spendable tokens
        assert store.spendable_tokens >= 10_000_000

    def test_multi_tool_wizard_requires_three_sources_today(self, tmp_path, monkeypatch):
        store = self._create_isolated_store(tmp_path, monkeypatch)
        engine = AchievementEngine(store)

        summary = TokenUsageSummary()
        summary.by_source_today = {"claude": 5000, "cursor": 3000}
        engine.on_token_poll(delta=8000, summary=summary)
        assert "multi_tool" not in store.unlocked_achievements

        # Add third tool
        summary.by_source_today["antigravity"] = 4000
        engine.on_token_poll(delta=4000, summary=summary)
        assert "multi_tool" in store.unlocked_achievements
        # Reward: 2 Nature Mints
        assert store.inventory.get(ItemKind.MINT.value, 0) >= 2

    def test_egg_hoarder_requires_all_paid_tiers(self, tmp_path, monkeypatch):
        store = self._create_isolated_store(tmp_path, monkeypatch)
        engine = AchievementEngine(store)

        store.spendable_tokens = 1_000_000_000

        store.buy_egg(EggTier.UNCOMMON)
        engine.on_game_event("BUY_EGG")
        assert "egg_hoarder" not in store.unlocked_achievements

        store.buy_egg(EggTier.RARE)
        engine.on_game_event("BUY_EGG")
        assert "egg_hoarder" not in store.unlocked_achievements

        store.buy_egg(EggTier.LEGENDARY)
        engine.on_game_event("BUY_EGG")
        assert "egg_hoarder" in store.unlocked_achievements
        # Reward: 50M tokens
        assert "egg_hoarder" in store.unlocked_achievements

    def test_overclock_time_based_burst_window(self, tmp_path, monkeypatch):
        store = self._create_isolated_store(tmp_path, monkeypatch)
        engine = AchievementEngine(store)

        summary = TokenUsageSummary()

        # Simulate 600k tokens now
        engine.on_token_poll(delta=600_000, summary=summary)
        assert "overclock" not in store.unlocked_achievements

        # Simulate another 500k tokens within the hour
        engine.on_token_poll(delta=500_000, summary=summary)
        assert "overclock" in store.unlocked_achievements
        # Reward: 1x Rare Candy
        assert store.inventory.get(ItemKind.RARE_CANDY.value, 0) >= 2

    def test_100m_burn_club_and_rewards(self, tmp_path, monkeypatch):
        store = self._create_isolated_store(tmp_path, monkeypatch)
        engine = AchievementEngine(store)

        summary = TokenUsageSummary()
        store.total_tokens_burned_lifetime = 99_000_000
        engine.on_token_poll(delta=500_000, summary=summary)
        assert "100m_burn_club" not in store.unlocked_achievements

        store.total_tokens_burned_lifetime = 100_000_000
        engine.on_token_poll(delta=500_000, summary=summary)
        assert "100m_burn_club" in store.unlocked_achievements
        assert store.spendable_tokens >= 25_000_000

    def test_achievement_idempotency_and_no_double_rewards(self, tmp_path, monkeypatch):
        store = self._create_isolated_store(tmp_path, monkeypatch)
        store.spendable_tokens = 0

        # First unlock
        res1 = store.unlock_achievement("first_hatch")
        assert res1 is True
        initial_tokens = store.spendable_tokens
        assert initial_tokens == 10_000_000

        # Second unlock attempt
        res2 = store.unlock_achievement("first_hatch")
        assert res2 is False
        assert store.spendable_tokens == initial_tokens

    def test_retro_migration_for_existing_users(self, tmp_path, monkeypatch):
        fake_state = tmp_path / "state.json"
        monkeypatch.setattr("core.companion_store.STATE_FILE", str(fake_state))

        # Create a legacy state file with 120M lifetime tokens and 6 catches
        legacy_data = {
            "total_tokens_burned_lifetime": 120_000_000,
            "catch_log": [
                {"species_id": 1},
                {"species_id": 4},
                {"species_id": 7},
                {"species_id": 25},
                {"species_id": 133},
                {"species_id": 152},
            ],
            "pokedex": {"1": {"name": "Bulbasaur", "shiny": True}},
        }
        import json

        with open(fake_state, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        store = CompanionStore()
        assert "100m_burn_club" in store.unlocked_achievements
        assert "first_hatch" in store.unlocked_achievements
        assert "shiny_hunter" in store.unlocked_achievements
        assert "senior_professor" in store.unlocked_achievements

    def test_trophies_overview_metadata(self, tmp_path, monkeypatch):
        store = self._create_isolated_store(tmp_path, monkeypatch)
        engine = AchievementEngine(store)

        overview = engine.get_trophies_overview()
        assert len(overview) == 8
        for item in overview:
            assert "id" in item
            assert "title" in item
            assert "tier_color" in item
            assert "progress_pct" in item
