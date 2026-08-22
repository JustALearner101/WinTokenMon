"""
Windows System Tray integration using pystray
"""

import threading
from collections.abc import Callable

import pystray
from PIL import Image, ImageDraw

from core.companion_store import CompanionStore
from core.token_reader import TokenUsageSummary

from .desktop_pet import format_tokens


def create_tray_icon_image() -> Image.Image:
    """Creates a cute Pokéball icon for the system tray."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer circle border
    draw.ellipse((4, 4, 60, 60), fill=None, outline=(30, 30, 30, 255), width=3)

    # Top red half
    draw.pieslice(
        (4, 4, 60, 60),
        start=180,
        end=360,
        fill=(239, 83, 80, 255),
        outline=(30, 30, 30, 255),
        width=2,
    )
    # Bottom white half
    draw.pieslice(
        (4, 4, 60, 60),
        start=0,
        end=180,
        fill=(245, 245, 245, 255),
        outline=(30, 30, 30, 255),
        width=2,
    )

    # Middle black dividing line
    draw.line((4, 32, 60, 32), fill=(30, 30, 30, 255), width=4)

    # Center circle button
    draw.ellipse((22, 22, 42, 42), fill=(255, 255, 255, 255), outline=(30, 30, 30, 255), width=3)
    draw.ellipse((27, 27, 37, 37), fill=(220, 220, 220, 255), outline=(30, 30, 30, 255), width=2)

    return img


class SystemTrayManager:
    def __init__(
        self,
        store: CompanionStore,
        on_open_dashboard: Callable,
        on_toggle_pet: Callable,
        on_refresh: Callable,
        on_exit: Callable,
        on_toggle_roaming: Callable | None = None,
        on_switch_mode: Callable | None = None,
    ):
        self.store = store
        self.on_open_dashboard = on_open_dashboard
        self.on_toggle_pet = on_toggle_pet
        self.on_refresh = on_refresh
        self.on_exit = on_exit
        self.on_toggle_roaming = on_toggle_roaming
        self.on_switch_mode = on_switch_mode

        self.icon_image = create_tray_icon_image()
        self.tray_icon = None

    def _build_menu(self):
        mode_label = (
            "🐾 Mode: Full Desktop Pet"
            if self.store.display_mode == "compact_hud"
            else "📊 Mode: Compact HUD Pill"
        )
        return pystray.Menu(
            pystray.MenuItem("🐾 Open Dashboard", lambda: self.on_open_dashboard()),
            pystray.MenuItem("🔄 Force Token Refresh", lambda: self.on_refresh()),
            pystray.MenuItem(mode_label, lambda: self.on_switch_mode()),
            pystray.MenuItem("👁️ Toggle Desktop Pet", lambda: self.on_toggle_pet()),
            pystray.MenuItem("🚶 Toggle Roaming (Walk Around)", lambda: self._toggle_roam()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit WinTokenMon", lambda: self.on_exit()),
        )

    def refresh_mode_label(self):
        """Rebuilds the tray menu so the display-mode label reflects current state."""
        if not self.tray_icon:
            return
        try:
            self.tray_icon.menu = self._build_menu()
            self.tray_icon.update_menu()
        except Exception:
            pass

    def _toggle_roam(self):
        new_val = not getattr(self.store, "roaming_enabled", True)
        self.store.roaming_enabled = new_val
        self.store.save()
        if self.on_toggle_roaming:
            self.on_toggle_roaming(new_val)

    def start(self):
        self.tray_icon = pystray.Icon(
            "WinTokenMon", self.icon_image, "WinTokenMon — Windows", menu=self._build_menu()
        )
        # Run tray in separate daemon thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def update_tooltip(self, summary: TokenUsageSummary):
        if not self.tray_icon:
            return

        today_str = format_tokens(summary.today_tokens)
        if self.store.is_egg:
            comp_str = f"Egg ({self.store.progress_percentage * 100:.0f}%)"
        else:
            comp_str = (
                f"{self.store.active.species_name} ({self.store.progress_percentage * 100:.0f}%)"
            )

        self.tray_icon.title = f"WinTokenMon | Today: {today_str} | {comp_str}"

    def send_notification(self, title: str, message: str):
        """Sends a native Windows toast/balloon notification via the tray icon."""
        if not self.tray_icon:
            return
        try:
            self.tray_icon.notify(message, title)
        except Exception:
            pass

    def stop(self):
        if self.tray_icon:
            self.tray_icon.stop()
