"""
Unit tests for data models, progression balance formulas, egg tiers, and item prices.
"""

import unittest

from core.models import EggTier, ItemKind, PokemonBalance, PokemonNature, Rarity


class TestModelsAndBalance(unittest.TestCase):
    def test_rarity_ranking_and_totals(self):
        """Tests that higher rarity tiers have strictly non-decreasing lifetime token requirements."""
        common_tot = PokemonBalance.graduation_total(Rarity.COMMON)
        uncommon_tot = PokemonBalance.graduation_total(Rarity.UNCOMMON)
        rare_tot = PokemonBalance.graduation_total(Rarity.RARE)
        legendary_tot = PokemonBalance.graduation_total(Rarity.LEGENDARY)

        self.assertEqual(common_tot, 250_000_000)
        self.assertEqual(uncommon_tot, 750_000_000)
        self.assertEqual(rare_tot, 2_000_000_000)
        self.assertEqual(legendary_tot, 5_000_000_000)
        self.assertTrue(common_tot < uncommon_tot < rare_tot < legendary_tot)

    def test_phase_threshold_progression_formula(self):
        """Tests that multi-stage evolution thresholds follow arithmetic series."""
        # 3-stage Uncommon line (e.g. Bulbasaur line, Total = 750M, Denom = 6)
        t1 = PokemonBalance.phase_threshold(Rarity.UNCOMMON, total_forms=3, stage_index=0)
        t2 = PokemonBalance.phase_threshold(Rarity.UNCOMMON, total_forms=3, stage_index=1)
        t3 = PokemonBalance.phase_threshold(Rarity.UNCOMMON, total_forms=3, stage_index=2)

        self.assertEqual(t1, 125_000_000)  # 750M * 1/6
        self.assertEqual(t2, 250_000_000)  # 750M * 2/6
        self.assertEqual(t3, 375_000_000)  # 750M * 3/6
        self.assertEqual(t1 + t2 + t3, 750_000_000)

        # Single stage Legendary line (e.g. Mewtwo, Total = 5B)
        t_single = PokemonBalance.phase_threshold(Rarity.LEGENDARY, total_forms=1, stage_index=0)
        self.assertEqual(t_single, 5_000_000_000)

    def test_egg_tiers_and_thresholds(self):
        """Tests egg incubation thresholds and purchase prices."""
        self.assertEqual(EggTier.STANDARD.hatch_threshold, 2_500_000)
        self.assertEqual(EggTier.UNCOMMON.hatch_threshold, 6_000_000)
        self.assertEqual(EggTier.RARE.hatch_threshold, 15_000_000)
        self.assertEqual(EggTier.LEGENDARY.hatch_threshold, 35_000_000)

        self.assertEqual(EggTier.STANDARD.price_tokens, 0)
        self.assertEqual(EggTier.UNCOMMON.price_tokens, 50_000_000)
        self.assertEqual(EggTier.RARE.price_tokens, 200_000_000)
        self.assertEqual(EggTier.LEGENDARY.price_tokens, 600_000_000)

    def test_item_kind_properties(self):
        """Tests items, descriptions, and economy prices."""
        self.assertEqual(ItemKind.RARE_CANDY.price_tokens, 25_000_000)
        self.assertEqual(ItemKind.MINT.price_tokens, 50_000_000)
        self.assertEqual(ItemKind.SHINY_CHARM.price_tokens, 500_000_000)
        self.assertEqual(ItemKind.RARE_CANDY.emoji, "🍬")
        self.assertEqual(ItemKind.MINT.emoji, "🌿")
        self.assertEqual(ItemKind.SHINY_CHARM.emoji, "✨")

    def test_pokemon_natures_enumeration(self):
        """Tests that all 25 canonical Pokémon natures exist."""
        self.assertEqual(len(PokemonNature), 25)
        self.assertIn(PokemonNature.ADAMANT, PokemonNature)
        self.assertIn(PokemonNature.MODEST, PokemonNature)
        self.assertIn(PokemonNature.JOLLY, PokemonNature)
        self.assertIn(PokemonNature.TIMID, PokemonNature)


if __name__ == "__main__":
    unittest.main()
