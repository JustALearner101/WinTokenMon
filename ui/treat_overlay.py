"""
Transparent Desktop Treat Overlay for WinTokenMon
Simulates physical gravity drop, damped floor bounces, and resting on the taskbar.
"""

import math
import tkinter as tk
from collections.abc import Callable


class TreatDropWindow:
    """
    Lightweight floating window representing a dropped treat (Rare Candy or Berry) on the desktop.
    Simulates gravity drop and damped bounce against the monitor workarea floor.
    """

    def __init__(
        self,
        item_kind: str,
        start_x: int,
        start_y: int,
        floor_y: int,
        on_landed: Callable[[int, int], None] | None = None,
        on_despawn: Callable[[], None] | None = None,
    ):
        self.item_kind = item_kind
        self.x = start_x
        self.y = start_y
        self.floor_y = floor_y
        self.on_landed = on_landed
        self.on_despawn = on_despawn

        self.size = 48
        self.vy = -3.5  # Slight upward initial arc
        self.gravity = 1.4
        self.restitution = 0.42
        self.bounces = 0
        self.is_landed = False
        self.is_despawned = False

        self._physics_job = None
        self._timeout_job = None
        self._bob_job = None
        self._bob_angle = 0.0

        # Trans color
        self.trans_color = "#000001"

        # Create window
        self.win = tk.Toplevel()
        self.win.title("WinTokenMon Treat")
        self.win.overrideredirect(True)
        self.win.wm_attributes("-topmost", True)
        self.win.config(bg=self.trans_color)
        self.win.wm_attributes("-transparentcolor", self.trans_color)

        self.canvas = tk.Canvas(
            self.win,
            width=self.size,
            height=self.size,
            bg=self.trans_color,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Determine icon emoji
        if "candy" in item_kind.lower():
            emoji = "🍬"
        elif "oran" in item_kind.lower() or "berry" in item_kind.lower():
            emoji = "🫐"
        elif "mint" in item_kind.lower():
            emoji = "🌿"
        else:
            emoji = "🎁"

        self.text_item = self.canvas.create_text(
            self.size // 2,
            self.size // 2,
            text=emoji,
            font=("Segoe UI Emoji", 24),
            tags="treat_icon",
        )

        self.win.geometry(f"{self.size}x{self.size}+{int(self.x)}+{int(self.y)}")

        # Start gravity physics loop
        self._step_physics()

        # 30s auto-despawn safety timer
        self._timeout_job = self.win.after(30000, self.despawn)

    def _step_physics(self):
        if self.is_despawned or not self.win.winfo_exists():
            return

        self.vy += self.gravity
        self.y += self.vy

        target_floor = self.floor_y - self.size

        if self.y >= target_floor:
            self.y = target_floor
            self.bounces += 1

            if abs(self.vy) > 2.0 and self.bounces < 5:
                self.vy = -self.vy * self.restitution
            else:
                self.vy = 0
                self.is_landed = True

        self.win.geometry(f"{self.size}x{self.size}+{int(self.x)}+{int(self.y)}")

        if not self.is_landed:
            self._physics_job = self.win.after(20, self._step_physics)
        else:
            if self.on_landed:
                try:
                    self.on_landed(int(self.x + self.size // 2), int(self.y + self.size // 2))
                except Exception:
                    pass
            self._start_resting_bob()

    def _start_resting_bob(self):
        """Gentle hover bob and sparkle pulse while resting on the floor."""
        if self.is_despawned or not self.win.winfo_exists():
            return

        self._bob_angle += 0.15
        bob_offset = int(2.5 * math.sin(self._bob_angle))
        self.canvas.coords(self.text_item, self.size // 2, (self.size // 2) + bob_offset)

        self._bob_job = self.win.after(50, self._start_resting_bob)

    def get_center_coords(self) -> tuple[int, int]:
        return int(self.x + self.size // 2), int(self.y + self.size // 2)

    def despawn(self):
        """Cleans up timers and destroys the treat overlay."""
        if self.is_despawned:
            return
        self.is_despawned = True

        if self._physics_job:
            try:
                self.win.after_cancel(self._physics_job)
            except Exception:
                pass
            self._physics_job = None

        if self._timeout_job:
            try:
                self.win.after_cancel(self._timeout_job)
            except Exception:
                pass
            self._timeout_job = None

        if self._bob_job:
            try:
                self.win.after_cancel(self._bob_job)
            except Exception:
                pass
            self._bob_job = None

        if self.on_despawn:
            try:
                self.on_despawn()
            except Exception:
                pass

        try:
            self.win.destroy()
        except Exception:
            pass
