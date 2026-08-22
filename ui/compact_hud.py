"""
Ultra-Compact Floating HUD Capsule (v0.4.0)

A minimal 220x32px always-on-top pill showing live token burn,
velocity speedometer, and companion status as an alternative
presentation mode to the full Desktop Pet.
"""

import tkinter as tk

from core.companion_store import CompanionStore
from core.token_reader import TokenUsageSummary

from .desktop_pet import draw_rounded_pill, format_tokens, get_screen_work_area

HUD_WIDTH = 220
HUD_HEIGHT = 32
TASKBAR_MARGIN = 8

# Catppuccin Mocha palette (matches Dashboard theme)
BG_MANTLE = "#181825"
SURFACE0 = "#313244"
TEXT = "#CDD6F4"
SUBTEXT = "#A6ADC8"
ACCENT_RED = "#F38BA8"
ACCENT_GREEN = "#A6E3A1"
ACCENT_YELLOW = "#F9E2AF"


class CompactHUDWindow:
    def __init__(self, store: CompanionStore, on_switch_mode: callable):
        self.store = store
        self.on_switch_mode = on_switch_mode

        self.win = tk.Toplevel()
        self.win.overrideredirect(True)
        self.win.wm_attributes("-topmost", True)
        try:
            self.win.wm_attributes("-alpha", max(0.5, min(1.0, self.store.hud_opacity / 100.0)))
        except Exception:
            pass
        self.win.configure(bg=BG_MANTLE, highlightthickness=1, highlightbackground=SURFACE0)

        self.canvas = tk.Canvas(
            self.win,
            width=HUD_WIDTH,
            height=HUD_HEIGHT,
            bg=BG_MANTLE,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        # Draw rounded capsule background
        self._draw_capsule()

        self._text_burn = self.canvas.create_text(
            10,
            HUD_HEIGHT // 2,
            anchor="w",
            text="",
            fill=TEXT,
            font=("Segoe UI", 9, "bold"),
        )
        self._text_velocity = self.canvas.create_text(
            118,
            HUD_HEIGHT // 2,
            anchor="w",
            text="",
            fill=SUBTEXT,
            font=("Segoe UI", 8),
        )
        self._text_companion = self.canvas.create_text(
            HUD_WIDTH - 10,
            HUD_HEIGHT // 2,
            anchor="e",
            text="",
            fill=ACCENT_GREEN,
            font=("Segoe UI", 9),
        )

        self._restore_position()
        self._bind_dragging()
        self._bind_actions()

    def _draw_capsule(self):
        r = HUD_HEIGHT // 2
        draw_rounded_pill(self.canvas, 0, 0, HUD_WIDTH, HUD_HEIGHT, r, SURFACE0)

    def _bind_dragging(self):
        self.win.bind("<Button-1>", self._on_drag_start)
        self.win.bind("<B1-Motion>", self._on_drag_motion)
        self.win.bind("<ButtonRelease-1>", self._on_drag_end)
        self.canvas.bind("<Button-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)

    def _bind_actions(self):
        # Double-click anywhere toggles back to Full Pet Mode
        self.win.bind("<Double-Button-1>", lambda e: self.on_switch_mode())
        self.canvas.bind("<Double-Button-1>", lambda e: self.on_switch_mode())

    def _on_drag_start(self, event):
        self._drag_dx = event.x
        self._drag_dy = event.y

    def _on_drag_motion(self, event):
        x = self.win.winfo_x() + event.x - self._drag_dx
        y = self.win.winfo_y() + event.y - self._drag_dy
        self.win.geometry(f"+{x}+{y}")

    def _on_drag_end(self, event):
        self.store.hud_position = {
            "x": self.win.winfo_x(),
            "y": self.win.winfo_y(),
        }
        self.store.save()

    def _restore_position(self):
        pos = getattr(self.store, "hud_position", None)
        if pos and pos.get("x") and pos.get("y"):
            x, y = int(pos["x"]), int(pos["y"])
        else:
            # Default dock: above taskbar near system tray clock
            left, top, right, bottom = get_screen_work_area(self.win)
            x = right - HUD_WIDTH - TASKBAR_MARGIN
            y = bottom - HUD_HEIGHT - TASKBAR_MARGIN
        self.win.geometry(f"{HUD_WIDTH}x{HUD_HEIGHT}+{x}+{y}")

    def update_metrics(self, summary: TokenUsageSummary, velocity_per_min: float):
        """Refreshes the live token burn, velocity speedometer, and companion status."""
        limit = max(1, self.store.daily_token_limit)
        pct = min(100.0, summary.today_tokens / limit * 100.0)
        burn_color = ACCENT_GREEN if pct < 80 else (ACCENT_YELLOW if pct < 100 else ACCENT_RED)

        self.canvas.itemconfigure(
            self._text_burn,
            text=f"🔥 {format_tokens(summary.today_tokens)} ({pct:.1f}%)",
            fill=burn_color,
        )

        vel_str = (
            f"⚡ {format_tokens(int(velocity_per_min))}/min" if velocity_per_min > 0 else "⚡ idle"
        )
        self.canvas.itemconfigure(self._text_velocity, text=vel_str)

        if self.store.is_egg:
            comp_str = f"🥚 {self.store.progress_percentage * 100:.0f}%"
        else:
            comp_str = f"🐾 {self.store.progress_percentage * 100:.0f}%"
        self.canvas.itemconfigure(self._text_companion, text=comp_str)

    def show(self):
        self.win.deiconify()
        self.win.lift()

    def hide(self):
        self.win.withdraw()

    def destroy(self):
        try:
            self.win.destroy()
        except Exception:
            pass
