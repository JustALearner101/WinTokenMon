"""
Home & Companion Trainer HUD Tab for WinTokenMon Dashboard
"""

import tkinter as tk
from datetime import datetime, timedelta

import customtkinter as ctk

from core.audio_manager import play_sfx_levelup
from core.companion_store import CompanionStore
from core.models import ItemKind, PokemonNature
from core.poke_api import POKEMON_TYPES
from core.token_reader import TokenUsageSummary
from ui.dashboard_theme import TYPE_THEMES, get_pokemon_element_type
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
        self.trainer_ribbon = ctk.CTkFrame(self.parent, corner_radius=10, fg_color="#181825")
        self.trainer_ribbon.pack(fill="x", padx=6, pady=(2, 8))

        self.lbl_trainer_rank = ctk.CTkLabel(
            self.trainer_ribbon,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F1C40F",
        )
        self.lbl_trainer_rank.pack(side="left", padx=14, pady=8)

        self.lbl_trainer_streak = ctk.CTkLabel(
            self.trainer_ribbon,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#E67E22",
        )
        self.lbl_trainer_streak.pack(side="left", padx=14, pady=8)

        self.lbl_trainer_dex = ctk.CTkLabel(
            self.trainer_ribbon,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#89B4FA",
        )
        self.lbl_trainer_dex.pack(side="right", padx=14, pady=8)

        # 2-Column Split: Left (Companion Card), Right (Stats & Charts)
        self.hud_body = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.hud_body.pack(fill="both", expand=True)
        self.hud_body.columnconfigure(0, weight=1)
        self.hud_body.columnconfigure(1, weight=1)

        # Left Card: Companion Card with Dynamic Elemental Theme
        self.card_companion = ctk.CTkFrame(self.hud_body, corner_radius=12, border_width=2)
        self.card_companion.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        self.lbl_comp_title = ctk.CTkLabel(
            self.card_companion, text="", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_comp_title.pack(pady=(12, 2))

        self.lbl_comp_sub = ctk.CTkLabel(
            self.card_companion, text="", font=ctk.CTkFont(size=12), text_color="gray70"
        )
        self.lbl_comp_sub.pack(pady=(0, 6))

        self.lbl_sprite = ctk.CTkLabel(self.card_companion, text="")
        self.lbl_sprite.pack(pady=4)

        # RPG EXP Gauge
        self.lbl_progress_text = ctk.CTkLabel(
            self.card_companion, text="", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_progress_text.pack(pady=(4, 2))

        self.progress_bar = ctk.CTkProgressBar(self.card_companion, height=12)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 8))

        # RPG Daily Stamina/Budget Gauge
        self.lbl_stamina_text = ctk.CTkLabel(
            self.card_companion, text="", font=ctk.CTkFont(size=10), text_color="gray70"
        )
        self.lbl_stamina_text.pack(pady=(0, 2))

        self.stamina_bar = ctk.CTkProgressBar(self.card_companion, height=8, progress_color="#3498DB")
        self.stamina_bar.pack(fill="x", padx=20, pady=(0, 10))

        # Quick Actions
        self.quick_actions = ctk.CTkFrame(self.card_companion, fg_color="transparent")
        self.quick_actions.pack(fill="x", padx=16, pady=(0, 10))

        self.btn_use_candy = ctk.CTkButton(
            self.quick_actions,
            text="🍬 Feed Rare Candy (+100M)",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.action_use_candy,
            height=28,
        )
        self.btn_use_candy.pack(fill="x", pady=2)

        self.btn_use_mint = ctk.CTkButton(
            self.quick_actions,
            text="🌿 Choose Nature Mint",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.action_open_mint_picker,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            height=28,
        )
        self.btn_use_mint.pack(fill="x", pady=2)

        # Right Card: Token Activity, Breakdown & Chart (Scrollable)
        self.card_stats = ctk.CTkScrollableFrame(self.hud_body, corner_radius=12)
        self.card_stats.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(
            self.card_stats,
            text="📊 AI Token Activity & Insights",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(6, 6))

        self.lbl_today_total = ctk.CTkLabel(
            self.card_stats, text="", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_today_total.pack(anchor="w", padx=10, pady=1)

        self.lbl_today_breakdown = ctk.CTkLabel(
            self.card_stats, text="", font=ctk.CTkFont(size=11), text_color="gray70"
        )
        self.lbl_today_breakdown.pack(anchor="w", padx=10, pady=1)

        # Per-Tool Distribution Card
        self.tool_frame = ctk.CTkFrame(self.card_stats, fg_color="#1E1E2E", corner_radius=8)
        self.tool_frame.pack(fill="x", padx=6, pady=8)

        ctk.CTkLabel(
            self.tool_frame,
            text="🤖 AI Tools Distribution",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#CDD6F4",
        ).pack(anchor="w", padx=10, pady=(6, 2))

        self.lbl_tools_dist = ctk.CTkLabel(
            self.tool_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray70",
            justify="left",
        )
        self.lbl_tools_dist.pack(anchor="w", padx=10, pady=(0, 6))

        self.lbl_5h = ctk.CTkLabel(self.card_stats, text="", font=ctk.CTkFont(size=11))
        self.lbl_5h.pack(anchor="w", padx=10, pady=1)

        self.lbl_weekly = ctk.CTkLabel(self.card_stats, text="", font=ctk.CTkFont(size=11))
        self.lbl_weekly.pack(anchor="w", padx=10, pady=1)

        self.lbl_lifetime = ctk.CTkLabel(self.card_stats, text="", font=ctk.CTkFont(size=11))
        self.lbl_lifetime.pack(anchor="w", padx=10, pady=1)

        # 7-Day Chart
        self.chart_frame = ctk.CTkFrame(self.card_stats, fg_color="#181825", corner_radius=10)
        self.chart_frame.pack(fill="x", padx=6, pady=(10, 6))

        ctk.CTkLabel(
            self.chart_frame,
            text="📅 7-Day Burn History",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#CDD6F4",
        ).pack(anchor="w", padx=10, pady=(6, 2))

        self.chart_canvas = tk.Canvas(
            self.chart_frame, bg="#181825", highlightthickness=0, height=95
        )
        self.chart_canvas.pack(fill="x", padx=8, pady=(0, 6))

        self.refresh()

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

        self.lbl_trainer_rank.configure(text=f"🎖️ {rank_title} ({rank_badge})")
        self.lbl_trainer_streak.configure(text=f"🔥 {streak}-Day Coding Streak")
        self.lbl_trainer_dex.configure(text=f"⭐ {dex_count}/30 Pokédex Caught")

        # Update Companion Card with Dynamic Theme
        self.card_companion.configure(
            fg_color=theme["card_bg"],
            border_color=theme["border"],
        )

        if self.store.is_egg:
            self.lbl_comp_title.configure(text="🥚 Token Egg", text_color="#CDD6F4")
            self.lbl_comp_sub.configure(text=f"Tier: {self.store.egg_tier.value.capitalize()}")
            egg_img = ctk.CTkImage(create_egg_image((110, 110)), size=(110, 110))
            self.lbl_sprite.configure(image=egg_img)
            pct = self.store.progress_percentage
            self.progress_bar.configure(progress_color="#89B4FA")
            self.progress_bar.set(pct)
            self.lbl_progress_text.configure(
                text=f"Hatching Progress: {format_tokens(self.store.egg_usage)} / {format_tokens(self.store.current_threshold)} ({pct * 100:.1f}%)"
            )
            self.btn_use_mint.configure(state="disabled")
        else:
            act = self.store.active
            shiny_str = " ✨" if act.is_shiny else ""
            type_str = POKEMON_TYPES.get(act.species_id, "⭐ Normal")

            self.lbl_comp_title.configure(
                text=f"{act.species_name}{shiny_str}", text_color=theme["primary"]
            )
            self.lbl_comp_sub.configure(
                text=f"{type_str}  •  {act.nature.value} Nature  •  Form {act.stage_index + 1}/{act.total_forms}"
            )

            ctk_img = self.dashboard.get_cached_sprite(act.species_id, act.is_shiny, size=110)
            if ctk_img:
                self.lbl_sprite.configure(image=ctk_img)

            pct = self.store.progress_percentage
            self.progress_bar.configure(progress_color=theme["primary"])
            self.progress_bar.set(pct)
            stage_goal = "Graduation" if self.store.is_final_stage else "Next Evolution"
            self.lbl_progress_text.configure(
                text=f"{stage_goal} EXP: {format_tokens(act.used_at_stage)} / {format_tokens(self.store.current_threshold)} ({pct * 100:.1f}%)"
            )
            self.btn_use_mint.configure(state="normal")

        # Daily Budget Stamina Gauge
        limit = self.store.daily_token_limit
        if limit > 0:
            stamina_pct = min(1.0, self.summary.today_tokens / limit)
            stamina_color = (
                "#2ECC71" if stamina_pct < 0.8 else ("#E67E22" if stamina_pct < 1.0 else "#E74C3C")
            )
            self.stamina_bar.configure(progress_color=stamina_color)
            self.stamina_bar.set(stamina_pct)
            self.lbl_stamina_text.configure(
                text=f"⚡ Daily Stamina: {format_tokens(self.summary.today_tokens)} / {format_tokens(limit)} ({stamina_pct * 100:.1f}%)"
            )
        else:
            self.stamina_bar.configure(progress_color="#585B70")
            self.stamina_bar.set(0.0)
            self.lbl_stamina_text.configure(text="⚡ Daily Limit: Unlimited (Set in Settings)")

        # Stats Texts
        self.lbl_today_total.configure(
            text=f"🔥 Today's Spend: {format_tokens(self.summary.today_tokens)} tokens"
        )
        self.lbl_today_breakdown.configure(
            text=f"↳ In: {format_tokens(self.summary.today_input)} | Out: {format_tokens(self.summary.today_output)} | Cache: {format_tokens(self.summary.today_cache)}"
        )

        # Per-tool breakdown text
        dist_texts = []
        by_source = getattr(self.summary, "by_source", {}) or {}
        source_labels = {
            "antigravity": "Antigravity CLI",
            "claude": "Claude Code",
            "cursor": "Cursor IDE",
            "codex": "Codex CLI",
            "copilot": "GitHub Copilot",
            "koma": "Koma",
        }
        for src, count in by_source.items():
            if count > 0:
                name = source_labels.get(src, src.capitalize())
                dist_texts.append(f"{name}: {format_tokens(count)}")

        if not dist_texts:
            dist_texts.append("Active local AI sessions will appear here as tokens are burned.")
        self.lbl_tools_dist.configure(text="  •  ".join(dist_texts))

        self.lbl_5h.configure(
            text=f"⏱️ Last 5 Hours: {format_tokens(self.summary.rolling_5h_tokens)} tokens"
        )
        self.lbl_weekly.configure(
            text=f"📅 Past 7 Days: {format_tokens(self.summary.weekly_tokens)} tokens"
        )
        self.lbl_lifetime.configure(
            text=f"🌟 Lifetime Burn: {format_tokens(self.summary.lifetime_tokens)} tokens"
        )

        candies = self.store.inventory.get(ItemKind.RARE_CANDY.value, 0)
        mints = self.store.inventory.get(ItemKind.MINT.value, 0)
        self.btn_use_candy.configure(text=f"🍬 Feed Rare Candy ({candies} in bag)")
        self.btn_use_mint.configure(text=f"🌿 Use Nature Mint ({mints} in bag)")

        self._render_history_chart()

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
        bar_w = 24
        gap = 12
        start_x = 16
        chart_base_y = 78
        max_bar_h = 52

        for i, (val, lbl) in enumerate(zip(values, labels)):
            x = start_x + i * (bar_w + gap)
            bar_h = max(4, int(max_bar_h * val / max_val)) if val > 0 else 3
            y_top = chart_base_y - bar_h

            bar_color = (
                theme["primary"] if i == 6 else ("#E67E22" if i == peak_idx else "#45475A")
            )
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
            self.dashboard.show_toast("🍬 Fed Rare Candy! +100M Token EXP Gained!")
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
