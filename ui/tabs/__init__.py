"""
UI Tabs Module for WinTokenMon Dashboard
"""

from .home_tab import HomeTabView
from .pokedex_tab import PokedexTabView
from .settings_tab import SettingsTabView
from .shop_tab import ShopTabView

__all__ = [
    "HomeTabView",
    "PokedexTabView",
    "ShopTabView",
    "SettingsTabView",
]
