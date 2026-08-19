"""
Modern CustomTkinter Dashboard Window Coordinator for WinTokenMon
Featuring Modular Tabs (Home/HUD, Pokédex, Shop/Bag, Settings/Preferences),
Dynamic Elemental Accents, In-Memory Sprite Caching, and In-App Toast System.
"""

import os
from collections.abc import Callable

import customtkinter as ctk
from PIL import Image

from core.companion_store import CompanionStore
from core.poke_api import get_sprite_path
from core.token_reader import TokenUsageSummary
from ui.dashboard_theme import (
    NATURE_DETAILS,
    POKEMON_LORE,
    TYPE_THEMES,
    get_pokemon_element_type,
)
from ui.modals import NatureSelectorModal, PokedexInspectorModal
from ui.tabs import (
    HomeTabView,
    PokedexTabView,
    SettingsTabView,
    ShopTabView,
    TrophiesTabView,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Re-exports for backward-compatibility
__all__ = [
    "DashboardWindow",
    "NatureSelectorModal",
    "PokedexInspectorModal",
    "TYPE_THEMES",
    "NATURE_DETAILS",
    "POKEMON_LORE",
    "get_pokemon_element_type",
]


class DashboardWindow:
    """Main window coordinator managing the Tabview, toast banner, and sprite caching."""

    def __init__(
        self,
        store: CompanionStore,
        summary: TokenUsageSummary,
        on_update_callback: Callable | None = None,
        on_test_notification: Callable | None = None,
        on_size_change: Callable[[str], None] | None = None,
        on_opacity_change: Callable[[int], None] | None = None,
        on_taskbar_snap: Callable[[], None] | None = None,
        on_roaming_toggle: Callable[[bool], None] | None = None,
        achievement_engine=None,
    ):
        self.store = store
        self.summary = summary
        self.on_update_callback = on_update_callback
        self.on_test_notification = on_test_notification
        self.on_size_change = on_size_change
        self.on_opacity_change = on_opacity_change
        self.on_taskbar_snap = on_taskbar_snap
        self.on_roaming_toggle = on_roaming_toggle
        self.achievement_engine = achievement_engine

        # In-Memory Sprite Image Cache: (species_id, is_shiny, size) -> CTkImage
        self._sprite_cache: dict[tuple[int, bool, int], ctk.CTkImage] = {}

        # Lazy loading tab views
        self.home_tab_view: HomeTabView | None = None
        self.pokedex_tab_view: PokedexTabView | None = None
        self.trophies_tab_view: TrophiesTabView | None = None
        self.shop_tab_view: ShopTabView | None = None
        self.settings_tab_view: SettingsTabView | None = None

        self._pokedex_loaded = False
        self._trophies_loaded = False
        self._shop_loaded = False
        self._settings_loaded = False

        self.win = ctk.CTkToplevel()
        self.win.title("WinTokenMon — Pokémon Trainer RPG Companion")
        self.win.geometry("820x620")
        self.win.minsize(740, 540)

        # Bring to front initially
        self.win.lift()
        self.win.attributes("-topmost", True)
        self.win.after_idle(self.win.attributes, "-topmost", False)

        # In-App Toast Banner Frame (Top)
        self.toast_frame = ctk.CTkFrame(self.win, fg_color="#2ECC71", corner_radius=8, height=32)
        self.lbl_toast = ctk.CTkLabel(
            self.toast_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#181825",
        )
        self.lbl_toast.pack(side="left", padx=16, pady=4)
        self._toast_hide_job = None

        # Tabview layout with Lazy Loading callback
        self.tabview = ctk.CTkTabview(self.win, command=self._on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=14, pady=12)

        self.tab_home = self.tabview.add("🐾 Companion & HUD")
        self.tab_pokedex = self.tabview.add("📖 Pokédex")
        self.tab_trophies = self.tabview.add("🏆 Trophies")
        self.tab_shop = self.tabview.add("🛒 Shop & Bag")
        self.tab_settings = self.tabview.add("⚙️ Preferences")

        # Load ONLY Home Tab on startup (Instant launch < 0.05s)
        self.home_tab_view = HomeTabView(self.tab_home, self)

    def _on_tab_change(self):
        """Lazy loads tabs on first activation to keep window launch instantaneous."""
        active = self.tabview.get()
        if active == "📖 Pokédex" and not self._pokedex_loaded:
            self.pokedex_tab_view = PokedexTabView(self.tab_pokedex, self)
            self._pokedex_loaded = True
        elif active == "🏆 Trophies" and not self._trophies_loaded:
            if self.achievement_engine is not None:
                self.trophies_tab_view = TrophiesTabView(
                    self.tab_trophies, self.store, self.achievement_engine
                )
            else:
                from core.achievement_engine import AchievementEngine

                self.achievement_engine = AchievementEngine(self.store)
                self.trophies_tab_view = TrophiesTabView(
                    self.tab_trophies, self.store, self.achievement_engine
                )
            self._trophies_loaded = True
        elif active == "🛒 Shop & Bag" and not self._shop_loaded:
            self.shop_tab_view = ShopTabView(self.tab_shop, self)
            self._shop_loaded = True
        elif active == "⚙️ Preferences" and not self._settings_loaded:
            self.settings_tab_view = SettingsTabView(self.tab_settings, self)
            self._settings_loaded = True

    def get_cached_sprite(
        self, species_id: int, is_shiny: bool = False, size: int = 56
    ) -> ctk.CTkImage | None:
        """Retrieves or caches a CTkImage in memory to avoid repeated disk reads."""
        key = (species_id, is_shiny, size)
        if key in self._sprite_cache:
            return self._sprite_cache[key]

        sprite_path = get_sprite_path(species_id, is_shiny)
        if sprite_path and os.path.exists(sprite_path):
            try:
                pil_img = Image.open(sprite_path).convert("RGBA")
                ctk_img = ctk.CTkImage(pil_img, size=(size, size))
                self._sprite_cache[key] = ctk_img
                return ctk_img
            except Exception:
                pass
        return None

    def _get_cached_sprite(
        self, species_id: int, is_shiny: bool = False, size: int = 56
    ) -> ctk.CTkImage | None:
        """Backward-compatible alias for get_cached_sprite."""
        return self.get_cached_sprite(species_id, is_shiny, size)

    def show_toast(self, message: str, bg_color: str = "#2ECC71", text_color: str = "#181825"):
        """Displays an animated in-app toast notification banner."""
        if self._toast_hide_job:
            try:
                self.win.after_cancel(self._toast_hide_job)
            except Exception:
                pass

        self.toast_frame.configure(fg_color=bg_color)
        self.lbl_toast.configure(text=message, text_color=text_color)
        self.toast_frame.pack(fill="x", padx=16, pady=(8, 0), before=self.tabview)
        self._toast_hide_job = self.win.after(3200, self._hide_toast)

    def _hide_toast(self):
        try:
            self.toast_frame.pack_forget()
        except Exception:
            pass
        self._toast_hide_job = None

    def refresh_home_view(self):
        """Refreshes the Home HUD tab view."""
        if self.home_tab_view:
            self.home_tab_view.refresh()

    def refresh_pokedex_tab(self):
        """Refreshes the Pokédex tab view if loaded."""
        if self.pokedex_tab_view and self._pokedex_loaded:
            self.pokedex_tab_view.refresh()

    def refresh_trophies_tab(self):
        """Refreshes the Trophies tab view if loaded."""
        if self.trophies_tab_view and self._trophies_loaded:
            self.trophies_tab_view.refresh()

    def refresh_shop_tab(self):
        """Refreshes the Shop tab view if loaded."""
        if self.shop_tab_view and self._shop_loaded:
            self.shop_tab_view.refresh()

    def update_summary(self, summary: TokenUsageSummary):
        """Updates the active token summary and refreshes the HUD."""
        self.summary = summary
        if self.win.winfo_exists():
            self.refresh_home_view()
            self.refresh_trophies_tab()
