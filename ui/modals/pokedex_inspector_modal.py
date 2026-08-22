"""
Pokédex Species Detail Inspector Modal for WinTokenMon Dashboard
"""

import os
from collections.abc import Callable

import customtkinter as ctk
from PIL import Image

from core.audio_manager import play_cry
from core.poke_api import POKEMON_TYPES, SPECIES_INDEX, get_sprite_path
from ui.dashboard_theme import POKEMON_LORE, TYPE_THEMES, get_pokemon_element_type


class PokedexInspectorModal:
    """Full-screen detail inspector for a Pokémon entry: cry, evolution chain, lore, and companion switch."""

    def __init__(
        self,
        parent,
        species_id: int,
        species_name: str,
        is_caught: bool,
        is_shiny: bool,
        on_set_companion: Callable[[int], None] | None = None,
    ):
        self.win = ctk.CTkToplevel(parent)
        self.win.title(f"Pokédex Entry — #{species_id:03d} {species_name}")
        self.win.geometry("540x580")
        self.win.minsize(480, 500)
        self.win.lift()
        self.win.grab_set()

        self.species_id = species_id
        self.species_name = species_name
        self.is_caught = is_caught
        self.is_shiny = is_shiny
        self.on_set_companion = on_set_companion

        elem = get_pokemon_element_type(species_id)
        theme = TYPE_THEMES.get(elem, TYPE_THEMES["normal"])

        # Header
        hdr = ctk.CTkFrame(self.win, fg_color=theme["card_bg"], corner_radius=12)
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        shiny_str = " ✨ Shiny" if is_shiny else ""
        type_str = POKEMON_TYPES.get(species_id, "⭐ Normal")

        ctk.CTkLabel(
            hdr,
            text=f"#{species_id:03d} {species_name}{shiny_str}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=theme["primary"],
        ).pack(anchor="w", padx=16, pady=(12, 2))

        ctk.CTkLabel(
            hdr,
            text=f"Type: {type_str}  •  Status: {'✅ Registered' if is_caught else '🔒 Undiscovered'}",
            font=ctk.CTkFont(size=12),
            text_color=theme["badge_text"],
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # Main Content Scroll
        content = ctk.CTkScrollableFrame(self.win, corner_radius=10)
        content.pack(fill="both", expand=True, padx=16, pady=6)

        # Sprite Frame
        sprite_box = ctk.CTkFrame(content, fg_color="#181825", corner_radius=10)
        sprite_box.pack(fill="x", pady=6)

        sprite_path = get_sprite_path(species_id, is_shiny)
        if sprite_path and os.path.exists(sprite_path) and is_caught:
            try:
                pil_img = Image.open(sprite_path).convert("RGBA")
                ctk_img = ctk.CTkImage(pil_img, size=(120, 120))
                ctk.CTkLabel(sprite_box, image=ctk_img, text="").pack(pady=(12, 4))
            except Exception:
                ctk.CTkLabel(sprite_box, text="[Sprite Preview]", font=ctk.CTkFont(size=14)).pack(
                    pady=20
                )
        else:
            ctk.CTkLabel(
                sprite_box,
                text="❓\n\nUndiscovered Silhouette\nKeep burning tokens to hatch & register!",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="gray60",
            ).pack(pady=24)

        # Audio Cry Button
        btn_cry = ctk.CTkButton(
            sprite_box,
            text="🔊 Play Cry",
            width=130,
            height=28,
            fg_color="#1565C0",
            hover_color="#0D47A1",
            command=lambda: play_cry(species_id, volume=0.8),
        )
        btn_cry.pack(pady=(0, 12))

        # Lore / Bio Card
        lore_card = ctk.CTkFrame(content, corner_radius=10)
        lore_card.pack(fill="x", pady=6)

        ctk.CTkLabel(
            lore_card,
            text="📖 Pokédex Flavor Text",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#CDD6F4",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        lore_text = POKEMON_LORE.get(
            species_id,
            f"{species_name} thrives alongside software engineers, growing stronger as tokens flow through AI models.",
        )
        ctk.CTkLabel(
            lore_card,
            text=f'"{lore_text}"',
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#A6ADC8",
            wraplength=440,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Evolution Chain Tree
        chain_card = ctk.CTkFrame(content, corner_radius=10)
        chain_card.pack(fill="x", pady=6)

        ctk.CTkLabel(
            chain_card,
            text="🌿 Evolution Line & Thresholds",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#CDD6F4",
        ).pack(anchor="w", padx=12, pady=(10, 6))

        line_info = SPECIES_INDEX.get(species_id)

        if line_info:
            names = line_info["names"]
            chain_ids = line_info["chain"]
            tree_str = " ➔ ".join(
                [
                    f"{n} (#{cid:03d})" + (" ⭐" if cid == species_id else "")
                    for n, cid in zip(names, chain_ids)
                ]
            )
            ctk.CTkLabel(
                chain_card,
                text=tree_str,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=theme["primary"],
                wraplength=440,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(0, 10))

        # Footer Action (Set as Active Companion)
        if is_caught:
            btn_set = ctk.CTkButton(
                self.win,
                text="⭐ Set as Active Desktop Companion",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=theme["primary"],
                hover_color=theme["secondary"],
                height=36,
                command=self._action_set_active,
            )
            btn_set.pack(fill="x", padx=16, pady=(8, 14))

    def _action_set_active(self):
        if self.on_set_companion:
            self.on_set_companion(self.species_id)
        self.win.destroy()
