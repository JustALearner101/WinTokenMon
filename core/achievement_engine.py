"""
Developer Achievements & Badges Engine for WinTokenMon Windows (v0.2.0)
Evaluates token consumption behaviors and game events in real-time.
"""

import time
from collections import deque
from typing import Any

from .companion_store import CompanionStore
from .models import ACHIEVEMENT_DEFINITIONS, AchievementDef
from .token_reader import TokenUsageSummary


class AchievementEngine:
    def __init__(self, store: CompanionStore):
        self.store = store
        # Time-based burst window: deque of (timestamp, delta)
        self.token_burst_window: deque[tuple[float, int]] = deque()

        # Connect callbacks from CompanionStore
        self.store.on_hatch_callbacks.append(self._handle_hatch_event)
        self.store.on_graduate_callbacks.append(self._handle_graduate_event)

    def on_token_poll(self, delta: int, summary: TokenUsageSummary) -> list[AchievementDef]:
        """
        Evaluates token-related achievements on every polling tick.
        Returns a list of newly unlocked AchievementDef instances.
        """
        now = time.time()
        unlocked: list[AchievementDef] = []

        if delta > 0:
            self.token_burst_window.append((now, delta))

        # Prune entries older than 1 hour (3600 seconds)
        cutoff = now - 3600
        while self.token_burst_window and self.token_burst_window[0][0] < cutoff:
            self.token_burst_window.popleft()

        # 1. Night Owl Coder (00:00 - 05:00 local time)
        if "night_owl" not in self.store.unlocked_achievements:
            now_local = time.localtime(now)
            if 0 <= now_local.tm_hour < 5:
                if delta >= 100_000 or summary.today_tokens >= 100_000:
                    if self.store.unlock_achievement("night_owl"):
                        unlocked.append(ACHIEVEMENT_DEFINITIONS["night_owl"])

        # 2. Token Overclock (>1M tokens in 1-hour rolling window)
        if "overclock" not in self.store.unlocked_achievements:
            rolling_1h_tokens = sum(d for t, d in self.token_burst_window if t >= cutoff)
            if rolling_1h_tokens >= 1_000_000:
                if self.store.unlock_achievement("overclock"):
                    unlocked.append(ACHIEVEMENT_DEFINITIONS["overclock"])

        # 3. Multi-Tool Wizard (3+ AI tools in a single day)
        if "multi_tool" not in self.store.unlocked_achievements:
            active_tools_today = [src for src, tok in summary.by_source_today.items() if tok > 0]
            if len(active_tools_today) >= 3:
                if self.store.unlock_achievement("multi_tool"):
                    unlocked.append(ACHIEVEMENT_DEFINITIONS["multi_tool"])

        # 4. 100M Burn Club (100M total lifetime tokens burned)
        if "100m_burn_club" not in self.store.unlocked_achievements:
            if self.store.total_tokens_burned_lifetime >= 100_000_000:
                if self.store.unlock_achievement("100m_burn_club"):
                    unlocked.append(ACHIEVEMENT_DEFINITIONS["100m_burn_club"])

        return unlocked

    def _handle_hatch_event(self, active_pokemon):
        """Callback handler when an egg hatches."""
        # First Hatch
        if "first_hatch" not in self.store.unlocked_achievements:
            self.store.unlock_achievement("first_hatch")

        # Shiny Hunter
        if active_pokemon and active_pokemon.is_shiny:
            if "shiny_hunter" not in self.store.unlocked_achievements:
                self.store.unlock_achievement("shiny_hunter")

    def _handle_graduate_event(self, graduated_pokemon):
        """Callback handler when a companion graduates."""
        # Senior Professor (5 graduated companions)
        if "senior_professor" not in self.store.unlocked_achievements:
            if len(self.store.catch_log) >= 5:
                self.store.unlock_achievement("senior_professor")

    def get_trophies_overview(self) -> list[dict[str, Any]]:
        """
        Returns a rich list of all achievements with unlock status and progress calculation.
        """
        overview = []
        now = time.time()
        cutoff = now - 3600
        rolling_1h = sum(d for t, d in self.token_burst_window if t >= cutoff)

        for badge_id, defn in ACHIEVEMENT_DEFINITIONS.items():
            is_unlocked = badge_id in self.store.unlocked_achievements
            unlocked_at = self.store.unlocked_achievements.get(badge_id)

            progress_pct = 1.0 if is_unlocked else 0.0
            progress_label = "Completed" if is_unlocked else "Locked"

            if not is_unlocked:
                if badge_id == "100m_burn_club":
                    curr = self.store.total_tokens_burned_lifetime
                    progress_pct = min(1.0, curr / 100_000_000)
                    progress_label = f"{curr / 1_000_000:.1f}M / 100M ({progress_pct * 100:.0f}%)"
                elif badge_id == "senior_professor":
                    curr = len(self.store.catch_log)
                    progress_pct = min(1.0, curr / 5)
                    progress_label = f"{curr} / 5 Graduates"
                elif badge_id == "egg_hoarder":
                    owned = set(self.store.purchased_egg_tiers) & {"uncommon", "rare", "legendary"}
                    progress_pct = len(owned) / 3.0
                    progress_label = f"{len(owned)} / 3 Egg Tiers"
                elif badge_id == "overclock":
                    progress_pct = min(1.0, rolling_1h / 1_000_000)
                    progress_label = f"{rolling_1h / 1_000_000:.2f}M / 1.0M (1h)"
                elif badge_id == "first_hatch":
                    progress_label = "Hatch any egg"
                elif badge_id == "shiny_hunter":
                    progress_label = "Hatch a shiny variant"
                elif badge_id == "night_owl":
                    progress_label = "Code between 00:00 - 05:00"
                elif badge_id == "multi_tool":
                    progress_label = "Use 3+ AI tools today"

            reward_desc = ""
            if defn.reward_tokens > 0:
                reward_desc = f"+{defn.reward_tokens / 1_000_000:.0f}M Tokens"
            if defn.reward_item:
                count_str = f"{defn.reward_item_count}x " if defn.reward_item_count > 1 else ""
                reward_desc = f"{count_str}{defn.reward_item.title}"

            overview.append(
                {
                    "id": defn.id,
                    "title": defn.title,
                    "description": defn.description,
                    "tier": defn.tier,
                    "tier_title": defn.tier.title,
                    "tier_color": defn.tier.color_hex,
                    "icon_emoji": defn.icon_emoji,
                    "category": defn.category,
                    "reward_desc": reward_desc,
                    "reward_tokens": defn.reward_tokens,
                    "reward_item": defn.reward_item,
                    "is_unlocked": is_unlocked,
                    "unlocked_at": unlocked_at,
                    "progress_pct": progress_pct,
                    "progress_label": progress_label,
                }
            )

        return overview
