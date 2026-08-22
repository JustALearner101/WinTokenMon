"""
Pokédex & Catch Log Tab for WinTokenMon Dashboard
"""

from datetime import datetime

import customtkinter as ctk

from core.audio_manager import play_cry
from core.companion_store import CompanionStore
from ui.dashboard_theme import TYPE_THEMES, get_pokemon_element_type
from ui.desktop_pet import format_tokens
from ui.modals.pokedex_inspector_modal import PokedexInspectorModal


class PokedexTabView:
    """Manages the Pokédex and Catch Log dynamic view with search, filter, and inspector triggers."""

    def __init__(self, parent: ctk.CTkFrame, dashboard):
        self.parent = parent
        self.dashboard = dashboard
        self.store: CompanionStore = dashboard.store

        self._build_ui()

    def _build_ui(self):
        # 1. Top Header Bar with Mode Switcher (Pokédex vs Catch Log)
        self.pokedex_header = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.pokedex_header.pack(fill="x", padx=10, pady=(6, 2))

        self.lbl_dex_count = ctk.CTkLabel(
            self.pokedex_header, text="", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_dex_count.pack(side="left")

        self.view_mode_btn = ctk.CTkSegmentedButton(
            self.pokedex_header,
            values=["📖 Pokédex", "📜 Catch Log"],
            command=lambda v: self.refresh(),
            width=200,
        )
        self.view_mode_btn.set("📖 Pokédex")
        self.view_mode_btn.pack(side="right")

        # 2. Filter Bar (Search + Rarity Pills)
        self.filter_bar = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.filter_bar.pack(fill="x", padx=10, pady=(2, 6))

        self.entry_search = ctk.CTkEntry(
            self.filter_bar, placeholder_text="🔍 Search species or #ID...", width=200
        )
        self.entry_search.pack(side="left", padx=(0, 8))
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh())

        self.filter_selector = ctk.CTkSegmentedButton(
            self.filter_bar,
            values=["All", "Legendary", "Rare", "Uncommon", "Common"],
            command=lambda v: self.refresh(),
        )
        self.filter_selector.set("All")
        self.filter_selector.pack(side="left", fill="x", expand=True)

        # 3. Main Scrollable Content Area
        self.pokedex_scroll = ctk.CTkScrollableFrame(self.parent, corner_radius=12)
        self.pokedex_scroll.pack(fill="both", expand=True, padx=10, pady=6)

        self.refresh()

    def refresh(self):
        if not hasattr(self, "pokedex_scroll"):
            return

        # Clear existing widgets inside scroll container
        for child in self.pokedex_scroll.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        dex_species = self.store.get_dex_species()
        mode = self.view_mode_btn.get() if hasattr(self, "view_mode_btn") else "📖 Pokédex"
        search_kw = self.entry_search.get().strip().lower() if hasattr(self, "entry_search") else ""
        rarity_filter = self.filter_selector.get() if hasattr(self, "filter_selector") else "All"

        total_registered = len(dex_species)
        total_logs = len(self.store.catch_log)
        self.lbl_dex_count.configure(
            text=f"📖 {total_registered} Species Registered  •  {total_logs} Lifetime Catches"
        )

        if mode == "📖 Pokédex":
            self._render_pokedex_view(dex_species, search_kw, rarity_filter)
        else:
            self._render_catch_log_view(search_kw, rarity_filter)

    def _render_empty_state(self, species_id: int = 25, title: str = "", subtitle: str = ""):
        empty_box = ctk.CTkFrame(self.pokedex_scroll, fg_color="transparent")
        empty_box.pack(fill="both", expand=True, pady=40)

        ctk_img = self.dashboard.get_cached_sprite(species_id, False, size=80)
        if ctk_img:
            ctk.CTkLabel(empty_box, image=ctk_img, text="").pack(pady=(10, 6))
        else:
            ctk.CTkLabel(empty_box, text="🥚", font=ctk.CTkFont(size=48)).pack(pady=(10, 6))

        ctk.CTkLabel(
            empty_box,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#CDD6F4",
        ).pack(pady=2)

        ctk.CTkLabel(
            empty_box,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color="gray70",
            justify="center",
        ).pack(pady=(2, 10))

    def _render_pokedex_view(self, dex_species: list[dict], search_kw: str, rarity_filter: str):
        if not dex_species:
            self._render_empty_state(
                species_id=25,
                title="📖 Your Pokédex is Empty",
                subtitle="You haven't registered any Pokémon yet!\nBurn tokens in AI coding sessions to hatch eggs and evolve your companions.",
            )
            return

        filtered = dex_species
        if search_kw:
            filtered = [
                s for s in filtered if search_kw in s["name"].lower() or str(s["id"]) in search_kw
            ]
        if rarity_filter != "All":
            filtered = [s for s in filtered if s["rarity"].lower() == rarity_filter.lower()]

        if not filtered:
            ctk.CTkLabel(
                self.pokedex_scroll,
                text="🔍 No Pokémon found matching the selected filter/search.",
                font=ctk.CTkFont(size=13),
                text_color="gray70",
            ).pack(pady=40)
            return

        # 4-Column Grid of Owned Pokémon
        grid_frame = ctk.CTkFrame(self.pokedex_scroll, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)

        for i in range(4):
            grid_frame.columnconfigure(i, weight=1)

        row, col = 0, 0
        for entry in filtered:
            sp_id = entry["id"]
            name = entry["name"]
            is_shiny = entry["is_shiny"]
            is_raising = entry.get("is_raising", False)

            elem = get_pokemon_element_type(sp_id)
            theme = TYPE_THEMES.get(elem, TYPE_THEMES["normal"])

            card = ctk.CTkFrame(
                grid_frame,
                corner_radius=12,
                border_width=2 if (is_shiny or is_raising) else 1,
                border_color=(
                    "#F1C40F" if is_shiny else (theme["primary"] if is_raising else theme["border"])
                ),
                fg_color=theme["card_bg"],
                height=155,
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            card.pack_propagate(False)

            # Title / Header Row
            top_bar = ctk.CTkFrame(card, fg_color="transparent")
            top_bar.pack(fill="x", padx=8, pady=(6, 2))

            shiny_star = " ✨" if is_shiny else ""
            lbl_title = ctk.CTkLabel(
                top_bar,
                text=f"#{sp_id:03d} {name}{shiny_star}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=theme["primary"],
            )
            lbl_title.pack(side="left")

            if is_raising:
                lbl_badge = ctk.CTkLabel(
                    top_bar,
                    text="⭐ ACTIVE",
                    font=ctk.CTkFont(size=8, weight="bold"),
                    fg_color="#F1C40F",
                    text_color="#181825",
                    corner_radius=4,
                    padx=4,
                    pady=1,
                )
                lbl_badge.pack(side="right")

            # Sprite Image
            ctk_img = self.dashboard.get_cached_sprite(sp_id, is_shiny, size=64)
            if ctk_img:
                lbl_sp = ctk.CTkLabel(card, image=ctk_img, text="", cursor="hand2")
                lbl_sp.pack(pady=2)
                lbl_sp.bind(
                    "<Button-1>",
                    lambda e, sid=sp_id, sn=name, ish=is_shiny: self._open_inspector(
                        sid, sn, True, ish
                    ),
                )
            else:
                lbl_sp = ctk.CTkLabel(card, text="🐾", font=ctk.CTkFont(size=24), cursor="hand2")
                lbl_sp.pack(pady=10)
                lbl_sp.bind(
                    "<Button-1>",
                    lambda e, sid=sp_id, sn=name, ish=is_shiny: self._open_inspector(
                        sid, sn, True, ish
                    ),
                )

            # Rarity & Inspect Action
            btn_inspect = ctk.CTkButton(
                card,
                text="Inspect 🔍",
                font=ctk.CTkFont(size=10, weight="bold"),
                height=24,
                fg_color=theme["primary"],
                hover_color=theme["secondary"],
                text_color="#181825",
                command=lambda sid=sp_id, sn=name, ish=is_shiny: self._open_inspector(
                    sid, sn, True, ish
                ),
            )
            btn_inspect.pack(fill="x", padx=10, pady=(0, 6))

            col += 1
            if col >= 4:
                col = 0
                row += 1

    def _render_catch_log_view(self, search_kw: str, rarity_filter: str):
        logs = list(self.store.catch_log)
        # If currently active companion exists, prepend it as the newest entry
        if self.store.active:
            act = self.store.active
            active_log = {
                "species_id": act.species_id,
                "species_name": act.species_name,
                "rarity": act.rarity.value,
                "nature": act.nature.value,
                "is_shiny": act.is_shiny,
                "caught_at": act.hatched_at,
                "total_tokens_spent": act.used_at_stage,
                "is_raising": True,
            }
            logs.insert(0, active_log)

        if not logs:
            self._render_empty_state(
                species_id=143,
                title="📜 No Catch History Yet",
                subtitle="When your companions graduate or hatch, detailed catch logs with timestamps and natures will appear here.",
            )
            return

        filtered = logs
        if search_kw:
            filtered = [
                log_item
                for log_item in filtered
                if search_kw in log_item.get("species_name", "").lower()
                or str(log_item.get("species_id", "")) in search_kw
            ]
        if rarity_filter != "All":
            filtered = [
                log_item
                for log_item in filtered
                if log_item.get("rarity", "").lower() == rarity_filter.lower()
            ]

        if not filtered:
            ctk.CTkLabel(
                self.pokedex_scroll,
                text="🔍 No logs found matching the selected filter/search.",
                font=ctk.CTkFont(size=13),
                text_color="gray70",
            ).pack(pady=40)
            return

        for entry in filtered:
            sp_id = entry.get("species_id", 0)
            name = entry.get("species_name", f"Pokémon #{sp_id}")
            rarity = entry.get("rarity", "uncommon")
            nature = entry.get("nature", "Hardy")
            is_shiny = entry.get("is_shiny", False)
            caught_at = entry.get("caught_at", 0)
            is_raising = entry.get("is_raising", False)
            tokens_spent = entry.get("total_tokens_spent", 0)

            time_str = (
                datetime.fromtimestamp(caught_at).strftime("%Y-%m-%d %H:%M")
                if caught_at
                else "Recently"
            )

            elem = get_pokemon_element_type(sp_id)
            theme = TYPE_THEMES.get(elem, TYPE_THEMES["normal"])

            row_card = ctk.CTkFrame(
                self.pokedex_scroll,
                corner_radius=10,
                fg_color=theme["card_bg"],
                border_width=1,
                border_color=theme["border"],
            )
            row_card.pack(fill="x", padx=4, pady=4)

            # Left: Sprite
            ctk_img = self.dashboard.get_cached_sprite(sp_id, is_shiny, size=48)
            if ctk_img:
                lbl_img = ctk.CTkLabel(row_card, image=ctk_img, text="")
                lbl_img.pack(side="left", padx=10, pady=6)
            else:
                ctk.CTkLabel(row_card, text="🐾", font=ctk.CTkFont(size=20)).pack(
                    side="left", padx=12, pady=6
                )

            # Middle: Info Details
            info_frame = ctk.CTkFrame(row_card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=4, pady=6)

            shiny_star = " ✨" if is_shiny else ""
            status_tag = " [Raising Now ⭐]" if is_raising else " [Graduated 🎓]"
            ctk.CTkLabel(
                info_frame,
                text=f"#{sp_id:03d} {name}{shiny_star}{status_tag}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=theme["primary"],
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_frame,
                text=f"Nature: {nature}  •  Rarity: {rarity.capitalize()}  •  Tokens Burned: {format_tokens(tokens_spent)}",
                font=ctk.CTkFont(size=10),
                text_color="#CDD6F4",
            ).pack(anchor="w", pady=1)

            ctk.CTkLabel(
                info_frame,
                text=f"🕒 Registered: {time_str}",
                font=ctk.CTkFont(size=9),
                text_color="gray70",
            ).pack(anchor="w")

            # Right: Action Button
            btn_view = ctk.CTkButton(
                row_card,
                text="Inspect 🔍",
                font=ctk.CTkFont(size=10, weight="bold"),
                width=90,
                height=26,
                fg_color=theme["primary"],
                text_color="#181825",
                hover_color=theme["secondary"],
                command=lambda sid=sp_id, sn=name, ish=is_shiny: self._open_inspector(
                    sid, sn, True, ish
                ),
            )
            btn_view.pack(side="right", padx=12, pady=8)

    def _open_inspector(self, species_id: int, species_name: str, is_caught: bool, is_shiny: bool):
        def on_set_companion(sp_id: int):
            if self.store.set_active_from_pokedex(sp_id):
                play_cry(sp_id, 0.7)
                self.dashboard.show_toast(f"⭐ Active companion changed to {species_name}!")
                self.dashboard.refresh_home_view()
                self.refresh()
                if self.dashboard.on_update_callback:
                    self.dashboard.on_update_callback()

        PokedexInspectorModal(
            self.dashboard.win, species_id, species_name, is_caught, is_shiny, on_set_companion
        )
