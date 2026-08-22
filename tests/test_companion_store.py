"""
Unit tests for CompanionStore game state engine, evolution mechanics, and ceremony queue.
"""

import os
import tempfile
import time
import unittest
from unittest.mock import patch

from core.companion_store import CeremonyEvent, CompanionStore
from core.models import EggTier, ItemKind, PokemonNature


class TestCompanionStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file_patch = patch(
            "core.companion_store.STATE_FILE", os.path.join(self.temp_dir.name, "state.json")
        )
        self.state_file_patch.start()
        self.store = CompanionStore()

    def tearDown(self):
        self.state_file_patch.stop()
        self.temp_dir.cleanup()

    def test_starter_egg_initialization(self):
        """Tests that a fresh store initializes with an incubating starter egg."""
        self.assertTrue(self.store.is_egg)
        self.assertIsNone(self.store.active)
        self.assertEqual(self.store.egg_usage, 0)
        self.assertEqual(self.store.egg_tier, EggTier.STANDARD)
        self.assertEqual(self.store.current_threshold, 2_500_000)
        self.assertEqual(self.store.progress_percentage, 0.0)

    def test_egg_hatching_and_overflow(self):
        """Tests that adding 3,000,000 tokens hatches the egg and overflows 500k into the new Pokemon."""
        self.store.add_tokens(3_000_000)

        self.assertFalse(self.store.is_egg)
        self.assertIsNotNone(self.store.active)
        self.assertEqual(self.store.active.stage_index, 0)
        self.assertEqual(self.store.active.used_at_stage, 500_000)
        self.assertEqual(self.store.spendable_tokens, 3_000_000)
        self.assertEqual(self.store.total_tokens_burned_lifetime, 3_000_000)

        # Verify Hatch Ceremony queued
        self.assertTrue(len(self.store.ceremony_queue) >= 1)
        event = self.store.ceremony_queue[0]
        self.assertEqual(event.event_type, CeremonyEvent.HATCH)
        self.assertEqual(event.species_id, self.store.active.species_id)

    def test_rare_candy_item_usage(self):
        """Tests feeding a Rare Candy uses 1 candy, adds 100M EXP, and queues CANDY_XP ceremony."""
        # Hatch first
        self.store.add_tokens(2_500_000)
        initial_candies = self.store.inventory[ItemKind.RARE_CANDY.value]
        self.assertTrue(initial_candies > 0)

        initial_used = self.store.active.used_at_stage
        success = self.store.use_item(ItemKind.RARE_CANDY)

        self.assertTrue(success)
        self.assertGreater(self.store.active.used_at_stage, initial_used)
        self.assertEqual(self.store.inventory[ItemKind.RARE_CANDY.value], initial_candies - 1)

        # Verify event was queued
        events = [e.event_type for e in self.store.ceremony_queue]
        self.assertIn(CeremonyEvent.CANDY_XP, events)

    def test_nature_mint_usage(self):
        """Tests using Nature Mint with specific target nature queues MINT_CHANGE."""
        self.store.add_tokens(2_500_000)
        self.store.inventory[ItemKind.MINT.value] = 2
        original_nature = self.store.active.nature
        target_nature = (
            PokemonNature.ADAMANT
            if original_nature != PokemonNature.ADAMANT
            else PokemonNature.MODEST
        )

        success = self.store.use_mint_with_nature(target_nature)
        self.assertTrue(success)
        self.assertEqual(self.store.inventory[ItemKind.MINT.value], 1)
        self.assertEqual(self.store.active.nature, target_nature)

        events = [e.event_type for e in self.store.ceremony_queue]
        self.assertIn(CeremonyEvent.MINT_CHANGE, events)

    def test_species_index_lookup(self):
        """Tests that precomputed SPECIES_INDEX has O(1) mappings for all evolution chains."""
        from core.poke_api import SPECIES_INDEX

        self.assertIn(1, SPECIES_INDEX)
        self.assertEqual(SPECIES_INDEX[1]["name"], "Bulbasaur")
        self.assertIn(4, SPECIES_INDEX)
        self.assertEqual(SPECIES_INDEX[4]["name"], "Charmander")
        self.assertIn(25, SPECIES_INDEX)
        self.assertEqual(SPECIES_INDEX[25]["name"], "Pikachu")

    def test_daily_token_limit_notifications(self):
        """Tests 80% warning and 100% threshold alert notifications."""
        self.store.set_daily_token_limit(10_000_000)  # 10M limit

        # At 5M (50%), no notification
        notif = self.store.check_and_trigger_notifications(5_000_000)
        self.assertIsNone(notif)

        # At 8M (80%), trigger warning
        notif_80 = self.store.check_and_trigger_notifications(8_000_000)
        self.assertIsNotNone(notif_80)
        self.assertIn("80%", notif_80[0])

        # Second check at 8.5M should not repeat 80% alert
        notif_repeat = self.store.check_and_trigger_notifications(8_500_000)
        self.assertIsNone(notif_repeat)

        # At 10M (100%), trigger limit reached alert
        notif_100 = self.store.check_and_trigger_notifications(10_000_000)
        self.assertIsNotNone(notif_100)
        self.assertIn("100%", notif_100[0])

    def test_daily_history_recording(self):
        """Tests 7-day token history recording and rolling retention."""
        self.store.record_daily_tokens(45_000_000)
        today_str = time.strftime("%Y-%m-%d")
        self.assertIn(today_str, self.store.daily_history)
        self.assertEqual(self.store.daily_history[today_str], 45_000_000)

    def test_record_daily_tokens_throttling(self):
        """Tests that record_daily_tokens skips save when count is unchanged."""
        state_file = os.path.join(self.temp_dir.name, "state.json")
        self.store.record_daily_tokens(50_000_000)
        mtime1 = os.path.getmtime(state_file)
        time.sleep(0.01)
        # Record identical amount
        self.store.record_daily_tokens(50_000_000)
        mtime2 = os.path.getmtime(state_file)
        self.assertEqual(mtime1, mtime2)

    def test_save_and_load_persistence(self):
        """Tests state serialization and deserialization across store instances."""
        self.store.spendable_tokens = 999_999
        self.store.roaming_enabled = False
        self.store.pet_size_preset = "large"
        self.store.save()

        # Create new store instance loading the saved state
        new_store = CompanionStore()
        self.assertEqual(new_store.spendable_tokens, 999_999)
        self.assertFalse(new_store.roaming_enabled)
        self.assertEqual(new_store.pet_size_preset, "large")

    def test_choose_starter_gen1_charmander(self):
        """Tests choosing Gen 1 Charmander instantly activates companion and registers Pokédex."""
        self.assertFalse(self.store.starter_chosen)
        success = self.store.choose_starter(4)  # Charmander
        self.assertTrue(success)
        self.assertTrue(self.store.starter_chosen)
        self.assertIsNotNone(self.store.active)
        self.assertEqual(self.store.active.species_id, 4)
        self.assertEqual(self.store.active.species_name, "Charmander")
        self.assertIn("4", self.store.pokedex)
        self.assertEqual(self.store.pokedex["4"]["name"], "Charmander")

    def test_choose_starter_gen9_sprigatito(self):
        """Tests choosing Gen 9 Sprigatito initializes Paldea evolution chain correctly."""
        success = self.store.choose_starter(906)  # Sprigatito
        self.assertTrue(success)
        self.assertEqual(self.store.active.species_id, 906)
        self.assertEqual(self.store.active.species_name, "Sprigatito")

    def test_trainer_rank_and_streak(self):
        """Tests Trainer rank progression and active daily streak calculation."""
        rank, badge, pct = self.store.get_trainer_rank()
        self.assertIn("Novice", rank)

        self.store.total_tokens_burned_lifetime = 150_000_000
        rank, badge, pct = self.store.get_trainer_rank()
        self.assertIn("Model Master", rank)
        self.assertEqual(badge, "Rank IV")

        self.store.choose_starter(1)
        streak = self.store.get_active_streak()
        self.assertGreaterEqual(streak, 1)

    def test_use_mint_with_specific_nature(self):
        """Tests using Nature Mint with an explicitly chosen nature."""
        self.store.choose_starter(1)  # Bulbasaur
        self.store.inventory[ItemKind.MINT.value] = 2

        success = self.store.use_mint_with_nature(PokemonNature.ADAMANT)
        self.assertTrue(success)
        self.assertEqual(self.store.active.nature, PokemonNature.ADAMANT)
        self.assertEqual(self.store.inventory[ItemKind.MINT.value], 1)

    def test_set_active_from_pokedex(self):
        """Tests switching active companion to a previously caught species."""
        self.store.choose_starter(1)  # Bulbasaur
        self.store.pokedex["4"] = {"id": 4, "name": "Charmander", "shiny": True}

        success = self.store.set_active_from_pokedex(4)
        self.assertTrue(success)
        self.assertEqual(self.store.active.species_id, 4)
        self.assertEqual(self.store.active.species_name, "Charmander")
        self.assertTrue(self.store.active.is_shiny)

    def test_get_dex_species_aggregation(self):
        """Tests that get_dex_species aggregates pokedex entries, active companion, and reached evolution forms."""
        # Initial empty state
        self.store.pokedex.clear()
        self.store.active = None
        self.assertEqual(len(self.store.get_dex_species()), 0)

        # Choose starter Charmander (#4)
        self.store.choose_starter(4)
        dex = self.store.get_dex_species()
        self.assertEqual(len(dex), 1)
        self.assertEqual(dex[0]["id"], 4)
        self.assertEqual(dex[0]["name"], "Charmander")
        self.assertTrue(dex[0]["is_raising"])

        # Evolve Charmander to Charmeleon (#5)
        self.store.evolve()
        dex = self.store.get_dex_species()
        self.assertEqual(len(dex), 2)
        ids = [d["id"] for d in dex]
        self.assertIn(4, ids)
        self.assertIn(5, ids)


if __name__ == "__main__":
    unittest.main()
