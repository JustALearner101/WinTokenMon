"""
Shop & Bag Inventory Tab for WinTokenMon Dashboard
"""

import customtkinter as ctk

from core.companion_store import CompanionStore
from core.models import EggTier, ItemKind
from ui.desktop_pet import format_tokens


class ShopTabView:
    """Manages the Shop and Bag item purchases, egg incubator adoption, and inventory counts."""

    def __init__(self, parent: ctk.CTkFrame, dashboard):
        self.parent = parent
        self.dashboard = dashboard
        self.store: CompanionStore = dashboard.store

        self._build_ui()

    def _build_ui(self):
        self.shop_scroll = ctk.CTkScrollableFrame(self.parent, corner_radius=12)
        self.shop_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh()

    def refresh(self):
        for widget in self.shop_scroll.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        # Spendable Token Header
        hdr = ctk.CTkFrame(self.shop_scroll, fg_color="#1E1E2E", corner_radius=10)
        hdr.pack(fill="x", padx=6, pady=6)

        ctk.CTkLabel(
            hdr,
            text=f"🪙 Spendable Tokens: {format_tokens(self.store.spendable_tokens)}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#89B4FA",
        ).pack(side="left", padx=14, pady=10)

        # Egg Incubator Status Card
        inc_frame = ctk.CTkFrame(
            self.shop_scroll,
            fg_color="#181825",
            corner_radius=10,
            border_width=1,
            border_color="#313244",
        )
        inc_frame.pack(fill="x", padx=6, pady=6)

        if self.store.is_egg:
            pct = self.store.progress_percentage
            ctk.CTkLabel(
                inc_frame,
                text=f"🥚 Active Egg Incubator ({self.store.egg_tier.value.capitalize()} Tier)",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#F1C40F",
            ).pack(anchor="w", padx=12, pady=(8, 2))
            ctk.CTkLabel(
                inc_frame,
                text=f"Tokens needed to hatch: {format_tokens(self.store.egg_usage)} / {format_tokens(self.store.current_threshold)} ({pct * 100:.1f}%)",
                font=ctk.CTkFont(size=11),
                text_color="gray70",
            ).pack(anchor="w", padx=12, pady=(0, 8))
        else:
            ctk.CTkLabel(
                inc_frame,
                text="🥚 Incubator Standby: Ready for new egg adoption when active Pokémon graduates.",
                font=ctk.CTkFont(size=11),
                text_color="gray70",
            ).pack(anchor="w", padx=12, pady=10)

        # Items list
        items_to_sell = [
            (
                ItemKind.RARE_CANDY,
                "🍬 Rare Candy",
                "Gives your active Pokémon 100M bonus token EXP immediately.",
            ),
            (
                ItemKind.MINT,
                "🌿 Nature Mint",
                "Choose a desired nature from 20 personalities to optimize stat buffs.",
            ),
            (
                ItemKind.SHINY_CHARM,
                "✨ Shiny Charm",
                "Permanently boosts shiny egg hatch probability from 1/129 to 1/40.",
            ),
        ]

        for item, title, desc in items_to_sell:
            item_card = ctk.CTkFrame(self.shop_scroll, corner_radius=10)
            item_card.pack(fill="x", padx=6, pady=5)

            left_frame = ctk.CTkFrame(item_card, fg_color="transparent")
            left_frame.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            owned = self.store.inventory.get(item.value, 0)
            ctk.CTkLabel(
                left_frame,
                text=f"{title} (In Bag: {owned})",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(anchor="w")

            ctk.CTkLabel(
                left_frame, text=desc, font=ctk.CTkFont(size=10), text_color="gray70"
            ).pack(anchor="w", pady=1)

            price_str = f"Cost: {format_tokens(item.price_tokens)}"
            btn = ctk.CTkButton(
                item_card,
                text=f"Buy ({price_str})",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda i=item: self.action_buy_item(i),
                width=140,
                height=30,
            )
            btn.pack(side="right", padx=12, pady=8)

        # Eggs list
        egg_tiers = [
            (
                EggTier.UNCOMMON,
                "🥚 Uncommon Egg",
                "Guarantees an Uncommon or higher starter Pokémon (Hatch: 6M tokens).",
                EggTier.UNCOMMON.price_tokens,
            ),
            (
                EggTier.RARE,
                "🥚 Rare Egg",
                "Guarantees a Rare or Legendary tier Pokémon like Dratini, Bagon (Hatch: 15M tokens).",
                EggTier.RARE.price_tokens,
            ),
            (
                EggTier.LEGENDARY,
                "🥚 Legendary Egg",
                "Guarantees a Legendary Pokémon like Mewtwo, Rayquaza (Hatch: 35M tokens).",
                EggTier.LEGENDARY.price_tokens,
            ),
        ]

        for tier, title, desc, price in egg_tiers:
            egg_card = ctk.CTkFrame(self.shop_scroll, corner_radius=10)
            egg_card.pack(fill="x", padx=6, pady=5)

            left_frame = ctk.CTkFrame(egg_card, fg_color="transparent")
            left_frame.pack(side="left", fill="both", expand=True, padx=12, pady=8)

            ctk.CTkLabel(left_frame, text=title, font=ctk.CTkFont(size=13, weight="bold")).pack(
                anchor="w"
            )

            ctk.CTkLabel(
                left_frame, text=desc, font=ctk.CTkFont(size=10), text_color="gray70"
            ).pack(anchor="w", pady=1)

            btn = ctk.CTkButton(
                egg_card,
                text=f"Adopt ({format_tokens(price)})",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda t=tier: self.action_buy_egg(t),
                width=140,
                height=30,
            )
            btn.pack(side="right", padx=12, pady=8)

    def action_buy_item(self, item: ItemKind):
        if self.store.buy_item(item):
            self.dashboard.show_toast(f"✅ Purchased {item.value.replace('_', ' ').title()}!")
            self.refresh()
            self.dashboard.refresh_home_view()
            if self.dashboard.on_update_callback:
                self.dashboard.on_update_callback()
        else:
            self.dashboard.show_toast(
                "❌ Insufficient spendable tokens to purchase item!",
                bg_color="#E74C3C",
                text_color="#FFF",
            )

    def action_buy_egg(self, tier: EggTier):
        if self.store.buy_egg(tier):
            self.dashboard.show_toast(f"🥚 Adopted {tier.value.capitalize()} Egg!")
            self.refresh()
            self.dashboard.refresh_home_view()
            if self.dashboard.on_update_callback:
                self.dashboard.on_update_callback()
        else:
            self.dashboard.show_toast(
                "❌ Insufficient spendable tokens to adopt egg!",
                bg_color="#E74C3C",
                text_color="#FFF",
            )
