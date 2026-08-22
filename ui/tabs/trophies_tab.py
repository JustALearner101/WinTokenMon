"""
Trophies and Achievements Tab View for WinTokenMon Dashboard (v0.2.0)
Presents developer badges, progress bars, tiers, and rewards in a clean CustomTkinter grid.
"""

import datetime
from typing import Any

import customtkinter as ctk

from core.companion_store import CompanionStore


class TrophiesTabView(ctk.CTkFrame):
    def __init__(self, master, store: CompanionStore, achievement_engine, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack(fill="both", expand=True)
        self.store = store
        self.achievement_engine = achievement_engine
        self.current_filter = "All"

        self._build_ui()

    def _build_ui(self):
        # 1. Summary Header Card
        self.header_card = ctk.CTkFrame(
            self, fg_color="#181C24", corner_radius=12, border_width=1, border_color="#2A2F3D"
        )
        self.header_card.pack(fill="x", padx=16, pady=(12, 10))

        header_inner = ctk.CTkFrame(self.header_card, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=12)

        self.lbl_trophies_count = ctk.CTkLabel(
            header_inner,
            text="🏆 0/8 Trophies Unlocked",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#F1C40F",
        )
        self.lbl_trophies_count.pack(side="left")

        # Filter Segmented Button
        self.filter_seg = ctk.CTkSegmentedButton(
            header_inner,
            values=["All", "Unlocked", "Locked"],
            command=self._on_filter_changed,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#12141A",
            selected_color="#3B82F6",
            selected_hover_color="#2563EB",
            unselected_color="#181C24",
            unselected_hover_color="#232733",
        )
        self.filter_seg.set("All")
        self.filter_seg.pack(side="right")

        # 2. Scrollable Grid Container for Badges
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)

        self.refresh()

    def _on_filter_changed(self, value: str):
        self.current_filter = value
        self.refresh()

    def refresh(self):
        """Re-renders trophy list and header stats."""
        # Clear existing cards
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        overview: list[dict[str, Any]] = self.achievement_engine.get_trophies_overview()
        unlocked_count = sum(1 for a in overview if a["is_unlocked"])
        total_count = len(overview)

        self.lbl_trophies_count.configure(
            text=f"🏆 {unlocked_count}/{total_count} Trophies Unlocked"
        )

        # Filter items
        filtered = []
        for a in overview:
            if self.current_filter == "Unlocked" and not a["is_unlocked"]:
                continue
            if self.current_filter == "Locked" and a["is_unlocked"]:
                continue
            filtered.append(a)

        if not filtered:
            empty_lbl = ctk.CTkLabel(
                self.scroll_frame,
                text="No trophies match the selected filter.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color="#8B949E",
            )
            empty_lbl.pack(pady=40)
            return

        # Render 2-column grid
        for idx, item in enumerate(filtered):
            row = idx // 2
            col = idx % 2
            card = self._create_trophy_card(self.scroll_frame, item)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

    def _create_trophy_card(self, parent, item: dict[str, Any]) -> ctk.CTkFrame:
        is_unlocked = item["is_unlocked"]
        tier_color = item["tier_color"]

        card_bg = "#1A1E27" if is_unlocked else "#13161C"
        border_color = tier_color if is_unlocked else "#262C38"
        border_w = 2 if is_unlocked else 1

        card = ctk.CTkFrame(
            parent,
            fg_color=card_bg,
            corner_radius=10,
            border_width=border_w,
            border_color=border_color,
        )

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # Top row: Emoji + Tier Tag + Status
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 4))

        # Icon Emoji
        emoji_lbl = ctk.CTkLabel(
            top_row,
            text=item["icon_emoji"],
            font=ctk.CTkFont(family="Segoe UI Emoji", size=24),
        )
        emoji_lbl.pack(side="left", padx=(0, 8))

        # Title & Category Container
        title_box = ctk.CTkFrame(top_row, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        title_color = "#FFFFFF" if is_unlocked else "#8B949E"
        title_lbl = ctk.CTkLabel(
            title_box,
            text=item["title"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=title_color,
            anchor="w",
        )
        title_lbl.pack(anchor="w")

        tier_tag = ctk.CTkLabel(
            title_box,
            text=f"{item['tier_title'].upper()} • {item['category']}",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=tier_color,
            anchor="w",
        )
        tier_tag.pack(anchor="w")

        # Unlocked status pill
        status_text = "✓ UNLOCKED" if is_unlocked else "🔒 LOCKED"
        status_bg = "#064E3B" if is_unlocked else "#21262D"
        status_fg = "#34D399" if is_unlocked else "#6E7681"

        status_pill = ctk.CTkLabel(
            top_row,
            text=status_text,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color=status_bg,
            text_color=status_fg,
            corner_radius=6,
            padx=6,
            pady=2,
        )
        status_pill.pack(side="right")

        # Middle: Description
        desc_lbl = ctk.CTkLabel(
            inner,
            text=item["description"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#9CA3AF" if is_unlocked else "#6B7280",
            wraplength=260,
            justify="left",
            anchor="w",
        )
        desc_lbl.pack(anchor="w", fill="x", pady=(4, 6))

        # Progress bar (for locked progressive achievements)
        if not is_unlocked:
            pct = item["progress_pct"]
            prog_bar = ctk.CTkProgressBar(
                inner,
                height=6,
                progress_color="#3B82F6",
                fg_color="#21262D",
                corner_radius=3,
            )
            prog_bar.set(pct)
            prog_bar.pack(fill="x", pady=(2, 2))

            prog_lbl = ctk.CTkLabel(
                inner,
                text=item["progress_label"],
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#6B7280",
                anchor="e",
            )
            prog_lbl.pack(anchor="e", fill="x")

        # Bottom row: Reward pill & Unlock date
        bottom_row = ctk.CTkFrame(inner, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(6, 0))

        if item["reward_desc"]:
            reward_pill = ctk.CTkLabel(
                bottom_row,
                text=f"🎁 {item['reward_desc']}",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color="#FBBF24",
                fg_color="#3B2A0A" if is_unlocked else "#262013",
                corner_radius=5,
                padx=6,
                pady=1,
            )
            reward_pill.pack(side="left")

        if is_unlocked and item["unlocked_at"]:
            dt_str = datetime.datetime.fromtimestamp(item["unlocked_at"]).strftime("%d %b %Y")
            date_lbl = ctk.CTkLabel(
                bottom_row,
                text=f"Unlocked on {dt_str}",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#4B5563",
            )
            date_lbl.pack(side="right")

        return card
