"""
Starter Pokémon Selection Modal for WinTokenMon
Features interactive Gen 1 - Gen 9 + Special grid selection,
animated sprite previews, elemental tags, and a confirmation modal.
"""

import os
from collections.abc import Callable

import customtkinter as ctk
from PIL import Image

from core.audio_manager import play_cry, play_sfx_levelup
from core.companion_store import CompanionStore
from core.poke_api import (
    POKEMON_TYPES,
    SPECIES_INDEX,
    STARTER_GENERATIONS,
    get_sprite_path,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class StarterSelectionModal:
    def __init__(self, store: CompanionStore, on_selected_callback: Callable | None = None):
        self.store = store
        self.on_selected_callback = on_selected_callback

        self.selected_generation: str = "Gen 1 (Kanto)"
        self.selected_species_id: int = 4  # Default Charmander

        self.win = ctk.CTkToplevel()
        self.win.title("WinTokenMon — Welcome & Starter Selection")
        self.win.geometry("860x650")
        self.win.minsize(800, 600)

        # Force on top during initial onboarding
        self.win.lift()
        self.win.attributes("-topmost", True)

        self._image_cache: dict[str, ctk.CTkImage] = {}

        self._build_ui()
        self._load_generation(self.selected_generation)

    def _build_ui(self):
        # 1. Header
        header_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(18, 10))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="🌟 Welcome to WinTokenMon!",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ctk.CTkLabel(
            header_frame,
            text="Choose your Starter Pokémon companion (Gen 1 to Gen 9) to begin your coding journey:",
            font=ctk.CTkFont(size=13),
            text_color="#8E8E93",
        )
        subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # 2. Generation Selector Grid / Bar
        gen_scroll = ctk.CTkScrollableFrame(self.win, height=48, orientation="horizontal")
        gen_scroll.pack(fill="x", padx=24, pady=6)

        self.gen_buttons: dict[str, ctk.CTkButton] = {}
        for gen_name in STARTER_GENERATIONS.keys():
            btn = ctk.CTkButton(
                gen_scroll,
                text=gen_name,
                width=110,
                height=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#2C2C2E" if gen_name != self.selected_generation else "#007AFF",
                hover_color="#3A3A3C",
                command=lambda g=gen_name: self._select_generation(g),
            )
            btn.pack(side="left", padx=4)
            self.gen_buttons[gen_name] = btn

        # 3. Starter Cards Container
        self.cards_container = ctk.CTkFrame(self.win, fg_color="transparent")
        self.cards_container.pack(fill="both", expand=True, padx=24, pady=10)

        # 4. Bottom Action Bar
        bottom_frame = ctk.CTkFrame(self.win, fg_color="#1C1C1E", corner_radius=12)
        bottom_frame.pack(fill="x", padx=24, pady=(6, 18))

        self.selected_banner_lbl = ctk.CTkLabel(
            bottom_frame,
            text="Selected Starter: 🔥 Charmander (#4)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF",
        )
        self.selected_banner_lbl.pack(side="left", padx=20, pady=14)

        choose_btn = ctk.CTkButton(
            bottom_frame,
            text="🔴 I Choose You! (Start Coding)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#FF3B30",
            hover_color="#D70015",
            height=38,
            command=self._open_confirmation_dialog,
        )
        choose_btn.pack(side="right", padx=20, pady=14)

    def _select_generation(self, gen_name: str):
        self.selected_generation = gen_name
        for name, btn in self.gen_buttons.items():
            btn.configure(fg_color="#007AFF" if name == gen_name else "#2C2C2E")
        self._load_generation(gen_name)

    def _load_generation(self, gen_name: str):
        # Clear previous cards
        for widget in self.cards_container.winfo_children():
            widget.destroy()

        species_ids = STARTER_GENERATIONS.get(gen_name, [])

        # Configure 3-column grid
        self.cards_container.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")

        # Automatically select the first pokemon of the generation if none selected
        if species_ids and self.selected_species_id not in species_ids:
            self.selected_species_id = species_ids[0]

        for col_idx, species_id in enumerate(species_ids):
            self._render_starter_card(col_idx, species_id)

        self._update_banner()

    def _render_starter_card(self, col_idx: int, species_id: int):
        line_info = SPECIES_INDEX.get(species_id)
        if not line_info:
            return

        name_idx = line_info["chain"].index(species_id)
        species_name = line_info["names"][name_idx]
        element_type = POKEMON_TYPES.get(species_id, "Normal")
        is_selected = self.selected_species_id == species_id

        # Determine theme color
        theme_color = (
            "#34C759"
            if "Grass" in element_type
            else (
                "#FF9500"
                if "Fire" in element_type
                else (
                    "#007AFF"
                    if "Water" in element_type
                    else "#FFCC00"
                    if "Electric" in element_type
                    else "#AF52DE"
                )
            )
        )

        card = ctk.CTkFrame(
            self.cards_container,
            fg_color="#242426" if not is_selected else "#2C2C2E",
            border_color=theme_color if is_selected else "#3A3A3C",
            border_width=3 if is_selected else 1,
            corner_radius=14,
        )
        card.grid(row=0, column=col_idx, padx=8, pady=4, sticky="nsew")

        # Type Badge Pill
        type_badge = ctk.CTkLabel(
            card,
            text=f" {element_type} ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#3A3A3C",
            corner_radius=6,
        )
        type_badge.pack(pady=(12, 4))

        # Sprite Image
        sprite_path = get_sprite_path(species_id)
        if sprite_path and os.path.exists(sprite_path):
            try:
                pil_img = Image.open(sprite_path)
                ctk_img = ctk.CTkImage(pil_img, size=(96, 96))
                self._image_cache[f"card_{species_id}"] = ctk_img
                img_lbl = ctk.CTkLabel(card, image=ctk_img, text="")
                img_lbl.pack(pady=4)
            except Exception:
                pass

        # Species Name & Pokédex Number
        name_lbl = ctk.CTkLabel(
            card,
            text=f"#{species_id:03d} {species_name}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FFFFFF" if not is_selected else theme_color,
        )
        name_lbl.pack(pady=(2, 4))

        # Evolution Chain Preview
        evo_names = " ➔ ".join(line_info["names"])
        evo_lbl = ctk.CTkLabel(
            card,
            text=f"Evolves: {evo_names}",
            font=ctk.CTkFont(size=11),
            text_color="#8E8E93",
            wraplength=190,
        )
        evo_lbl.pack(pady=(0, 10))

        # Select Card Button
        select_btn = ctk.CTkButton(
            card,
            text="Selected ✓" if is_selected else "Choose",
            fg_color=theme_color if is_selected else "#3A3A3C",
            hover_color=theme_color,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=lambda s=species_id: self._on_card_clicked(s),
        )
        select_btn.pack(fill="x", padx=16, pady=(0, 14), side="bottom")

    def _on_card_clicked(self, species_id: int):
        self.selected_species_id = species_id
        if self.store.sound_enabled:
            play_cry(species_id)
        self._load_generation(self.selected_generation)

    def _update_banner(self):
        line = SPECIES_INDEX.get(self.selected_species_id)
        species_name = "Unknown"
        if line and self.selected_species_id in line["chain"]:
            idx = line["chain"].index(self.selected_species_id)
            species_name = line["names"][idx]

        element_type = POKEMON_TYPES.get(self.selected_species_id, "")
        self.selected_banner_lbl.configure(
            text=f"Selected Starter: {element_type} {species_name} (#{self.selected_species_id:03d})"
        )

    def _open_confirmation_dialog(self):
        line = SPECIES_INDEX.get(self.selected_species_id)
        species_name = "Starter"
        if line and self.selected_species_id in line["chain"]:
            idx = line["chain"].index(self.selected_species_id)
            species_name = line["names"][idx]

        # Create confirmation modal
        dialog = ctk.CTkToplevel(self.win)
        dialog.title("Confirm Starter Selection")
        dialog.geometry("480x280")
        dialog.resizable(False, False)
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # Icon/Sprite in dialog
        sprite_path = get_sprite_path(self.selected_species_id)
        if sprite_path and os.path.exists(sprite_path):
            try:
                pil_img = Image.open(sprite_path)
                ctk_img = ctk.CTkImage(pil_img, size=(64, 64))
                self._image_cache["dialog_sprite"] = ctk_img
                dlg_img_lbl = ctk.CTkLabel(content_frame, image=ctk_img, text="")
                dlg_img_lbl.pack(pady=(0, 6))
            except Exception:
                pass

        dlg_title = ctk.CTkLabel(
            content_frame,
            text=f"Choose {species_name} as your companion?",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        dlg_title.pack(pady=(0, 6))

        dlg_desc = ctk.CTkLabel(
            content_frame,
            text=f"Are you sure you want to start with {species_name}?\nOnce chosen, {species_name} will roam your desktop\nand level up as you write code with AI!",
            font=ctk.CTkFont(size=12),
            text_color="#8E8E93",
            justify="center",
        )
        dlg_desc.pack(pady=(0, 16))

        btn_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            btn_row,
            text="↩️ Go Back",
            font=ctk.CTkFont(size=13),
            fg_color="#3A3A3C",
            hover_color="#48484A",
            width=120,
            command=dialog.destroy,
        )
        cancel_btn.pack(side="left", padx=(10, 8), expand=True)

        confirm_btn = ctk.CTkButton(
            btn_row,
            text=f"🔴 Yes, I Choose {species_name}!",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#FF3B30",
            hover_color="#D70015",
            width=200,
            command=lambda: self._finalize_choice(dialog),
        )
        confirm_btn.pack(side="right", padx=(8, 10), expand=True)

    def _finalize_choice(self, dialog: ctk.CTkToplevel):
        dialog.destroy()
        # Activate starter in store
        self.store.choose_starter(self.selected_species_id)

        # Play celebration SFX and cry
        if self.store.sound_enabled:
            play_sfx_levelup()
            play_cry(self.selected_species_id)

        # Trigger update callback for pet/tray
        if self.on_selected_callback:
            self.on_selected_callback()

        # Close onboarding modal
        self.win.destroy()
