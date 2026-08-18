"""
Nature Mint Selector Modal for WinTokenMon Dashboard
"""

from collections.abc import Callable

import customtkinter as ctk

from core.models import PokemonNature
from ui.dashboard_theme import NATURE_DETAILS


class NatureSelectorModal:
    """Interactive dialog to select from 20 Pokémon natures with full stat descriptions."""

    def __init__(self, parent, on_select: Callable[[PokemonNature], None]):
        self.win = ctk.CTkToplevel(parent)
        self.win.title("🌿 Select Nature Mint")
        self.win.geometry("560x520")
        self.win.minsize(500, 440)
        self.win.lift()
        self.win.grab_set()

        self.on_select = on_select

        ctk.CTkLabel(
            self.win,
            text="🌿 Choose Pokémon Nature",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2ECC71",
        ).pack(pady=(14, 4))

        ctk.CTkLabel(
            self.win,
            text="Select a personality nature to optimize your companion's combat stat buffs.",
            font=ctk.CTkFont(size=11),
            text_color="gray70",
        ).pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(self.win, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        row, col = 0, 0
        scroll.columnconfigure(0, weight=1)
        scroll.columnconfigure(1, weight=1)

        for nat in PokemonNature:
            details = NATURE_DETAILS.get(nat, ("Special Buff", "Minor Penalty", "Unique profile"))
            buff, nerf, desc = details

            card = ctk.CTkFrame(scroll, corner_radius=8, border_width=1, border_color="#313244")
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            btn = ctk.CTkButton(
                card,
                text=f"{nat.value}",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#2E7D32",
                hover_color="#1B5E20",
                command=lambda n=nat: self._pick(n),
                height=30,
            )
            btn.pack(fill="x", padx=8, pady=(8, 4))

            ctk.CTkLabel(
                card,
                text=f"🟢 {buff}\n🔴 {nerf}",
                font=ctk.CTkFont(size=10),
                text_color="#A6ADC8",
                justify="left",
            ).pack(anchor="w", padx=8, pady=(0, 2))

            ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(size=9, slant="italic"),
                text_color="gray60",
                justify="left",
                wraplength=220,
            ).pack(anchor="w", padx=8, pady=(0, 8))

            col += 1
            if col >= 2:
                col = 0
                row += 1

    def _pick(self, nature: PokemonNature):
        self.win.destroy()
        self.on_select(nature)
