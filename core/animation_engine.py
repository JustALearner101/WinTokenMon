"""
Reusable Tkinter animation engine for WinTokenMon desktop pet.
Handles smooth bounce curves, float physics, opacity fades, and particle trails.
"""

import math
import tkinter as tk
from collections.abc import Callable


class AnimationController:
    """Manages scheduled animations on a Tkinter canvas with automatic cleanup."""

    def __init__(self, canvas: tk.Canvas, root: tk.Tk):
        self.canvas = canvas
        self.root = root
        self._jobs: list[str] = []
        self._wiggle_active = False

    def cancel_all(self):
        """Cancels all active scheduled animation frame callbacks."""
        for job_id in self._jobs:
            try:
                self.root.after_cancel(job_id)
            except Exception:
                pass
        self._jobs.clear()
        self._wiggle_active = False

    def _schedule(self, delay_ms: int, fn: Callable):
        job = self.root.after(delay_ms, fn)
        self._jobs.append(job)
        return job

    # ── Bounce (spring-like vertical displacement) ──
    def bounce(
        self,
        amplitude: int = 14,
        duration_ms: int = 400,
        fps: int = 30,
        on_offset: Callable[[int], None] | None = None,
    ):
        """Quick bounce: sprite jumps up then settles back with damped sine oscillation."""
        frames = max(1, duration_ms * fps // 1000)
        frame_ms = max(10, duration_ms // frames)
        self._bounce_step(0, frames, amplitude, frame_ms, 0, on_offset)

    def _bounce_step(
        self,
        i: int,
        total: int,
        amp: int,
        dt: int,
        prev_offset: int,
        on_offset: Callable[[int], None] | None = None,
    ):
        if on_offset is not None:
            if i >= total:
                on_offset(0)
                return
            t = i / total
            y_offset = -int(amp * math.sin(math.pi * t) * math.exp(-2.5 * t))
            on_offset(y_offset)
            self._schedule(
                dt, lambda: self._bounce_step(i + 1, total, amp, dt, y_offset, on_offset)
            )
            return

        # Canvas move fallback when on_offset is not used
        if prev_offset != 0:
            try:
                self.canvas.move("sprite", 0, -prev_offset)
            except Exception:
                pass

        if i >= total:
            return

        t = i / total  # 0.0 -> 1.0
        # Damped sine: y = -amp * sin(pi * t) * exp(-2.5 * t)
        y_offset = -int(amp * math.sin(math.pi * t) * math.exp(-2.5 * t))
        try:
            self.canvas.move("sprite", 0, y_offset)
        except Exception:
            pass

        self._schedule(dt, lambda: self._bounce_step(i + 1, total, amp, dt, y_offset, None))

    # ── Float-Up Emoji Reaction ──
    def float_emoji(
        self, emoji: str, start_x: int, start_y: int, duration_ms: int = 900, fps: int = 24
    ):
        """Floats an emoji upward while shrinking/fading out."""
        try:
            text_id = self.canvas.create_text(
                start_x,
                start_y,
                text=emoji,
                font=("Segoe UI Emoji", 18),
                fill="white",
                tags="emoji_float",
            )
        except Exception:
            return

        frames = max(1, duration_ms * fps // 1000)
        frame_ms = max(15, duration_ms // frames)
        self._float_step(text_id, 0, frames, start_x, start_y, frame_ms)

    def _float_step(self, tid, i: int, total: int, start_x: int, start_y: int, dt: int):
        if i >= total:
            try:
                self.canvas.delete(tid)
            except Exception:
                pass
            return

        t = i / total
        new_y = start_y - int(45 * t)  # Float 45px upward
        font_size = max(6, int(18 * (1.0 - t * 0.5)))
        try:
            self.canvas.coords(tid, start_x, new_y)
            self.canvas.itemconfig(tid, font=("Segoe UI Emoji", font_size))
        except Exception:
            return

        self._schedule(dt, lambda: self._float_step(tid, i + 1, total, start_x, start_y, dt))

    # ── Egg Wiggle (Horizontal shake oscillation for egg near hatch) ──
    def start_wiggle(self, on_offset: Callable[[int], None]):
        """Continuous wiggle oscillation for egg at >=90% progress."""
        if self._wiggle_active:
            return
        self._wiggle_active = True
        self._wiggle_step(on_offset, 0)

    def stop_wiggle(self):
        self._wiggle_active = False

    def _wiggle_step(self, on_offset: Callable[[int], None], frame: int):
        if not self._wiggle_active:
            on_offset(0)
            return

        # Shake ±4px left and right rapidly
        offset_x = int(4 * math.sin(frame * 0.4))
        on_offset(offset_x)
        self._schedule(40, lambda: self._wiggle_step(on_offset, frame + 1))

    # ── White Flash Overlay (Ceremony Flash) ──
    def flash_white(self, duration_ms: int = 700, fps: int = 20):
        """Flashes white overlay over canvas and fades out."""
        try:
            w = max(10, self.canvas.winfo_width())
            h = max(10, self.canvas.winfo_height())
            rect_id = self.canvas.create_rectangle(
                0, 0, w, h, fill="white", outline="", stipple="gray75", tags="flash_overlay"
            )
        except Exception:
            return

        frames = max(1, duration_ms * fps // 1000)
        frame_ms = max(15, duration_ms // frames)
        self._flash_step(rect_id, 0, frames, frame_ms)

    def _flash_step(self, rid, i: int, total: int, dt: int):
        if i >= total:
            try:
                self.canvas.delete(rid)
            except Exception:
                pass
            return

        t = i / total
        stipples = ["gray75", "gray50", "gray25", "gray12", ""]
        idx = min(len(stipples) - 1, int(t * len(stipples)))
        if idx >= len(stipples) - 1:
            try:
                self.canvas.delete(rid)
            except Exception:
                pass
            return

        try:
            self.canvas.itemconfig(rid, stipple=stipples[idx])
        except Exception:
            return

        self._schedule(dt, lambda: self._flash_step(rid, i + 1, total, dt))

    # ── Sparkle Cluster (for Mint / Shiny Ceremony) ──
    def sparkle_cluster(self, cx: int, cy: int, duration_ms: int = 1000):
        """Staggered sparkle ✨ emojis appearing around center coordinates."""
        positions = [(-16, -12, 18), (14, -8, 14), (0, 16, 12), (-12, 12, 10), (16, 12, 14)]
        tids = []
        for dx, dy, size in positions:
            try:
                tid = self.canvas.create_text(
                    cx + dx, cy + dy, text="✨", font=("Segoe UI Emoji", size), tags="sparkle"
                )
                tids.append(tid)
            except Exception:
                pass

        self._schedule(duration_ms, lambda: self.canvas.delete("sparkle"))
