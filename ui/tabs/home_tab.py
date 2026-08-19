"""
Home & Companion Trainer HUD Tab for WinTokenMon Dashboard
Featuring Pokémon RPG Showcase, Evolution Lineage Trail, Lore Quotes,
and Developer Token Insights Grid.
"""

import tkinter as tk
from datetime import datetime, timedelta

import customtkinter as ctk

from core.audio_manager import play_sfx_levelup
from core.companion_store import CompanionStore
from core.models import ItemKind, PokemonNature
from core.poke_api import SPECIES_INDEX
from core.token_reader import TokenUsageSummary
from ui.dashboard_theme import (
    NATURE_DETAILS,
    POKEMON_LORE,
    TYPE_THEMES,
    get_pokemon_element_type,
)
from ui.desktop_pet import create_egg_image, format_tokens
from ui.modals.nature_modal import NatureSelectorModal


class HomeTabView:
    """Manages the Companion & Trainer HUD tab view and daily burn history chart."""

    def __init__(self, parent: ctk.CTkFrame, dashboard):
        self.parent = parent
        self.dashboard = dashboard
        self.store: CompanionStore = dashboard.store

        self._build_ui()

    @property
    def summary(self) -> TokenUsageSummary:
        return self.dashboard.summary

    def _build_ui(self):
        # 1. Trainer Profile Ribbon (Top Banner)
        self.trainer_ribbon = ctk.CTkFrame(
            self.parent,
            corner_radius=10,
            fg_color="#181825",
            border_width=1,
            border_color="#2A2F3D",
        )
        self.trainer_ribbon.pack(fill="x", padx=6, pady=(2, 6))

        self.lbl_trainer_rank = ctk.CTkLabel(
            self.trainer_ribbon,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#F1C40F",
        )
        self.lbl_trainer_rank.pack(side="left", padx=14, pady=6)

        self.lbl_trainer_streak = ctk.CTkLabel(
            self.trainer_ribbon,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#E67E22",
        )
        self.lbl_trainer_streak.pack(side="left", padx=14, pady=6)

        self.lbl_trainer_dex = ctk.CTkLabel(
            self.trainer_ribbon,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#89B4FA",
        )
        self.lbl_trainer_dex.pack(side="right", padx=14, pady=6)

        # 2. Main 2-Column Grid Split
        self.hud_body = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.hud_body.pack(fill="both", expand=True)
        self.hud_body.rowconfigure(0, weight=1)
        self.hud_body.columnconfigure(0, weight=5)  # Left Card: Companion RPG
        self.hud_body.columnconfigure(1, weight=6)  # Right Card: Token Analytics

        # =========================================================================
        # LEFT COLUMN: COMPANION RPG SHOWCASE CARD
        # =========================================================================
        self.card_companion = ctk.CTkFrame(self.hud_body, corner_radius=12, border_width=2)
        self.card_companion.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")

        # Header Title
        self.lbl_comp_title = ctk.CTkLabel(
            self.card_companion,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
        )
        self.lbl_comp_title.pack(pady=(6, 2))

        # Badges Row (Type Pill, Stage Pill, Nature Pill)
        self.badges_frame = ctk.CTkFrame(self.card_companion, fg_color="transparent")
        self.badges_frame.pack(pady=(0, 6))

        self.lbl_type_pill = ctk.CTkLabel(
            self.badges_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            corner_radius=6,
            padx=8,
            pady=2,
        )
        self.lbl_type_pill.pack(side="left", padx=3)

        self.lbl_stage_pill = ctk.CTkLabel(
            self.badges_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#21262D",
            text_color="#89B4FA",
            corner_radius=6,
            padx=8,
            pady=2,
        )
        self.lbl_stage_pill.pack(side="left", padx=3)

        self.lbl_nature_pill = ctk.CTkLabel(
            self.badges_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#21262D",
            text_color="#E0AF68",
            corner_radius=6,
            padx=8,
            pady=2,
        )
        self.lbl_nature_pill.pack(side="left", padx=3)

        # Sprite Centerpiece Container
        self.sprite_box = ctk.CTkFrame(
            self.card_companion,
            fg_color="#10131A",
            corner_radius=12,
            border_width=1,
            border_color="#1E2330",
        )
        self.sprite_box.pack(fill="x", padx=12, pady=4)

        self.lbl_sprite = ctk.CTkLabel(self.sprite_box, text="")
        self.lbl_sprite.pack(pady=8)

        # Pokédex Lore / Flavor Quote Box
        self.lore_box = ctk.CTkFrame(
            self.card_companion,
            fg_color="#141822",
            corner_radius=8,
            border_width=1,
            border_color="#222838",
        )
        self.lore_box.pack(fill="x", padx=12, pady=(4, 6))

        self.lbl_lore_quote = ctk.CTkLabel(
            self.lore_box,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10, slant="italic"),
            text_color="#A6ADC8",
            wraplength=280,
            justify="center",
        )
        self.lbl_lore_quote.pack(padx=10, pady=6)

        # Evolution Lineage Trail Frame
        self.trail_card = ctk.CTkFrame(
            self.card_companion,
            fg_color="#12151E",
            corner_radius=8,
            border_width=1,
            border_color="#1E2330",
        )
        self.trail_card.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(
            self.trail_card,
            text="🧬 Evolution Lineage",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#89B4FA",
        ).pack(anchor="w", padx=8, pady=(4, 2))

        self.trail_inner = ctk.CTkFrame(self.trail_card, fg_color="transparent")
        self.trail_inner.pack(fill="x", padx=6, pady=(0, 6))

        # RPG Evolution EXP Gauge
        self.lbl_progress_text = ctk.CTkLabel(
            self.card_companion,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        )
        self.lbl_progress_text.pack(pady=(2, 2))

        self.progress_bar = ctk.CTkProgressBar(self.card_companion, height=10, corner_radius=5)
        self.progress_bar.pack(fill="x", padx=12, pady=(0, 6))

        # Daily Activity Gauge
        self.lbl_stamina_text = ctk.CTkLabel(
            self.card_companion,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="gray70",
        )
        self.lbl_stamina_text.pack(pady=(0, 2))

        self.stamina_bar = ctk.CTkProgressBar(
            self.card_companion, height=6, corner_radius=3, progress_color="#3498DB"
        )
        self.stamina_bar.pack(fill="x", padx=12, pady=(0, 4))

        # Friendship / Affection Gauge
        self.lbl_friendship_text = ctk.CTkLabel(
            self.card_companion,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#F472B6",
        )
        self.lbl_friendship_text.pack(pady=(0, 2))

        self.friendship_bar = ctk.CTkProgressBar(
            self.card_companion, height=6, corner_radius=3, progress_color="#EC4899"
        )
        self.friendship_bar.pack(fill="x", padx=12, pady=(0, 8))

        # Quick Actions Grid (3-Column Layout)
        self.actions_grid = ctk.CTkFrame(self.card_companion, fg_color="transparent")
        self.actions_grid.pack(fill="x", padx=8, pady=(0, 6))
        self.actions_grid.columnconfigure(0, weight=1)
        self.actions_grid.columnconfigure(1, weight=1)
        self.actions_grid.columnconfigure(2, weight=1)

        self.btn_use_candy = ctk.CTkButton(
            self.actions_grid,
            text="🍬 Candy",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self.action_use_candy,
            height=28,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
        )
        self.btn_use_candy.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        self.btn_use_berry = ctk.CTkButton(
            self.actions_grid,
            text="🫐 Berry",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self.action_use_berry,
            height=28,
            fg_color="#7C3AED",
            hover_color="#6D28D9",
        )
        self.btn_use_berry.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        self.btn_use_mint = ctk.CTkButton(
            self.actions_grid,
            text="🌿 Mint",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self.action_open_mint_picker,
            height=28,
            fg_color="#059669",
            hover_color="#047857",
        )
        self.btn_use_mint.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        # =========================================================================
        # RIGHT COLUMN: DEVELOPER TOKEN ANALYTICS & INSIGHTS
        # =========================================================================
        self.card_stats = ctk.CTkScrollableFrame(self.hud_body, corner_radius=12)
        self.card_stats.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")

        # 1. Today's Burn Hero Card
        self.today_hero = ctk.CTkFrame(
            self.card_stats,
            fg_color="#181B24",
            corner_radius=10,
            border_width=1,
            border_color="#2A2F3D",
        )
        self.today_hero.pack(fill="x", padx=4, pady=(2, 6))

        self.lbl_today_total = ctk.CTkLabel(
            self.today_hero,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#FFFFFF",
        )
        self.lbl_today_total.pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_today_breakdown = ctk.CTkLabel(
            self.today_hero,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#9CA3AF",
        )
        self.lbl_today_breakdown.pack(anchor="w", padx=12, pady=(0, 8))

        # 2. 2x2 Quick Insights Mini-Cards Grid
        self.insights_grid = ctk.CTkFrame(self.card_stats, fg_color="transparent")
        self.insights_grid.pack(fill="x", padx=2, pady=(0, 6))
        self.insights_grid.columnconfigure(0, weight=1)
        self.insights_grid.columnconfigure(1, weight=1)

        # Card: Last 5 Hours
        self.card_5h = self._create_mini_insight_card(self.insights_grid, "⏱️ Last 5 Hours")
        self.card_5h.grid(row=0, column=0, padx=3, pady=3, sticky="nsew")
        self.lbl_5h_val = ctk.CTkLabel(
            self.card_5h,
            text="0",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#60A5FA",
        )
        self.lbl_5h_val.pack(anchor="w", padx=10, pady=(0, 6))

        # Card: Past 7 Days
        self.card_7d = self._create_mini_insight_card(self.insights_grid, "📅 Past 7 Days")
        self.card_7d.grid(row=0, column=1, padx=3, pady=3, sticky="nsew")
        self.lbl_7d_val = ctk.CTkLabel(
            self.card_7d,
            text="0",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#34D399",
        )
        self.lbl_7d_val.pack(anchor="w", padx=10, pady=(0, 6))

        # Card: Lifetime Burn
        self.card_life = self._create_mini_insight_card(self.insights_grid, "💎 Lifetime Total")
        self.card_life.grid(row=1, column=0, padx=3, pady=3, sticky="nsew")
        self.lbl_life_val = ctk.CTkLabel(
            self.card_life,
            text="0",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FBBF24",
        )
        self.lbl_life_val.pack(anchor="w", padx=10, pady=(0, 6))

        # Card: Active Streak
        self.card_strk = self._create_mini_insight_card(self.insights_grid, "🔥 Active Streak")
        self.card_strk.grid(row=1, column=1, padx=3, pady=3, sticky="nsew")
        self.lbl_strk_val = ctk.CTkLabel(
            self.card_strk,
            text="0",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#F87171",
        )
        self.lbl_strk_val.pack(anchor="w", padx=10, pady=(0, 6))

        # 3. AI Assistant Breakdown Card
        self.tool_frame = ctk.CTkFrame(
            self.card_stats,
            fg_color="#181B24",
            corner_radius=10,
            border_width=1,
            border_color="#2A2F3D",
        )
        self.tool_frame.pack(fill="x", padx=4, pady=(0, 6))

        ctk.CTkLabel(
            self.tool_frame,
            text="🤖 AI Tools Distribution",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#CDD6F4",
        ).pack(anchor="w", padx=10, pady=(6, 4))

        self.tools_container = ctk.CTkFrame(self.tool_frame, fg_color="transparent")
        self.tools_container.pack(fill="x", padx=8, pady=(0, 8))

        # 4. 7-Day Burn History Activity Chart
        self.chart_frame = ctk.CTkFrame(
            self.card_stats,
            fg_color="#141822",
            corner_radius=10,
            border_width=1,
            border_color="#2A2F3D",
        )
        self.chart_frame.pack(fill="x", padx=4, pady=(0, 6))

        ctk.CTkLabel(
            self.chart_frame,
            text="📅 7-Day Burn History",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#CDD6F4",
        ).pack(anchor="w", padx=10, pady=(6, 2))

        self.chart_canvas = tk.Canvas(
            self.chart_frame, bg="#141822", highlightthickness=0, height=105
        )
        self.chart_canvas.pack(fill="x", padx=8, pady=(0, 6))

        self.refresh()

    def _create_mini_insight_card(self, parent, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color="#181B24", corner_radius=8, border_width=1, border_color="#2A2F3D"
        )
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#9CA3AF",
        ).pack(anchor="w", padx=10, pady=(6, 2))
        return card

    def _get_active_theme(self) -> dict:
        if self.store.is_egg or not self.store.active:
            return TYPE_THEMES["normal"]
        elem = get_pokemon_element_type(self.store.active.species_id)
        return TYPE_THEMES.get(elem, TYPE_THEMES["normal"])

    def refresh(self):
        theme = self._get_active_theme()

        # Update Trainer Ribbon
        rank_title, rank_badge, _ = self.store.get_trainer_rank()
        streak = self.store.get_active_streak()
        dex_count = len(self.store.pokedex)

        has_gold_badge = "100m_burn_club" in getattr(self.store, "unlocked_achievements", {})
        if has_gold_badge:
            self.lbl_trainer_rank.configure(
                text=f"👑 {rank_title} ({rank_badge}) ⭐ 100M ELITE",
                text_color="#F1C40F",
            )
            self.trainer_ribbon.configure(border_color="#F1C40F", border_width=2)
        else:
            self.lbl_trainer_rank.configure(
                text=f"🎖️ {rank_title} ({rank_badge})",
                text_color="#F1C40F",
            )
            self.trainer_ribbon.configure(border_color="#2A2F3D", border_width=1)

        self.lbl_trainer_streak.configure(text=f"🔥 {streak}-Day Streak")
        self.lbl_trainer_dex.configure(text=f"⭐ {dex_count}/30 Dex Caught")

        # Update Companion Card Background & Theme
        self.card_companion.configure(
            fg_color=theme["card_bg"],
            border_color=theme["border"],
        )

        # Clear evolution trail
        for w in self.trail_inner.winfo_children():
            w.destroy()

        if self.store.is_egg:
            self.lbl_comp_title.configure(text="🥚 Pokémon Egg", text_color="#CDD6F4")
            self.lbl_type_pill.configure(text="🥚 EGG", fg_color="#313244", text_color="#CDD6F4")
            self.lbl_stage_pill.configure(text=f"Tier: {self.store.egg_tier.value.capitalize()}")
            self.lbl_nature_pill.configure(text="Egg Incubation", text_color="#9CA3AF")

            egg_img = ctk.CTkImage(create_egg_image((100, 100)), size=(100, 100))
            self.lbl_sprite.configure(image=egg_img)

            self.lbl_lore_quote.configure(
                text="“An enigmatic Pokémon egg. Walk, code, and burn tokens to help it hatch into a new companion!”"
            )

            # Trail placeholder for egg
            egg_lbl = ctk.CTkLabel(
                self.trail_inner,
                text="🥚 Incubating Egg ➔ ??? Unknown Species",
                font=ctk.CTkFont(family="Segoe UI", size=10, slant="italic"),
                text_color="#9CA3AF",
            )
            egg_lbl.pack(pady=2)

            pct = self.store.progress_percentage
            self.progress_bar.configure(progress_color="#89B4FA")
            self.progress_bar.set(pct)
            self.lbl_progress_text.configure(
                text=f"Hatching: {format_tokens(self.store.egg_usage)} / {format_tokens(self.store.current_threshold)} ({pct * 100:.1f}%)"
            )
            self.lbl_friendship_text.configure(text="🥚 Affection: Available after hatching")
            self.friendship_bar.set(0.0)
            self.btn_use_candy.configure(state="disabled")
            self.btn_use_berry.configure(state="disabled")
            self.btn_use_mint.configure(state="disabled")
        else:
            act = self.store.active
            shiny_str = " ✨" if act.is_shiny else ""
            type_name = get_pokemon_element_type(act.species_id).upper()

            self.lbl_comp_title.configure(
                text=f"#{act.species_id:03d} {act.species_name}{shiny_str}",
                text_color=theme["primary"],
            )

            self.lbl_type_pill.configure(
                text=f"{theme['icon']} {type_name}",
                fg_color=theme["badge_bg"],
                text_color=theme["badge_text"],
            )
            self.lbl_stage_pill.configure(
                text=f"Form {act.stage_index + 1}/{act.total_forms}",
            )

            nature_bonus, _, _ = NATURE_DETAILS.get(act.nature, ("Balanced", "", ""))
            self.lbl_nature_pill.configure(
                text=f"⚡ {act.nature.value} ({nature_bonus.split('/')[0].strip()})",
            )

            # Sprite
            ctk_img = self.dashboard.get_cached_sprite(act.species_id, act.is_shiny, size=90)
            if ctk_img:
                self.lbl_sprite.configure(image=ctk_img)

            # Lore
            lore_text = POKEMON_LORE.get(
                act.species_id,
                f"A loyal {act.species_name} companion actively assisting your daily software development workflow.",
            )
            self.lbl_lore_quote.configure(text=f"“{lore_text}”")

            # Render Evolution Lineage Trail
            self._render_evolution_trail(act, theme)

            # EXP Progression
            pct = self.store.progress_percentage
            self.progress_bar.configure(progress_color=theme["primary"])
            self.progress_bar.set(pct)

            curr = act.used_at_stage
            thresh = self.store.current_threshold
            rem = max(0, thresh - curr)

            line_info = SPECIES_INDEX.get(act.species_id)
            if line_info and act.stage_index + 1 < len(line_info["names"]):
                next_name = line_info["names"][act.stage_index + 1]
                self.lbl_progress_text.configure(
                    text=f"Evolution EXP: {format_tokens(curr)} / {format_tokens(thresh)} ({pct * 100:.1f}% • {format_tokens(rem)} to {next_name})"
                )
            else:
                self.lbl_progress_text.configure(
                    text=f"Graduation EXP: {format_tokens(curr)} / {format_tokens(thresh)} ({pct * 100:.1f}%)"
                )

            # Affection / Friendship Bar
            f_pct = min(1.0, act.friendship / 100.0)
            self.friendship_bar.set(f_pct)
            f_badge = (
                "Devoted (⭐ +10% EXP Boost)"
                if act.friendship >= 80
                else ("Affectionate" if act.friendship >= 50 else "Timid")
            )
            self.lbl_friendship_text.configure(text=f"💖 Affection: {act.friendship}% • {f_badge}")

            self.btn_use_candy.configure(state="normal")
            self.btn_use_berry.configure(state="normal")
            self.btn_use_mint.configure(state="normal")

        # Daily Budget Stamina
        today_burned = self.summary.today_tokens
        limit = self.store.daily_token_limit
        stam_pct = min(1.0, today_burned / limit) if limit > 0 else 0.0

        if stam_pct >= 1.0:
            stam_col = "#E74C3C"
        elif stam_pct >= 0.8:
            stam_col = "#E67E22"
        else:
            stam_col = "#3498DB"

        self.stamina_bar.configure(progress_color=stam_col)
        self.stamina_bar.set(stam_pct)
        self.lbl_stamina_text.configure(
            text=f"⚡ Daily Stamina: {format_tokens(today_burned)} / {format_tokens(limit)} ({stam_pct * 100:.0f}%)"
        )

        # Bag Buttons Text
        candies = self.store.inventory.get(ItemKind.RARE_CANDY.value, 0)
        berries = self.store.inventory.get(ItemKind.ORAN_BERRY.value, 0)
        mints = self.store.inventory.get(ItemKind.MINT.value, 0)
        self.btn_use_candy.configure(text=f"🍬 Candy ({candies})")
        self.btn_use_berry.configure(text=f"🫐 Berry ({berries})")
        self.btn_use_mint.configure(text=f"🌿 Mint ({mints})")

        # Right Column Stats
        self.lbl_today_total.configure(
            text=f"⚡ {format_tokens(self.summary.today_tokens)} Tokens Burned Today"
        )
        self.lbl_today_breakdown.configure(
            text=f"📥 In: {format_tokens(self.summary.today_input)}  •  📤 Out: {format_tokens(self.summary.today_output)}  •  ⚡ Cache: {format_tokens(self.summary.today_cache)}"
        )

        # 2x2 Mini Insight values
        self.lbl_5h_val.configure(text=f"{format_tokens(self.summary.rolling_5h_tokens)} tokens")
        self.lbl_7d_val.configure(text=f"{format_tokens(self.summary.weekly_tokens)} tokens")
        self.lbl_life_val.configure(text=f"{format_tokens(self.summary.lifetime_tokens)} tokens")
        self.lbl_strk_val.configure(text=f"{streak} Days Active")

        # Render AI Tools Distribution
        self._render_ai_tools_distribution()

        # Render 7-Day Bar Chart
        self._render_history_chart()

    def _render_evolution_trail(self, act, theme):
        line_info = SPECIES_INDEX.get(act.species_id)
        if not line_info:
            return

        chain_ids = line_info.get("chain", [act.species_id])
        chain_names = line_info.get("names", [act.species_name])

        for idx, (sp_id, name) in enumerate(zip(chain_ids, chain_names)):
            is_current = sp_id == act.species_id

            badge_bg = theme["badge_bg"] if is_current else "#181C26"
            text_color = theme["primary"] if is_current else "#6B7280"
            border_col = theme["border"] if is_current else "#262C3A"
            border_w = 1 if is_current else 0

            stage_box = ctk.CTkFrame(
                self.trail_inner,
                fg_color=badge_bg,
                corner_radius=6,
                border_width=border_w,
                border_color=border_col,
            )
            stage_box.pack(side="left", padx=2, pady=1)

            stage_text = f"● #{sp_id} {name}" if is_current else f"○ {name}"
            ctk.CTkLabel(
                stage_box,
                text=stage_text,
                font=ctk.CTkFont(
                    family="Segoe UI", size=9, weight="bold" if is_current else "normal"
                ),
                text_color=text_color,
            ).pack(padx=6, pady=2)

            if idx < len(chain_ids) - 1:
                ctk.CTkLabel(
                    self.trail_inner,
                    text="➔",
                    font=ctk.CTkFont(family="Segoe UI", size=8),
                    text_color="#4B5563",
                ).pack(side="left", padx=1)

    def _render_ai_tools_distribution(self):
        for w in self.tools_container.winfo_children():
            w.destroy()

        by_src = self.summary.by_source
        total = self.summary.lifetime_tokens if self.summary.lifetime_tokens > 0 else 1

        tool_meta = {
            "antigravity": ("🟣 Antigravity CLI", "#AF52DE"),
            "claude": ("🟢 Claude Code", "#10B981"),
            "cursor": ("🔷 Cursor IDE", "#3B82F6"),
            "codex": ("🟩 Codex CLI", "#14B8A6"),
            "copilot": ("🐙 GitHub Copilot", "#6366F1"),
            "koma": ("⚡ Koma", "#F59E0B"),
        }

        active_tools = [(src, tok) for src, tok in by_src.items() if tok > 0]
        if not active_tools:
            ctk.CTkLabel(
                self.tools_container,
                text="No active token streams detected yet.",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#6B7280",
            ).pack(pady=4)
            return

        for src, tok in sorted(active_tools, key=lambda x: x[1], reverse=True):
            name, color = tool_meta.get(src, (f"🔹 {src.capitalize()}", "#89B4FA"))
            pct = (tok / total) * 100

            row = ctk.CTkFrame(self.tools_container, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=name,
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color="#CDD6F4",
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=f"{format_tokens(tok)} ({pct:.1f}%)",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=color,
            ).pack(side="right")

            # Mini Progress Bar
            pbar = ctk.CTkProgressBar(
                self.tools_container,
                height=4,
                corner_radius=2,
                progress_color=color,
                fg_color="#21262D",
            )
            pbar.set(min(1.0, pct / 100.0))
            pbar.pack(fill="x", pady=(0, 3))

    def _render_history_chart(self):
        """Draws the 7-day token history bar chart with peak record and average line."""
        self.chart_canvas.delete("all")
        today = datetime.now()
        days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        labels = [(today - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]

        history = dict(self.store.daily_history)
        history[days[-1]] = max(history.get(days[-1], 0), self.summary.today_tokens)

        values = [history.get(d, 0) for d in days]
        max_val = max(values) if max(values) > 0 else 1
        peak_idx = values.index(max(values)) if max(values) > 0 else -1

        theme = self._get_active_theme()
        bar_w = 26
        gap = 12
        start_x = 18
        chart_base_y = 86
        max_bar_h = 58

        for i, (val, lbl) in enumerate(zip(values, labels)):
            x = start_x + i * (bar_w + gap)
            bar_h = max(4, int(max_bar_h * val / max_val)) if val > 0 else 3
            y_top = chart_base_y - bar_h

            bar_color = theme["primary"] if i == 6 else ("#E67E22" if i == peak_idx else "#363A4F")
            self.chart_canvas.create_rectangle(
                x, y_top, x + bar_w, chart_base_y, fill=bar_color, outline=""
            )
            self.chart_canvas.create_text(
                x + bar_w // 2, chart_base_y + 10, text=lbl, fill="#A6ADC8", font=("Segoe UI", 8)
            )

            if val > 0:
                self.chart_canvas.create_text(
                    x + bar_w // 2,
                    max(10, y_top - 6),
                    text=format_tokens(val),
                    fill="#CDD6F4",
                    font=("Segoe UI", 7, "bold"),
                )

    def action_use_candy(self):
        if self.store.use_item(ItemKind.RARE_CANDY):
            play_sfx_levelup(0.6)
            self.dashboard.show_toast("🍬 Fed Rare Candy! +100M Token EXP & +15% Affection!")
            self.refresh()
            self.dashboard.refresh_pokedex_tab()
            self.dashboard.refresh_shop_tab()
            if self.dashboard.on_update_callback:
                self.dashboard.on_update_callback()
        else:
            self.dashboard.show_toast(
                "❌ No Rare Candies left in Bag! Buy one from Shop.",
                bg_color="#E74C3C",
                text_color="#FFF",
            )

    def action_use_berry(self):
        if self.store.use_item(ItemKind.ORAN_BERRY):
            play_sfx_levelup(0.5)
            self.dashboard.show_toast("🫐 Fed Oran Berry! +10M Token EXP & +10% Affection!")
            self.refresh()
            self.dashboard.refresh_pokedex_tab()
            self.dashboard.refresh_shop_tab()
            if self.dashboard.on_update_callback:
                self.dashboard.on_update_callback()
        else:
            self.dashboard.show_toast(
                "❌ No Oran Berries left in Bag! Buy one from Shop.",
                bg_color="#E74C3C",
                text_color="#FFF",
            )

    def action_open_mint_picker(self):
        mints = self.store.inventory.get(ItemKind.MINT.value, 0)
        if mints <= 0:
            self.dashboard.show_toast(
                "❌ No Nature Mints in Bag! Buy one from Shop.",
                bg_color="#E74C3C",
                text_color="#FFF",
            )
            return

        def on_pick(nature: PokemonNature):
            if self.store.use_mint_with_nature(nature):
                self.dashboard.show_toast(f"🌿 Nature successfully changed to {nature.value}!")
                self.refresh()
                self.dashboard.refresh_shop_tab()
                if self.dashboard.on_update_callback:
                    self.dashboard.on_update_callback()

        NatureSelectorModal(self.dashboard.win, on_pick)
