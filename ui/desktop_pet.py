"""
Floating Desktop Pet Window for Windows
Transparent, draggable, animated Pokémon sprite with rich interactive feedback,
autonomous roaming (walking left/right with sprite flipping and waddling gait),
state reactions (idle sleep, burst burn), ceremony animations, and sound effects.
"""

import json
import math
import os
import random
import time
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from PIL import Image, ImageDraw, ImageSequence, ImageTk

from core.animation_engine import AnimationController
from core.audio_manager import play_cry, play_sfx_levelup
from core.companion_store import CeremonyEvent, CompanionStore
from core.poke_api import DATA_DIR, get_sprite_path
from core.token_reader import TokenUsageSummary

WINDOW_POS_FILE = os.path.join(DATA_DIR, "window_pos.json")

SIZE_MAP = {"small": 80, "medium": 110, "large": 150}

RARITY_COLORS = {
    "common": "#8E8E93",
    "uncommon": "#34C759",
    "rare": "#007AFF",
    "legendary": "#FF9500",
}


def format_tokens(num: int) -> str:
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def create_egg_image(size=(96, 96)) -> Image.Image:
    """Generates an aesthetic Pokémon egg image."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size
    # Outer egg oval
    bbox = (int(w * 0.16), int(h * 0.08), int(w * 0.84), int(h * 0.92))
    draw.ellipse(bbox, fill=(255, 248, 220, 255), outline=(139, 90, 43, 255), width=max(2, w // 35))
    # Spots on egg
    draw.ellipse(
        (int(w * 0.28), int(h * 0.26), int(w * 0.44), int(h * 0.44)), fill=(100, 181, 246, 220)
    )
    draw.ellipse(
        (int(w * 0.48), int(h * 0.48), int(w * 0.70), int(h * 0.68)), fill=(239, 83, 80, 220)
    )
    draw.ellipse(
        (int(w * 0.26), int(h * 0.56), int(w * 0.42), int(h * 0.72)), fill=(129, 199, 132, 220)
    )
    return img


def get_screen_work_area(window=None) -> tuple[int, int, int, int]:
    """
    Returns (left, top, right, bottom) of the monitor work area (excluding taskbar) in physical pixels.
    Supports Windows high-DPI scaling and multi-monitor setups.
    """
    try:
        import ctypes
        from ctypes import wintypes

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        user32 = ctypes.windll.user32
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)

        hwnd = window.winfo_id() if window and window.winfo_exists() else None
        h_mon = (
            user32.MonitorFromWindow(wintypes.HWND(hwnd), 2)
            if hwnd
            else user32.MonitorFromPoint(wintypes.POINT(0, 0), 1)
        )

        if h_mon and user32.GetMonitorInfoW(h_mon, ctypes.byref(mi)):
            if mi.rcWork.right > mi.rcWork.left and mi.rcWork.bottom > mi.rcWork.top:
                return mi.rcWork.left, mi.rcWork.top, mi.rcWork.right, mi.rcWork.bottom
    except Exception:
        pass

    try:
        import ctypes

        w = ctypes.windll.user32.GetSystemMetrics(0)
        h = ctypes.windll.user32.GetSystemMetrics(1)
        if w > 0 and h > 0:
            return 0, 0, w, h
    except Exception:
        pass

    if window:
        try:
            return 0, 0, window.winfo_screenwidth(), window.winfo_screenheight()
        except Exception:
            pass

    return 0, 0, 1920, 1080


class DesktopPetWindow:
    def __init__(self, store: CompanionStore, on_open_dashboard: Callable | None = None):
        self.store = store
        self.on_open_dashboard = on_open_dashboard
        self.summary = TokenUsageSummary()

        self.root = tk.Tk()
        self.root.title("WinTokenMon Companion")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)

        # Transparent background key color for Windows
        self.trans_color = "#000001"
        self.root.config(bg=self.trans_color)
        self.root.wm_attributes("-transparentcolor", self.trans_color)

        # Pet size & scaling
        preset = self.store.pet_size_preset
        self.pet_size = SIZE_MAP.get(preset, 110)
        self.load_position()

        # Canvas for animated sprite and overlay effects
        self.canvas = tk.Canvas(
            self.root,
            width=self.pet_size,
            height=self.pet_size,
            bg=self.trans_color,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Animation Controller
        self.anim = AnimationController(self.canvas, self.root)

        # Dragging & Click differentiation mechanics (absolute root tracking)
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._click_start_pos = None
        self._is_dragging = False

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self.open_dashboard)
        self.canvas.bind("<Button-3>", self.open_dashboard)
        self.canvas.bind("<Enter>", self.show_bubble)
        self.canvas.bind("<Leave>", self.hide_bubble)

        # Bubble tooltip window
        self.bubble_window = None

        # Sprite animation frames & dual directions
        self.frames_right = []
        self.frames_left = []
        self.frames = []
        self.frame_idx = 0
        self.facing_direction = "right"  # "right" or "left"
        self.anim_job = None
        self.current_loaded_species_id = None
        self.current_loaded_shiny = None

        # Behavioral states: "idle", "sleeping", "burning"
        self._pet_state = "idle"
        self._last_token_change_time = time.time()
        self._sleep_item_id = None
        self._burn_item_id = None
        self._wiggle_offset_x = 0
        self._bounce_offset_y = 0
        self._wiggling = False

        # Autonomous Roaming (Walking) State Machine
        self._roam_state = "idle"  # "idle", "walking", "paused"
        self._target_x = self.x
        self._walk_step_job = None
        self._idle_roam_job = None
        self._walk_step_counter = 0
        self._step_hop_y = 0
        self._step_sway_x = 0

        # Apply initial opacity
        self.apply_opacity(self.store.pet_opacity)

        self.update_sprite()
        self.animate()

        # Start background managers
        self._schedule_idle_check()
        self._schedule_next_roam()

        # Ensure window is visible and on top
        self.root.deiconify()
        self.root.lift()

    def load_position(self):
        left, top, right, bottom = get_screen_work_area(self.root)
        default_x = right - self.pet_size - 24
        default_y = bottom - int(self.pet_size * 0.90)

        if os.path.exists(WINDOW_POS_FILE):
            try:
                with open(WINDOW_POS_FILE) as f:
                    pos = json.load(f)
                    raw_x = pos.get("x", default_x)
                    raw_y = pos.get("y", default_y)
            except Exception:
                raw_x, raw_y = default_x, default_y
        else:
            raw_x, raw_y = default_x, default_y

        # Clamp within accessible screen boundaries (allowing feet to reach taskbar)
        self.x = max(left - (self.pet_size // 3), min(right - 40, raw_x))
        self.y = max(top, min(bottom - 20, raw_y))

        self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")

    def save_position(self):
        try:
            with open(WINDOW_POS_FILE, "w") as f:
                json.dump({"x": self.x, "y": self.y}, f)
        except Exception:
            pass

    def apply_size(self, preset: str):
        """Updates pet window size based on preset ('small', 'medium', 'large')."""
        new_size = SIZE_MAP.get(preset, 110)
        self.pet_size = new_size
        self.store.pet_size_preset = preset
        self.store.save()

        left, top, right, bottom = get_screen_work_area(self.root)
        self.x = max(left - (self.pet_size // 3), min(right - 40, self.x))
        self.y = max(top, min(bottom - 20, self.y))

        self.canvas.config(width=self.pet_size, height=self.pet_size)
        self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")
        self.save_position()
        self.update_sprite()

    def apply_opacity(self, opacity_pct: int):
        """Sets overall window opacity (50-100%)."""
        try:
            alpha = max(0.5, min(1.0, opacity_pct / 100.0))
            self.root.attributes("-alpha", alpha)
        except Exception:
            pass

    def snap_to_taskbar(self):
        """Positions pet right above the Windows taskbar on the right."""
        self._halt_walking()
        left, top, right, bottom = get_screen_work_area(self.root)
        self.x = right - self.pet_size - 24
        self.y = bottom - int(self.pet_size * 0.90)
        self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")
        self.save_position()

    def set_facing_direction(self, direction: str):
        """Changes the facing direction of the sprite ('left' or 'right') with a turnaround hop."""
        if direction not in ("left", "right") or direction == self.facing_direction:
            return
        self.facing_direction = direction
        self.frames = self.frames_left if direction == "left" else self.frames_right
        if not self.frames:
            self.frames = self.frames_right
        # Quick turnaround hop
        self.anim.bounce(amplitude=8, duration_ms=220, on_offset=self._set_bounce_offset)

    # ─────────────────────────────────────────────────────────────
    # AUTONOMOUS ROAMING & WALKING ANIMATION ENGINE
    # ─────────────────────────────────────────────────────────────
    def set_roaming_enabled(self, enabled: bool):
        """Toggles autonomous wandering on/off."""
        self.store.roaming_enabled = enabled
        self.store.save()
        if not enabled:
            self._halt_walking()
        else:
            self._schedule_next_roam(delay_ms=2000)

    def _schedule_next_roam(self, delay_ms: int | None = None):
        """Schedules the next autonomous walk interval."""
        if self._idle_roam_job:
            try:
                self.root.after_cancel(self._idle_roam_job)
            except Exception:
                pass
            self._idle_roam_job = None

        if delay_ms is None:
            # Random wait between 6 to 14 seconds before wandering
            delay_ms = random.randint(6000, 14000)

        self._idle_roam_job = self.root.after(delay_ms, self._decide_and_start_roam)

    def _decide_and_start_roam(self):
        """Decides whether to walk and picks target destination coordinate."""
        self._idle_roam_job = None

        # Guard checks: don't walk if disabled, egg, sleeping, dragging, or tooltip open
        if (
            not self.store.roaming_enabled
            or self.store.is_egg
            or self._pet_state == "sleeping"
            or self._is_dragging
            or (self.bubble_window and self.bubble_window.winfo_exists())
        ):
            self._schedule_next_roam()
            return

        left, top, right, bottom = get_screen_work_area(self.root)
        min_x = left + 16
        max_x = right - self.pet_size - 16

        # Pick random delta X between 70px and 220px in either direction
        direction_sign = random.choice([-1, 1])
        # If too close to edge, bias towards center
        if self.x < left + 120:
            direction_sign = 1
        elif self.x > max_x - 120:
            direction_sign = -1

        delta_x = direction_sign * random.randint(80, 220)
        target_x = max(min_x, min(max_x, self.x + delta_x))

        if abs(target_x - self.x) < 25:
            self._schedule_next_roam(3000)
            return

        # Turn to face destination
        if target_x < self.x:
            self.set_facing_direction("left")
        else:
            self.set_facing_direction("right")

        self._roam_state = "walking"
        self._target_x = target_x
        self._walk_step_counter = 0
        self._walk_step()

    def _walk_step(self):
        """Performs a single walking frame translation with dynamic step-hop & dust puffs."""
        if (
            not self.store.roaming_enabled
            or self._roam_state != "walking"
            or self._is_dragging
            or (self.bubble_window and self.bubble_window.winfo_exists())
        ):
            self._halt_walking()
            return

        distance = self._target_x - self.x
        if abs(distance) <= 2:
            # Arrived at destination!
            self.x = self._target_x
            self._halt_walking()
            self.save_position()
            self._schedule_next_roam()
            return

        # Step 2px per tick
        step_size = 2 if distance > 0 else -2
        self.x += step_size
        self._walk_step_counter += 1

        # Footstep hop physics: pronounced rhythmic vertical bounce on footsteps
        self._step_hop_y = -abs(int(6.0 * math.sin(self._walk_step_counter * 0.55)))
        self._step_sway_x = int(2.5 * math.sin(self._walk_step_counter * 0.27))

        # Footstep Dust Emitter: every 7 steps, puff a tiny dust particle behind trailing foot
        if self._walk_step_counter % 7 == 0:
            dust_x = (
                (self.pet_size // 2) - 20
                if self.facing_direction == "right"
                else (self.pet_size // 2) + 20
            )
            dust_y = self.pet_size - 18
            self.anim.float_emoji("💨", dust_x, dust_y, duration_ms=280)

        self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")

        # Schedule next step in 35ms (~28 FPS smooth glide)
        self._walk_step_job = self.root.after(35, self._walk_step)

    def _halt_walking(self):
        """Immediately halts walking movement and resets step offsets."""
        if self._walk_step_job:
            try:
                self.root.after_cancel(self._walk_step_job)
            except Exception:
                pass
            self._walk_step_job = None

        self._roam_state = "idle"
        self._step_hop_y = 0
        self._step_sway_x = 0
        try:
            self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")
        except Exception:
            pass

    def pause_roaming(self):
        """Pauses roaming temporarily (e.g. during hover/tooltip)."""
        self._halt_walking()
        if self._idle_roam_job:
            try:
                self.root.after_cancel(self._idle_roam_job)
            except Exception:
                pass
            self._idle_roam_job = None

    def resume_roaming(self):
        """Resumes roaming after pause."""
        if self.store.roaming_enabled and not self.store.is_egg:
            self._schedule_next_roam(4000)

    # ─────────────────────────────────────────────────────────────
    # MOUSE INPUT & CLICK HANDLERS
    # ─────────────────────────────────────────────────────────────
    def _on_press(self, event):
        self._click_start_pos = (event.x_root, event.y_root)
        self._drag_offset_x = event.x_root - self.x
        self._drag_offset_y = event.y_root - self.y
        self._is_dragging = False
        self.pause_roaming()

    def _on_motion(self, event):
        if self._click_start_pos:
            dx = abs(event.x_root - self._click_start_pos[0])
            dy = abs(event.y_root - self._click_start_pos[1])
            if dx > 4 or dy > 4:
                self._is_dragging = True

        if self._is_dragging:
            left, top, right, bottom = get_screen_work_area(self.root)
            self.x = max(
                left - (self.pet_size // 3), min(right - 40, event.x_root - self._drag_offset_x)
            )
            self.y = max(
                top, min(bottom - 20, event.y_root - self._drag_offset_y)
            )
            self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")
            if self.bubble_window and self.bubble_window.winfo_exists():
                self.position_bubble()

    def _on_release(self, event):
        if self._is_dragging:
            self.save_position()
            self.resume_roaming()
        else:
            self._on_pet_clicked(event)
        self._click_start_pos = None
        self._is_dragging = False

    def _on_pet_clicked(self, event=None):
        """Click reaction: halts walk, turns to user, double-hops and floats emoji."""
        self._wake_from_sleep()
        self._halt_walking()

        # Spring bounce animation
        self.anim.bounce(amplitude=16, duration_ms=450, on_offset=self._set_bounce_offset)

        # Float random reaction emoji
        emojis = ["❤️", "⚡", "✨", "🎵", "💪", "🔥", "😊", "🌟", "❗"]
        reaction = random.choice(emojis)
        self.anim.float_emoji(reaction, self.pet_size // 2, 12, duration_ms=900)

        # Play Pokemon cry if active and sound enabled
        if not self.store.is_egg and self.store.sound_enabled:
            play_cry(self.store.active.species_id, volume=0.5)

        # Schedule next walk after a brief pause
        self._schedule_next_roam(3500)

    def on_tokens_changed(self, delta: int):
        """Called when new tokens are burned."""
        if delta > 0:
            self._last_token_change_time = time.time()
            self._wake_from_sleep()
            if delta >= 500_000:
                self._enter_burn_mode()

    def _schedule_idle_check(self):
        """Checks every 30s if companion should enter nap/sleep mode."""
        self.root.after(30000, self._check_idle_status)

    def _check_idle_status(self):
        try:
            elapsed = time.time() - self._last_token_change_time
            if elapsed > 1200 and self._pet_state != "sleeping":  # 20 minutes idle
                self._enter_sleep_mode()
        except Exception:
            pass
        self._schedule_idle_check()

    def _enter_sleep_mode(self):
        self._pet_state = "sleeping"
        self._halt_walking()
        self._animate_sleep_bubble()

    def _animate_sleep_bubble(self):
        if self._pet_state != "sleeping":
            if self._sleep_item_id:
                try:
                    self.canvas.delete(self._sleep_item_id)
                except Exception:
                    pass
                self._sleep_item_id = None
            return

        try:
            # Gentle bob of 💤 emoji in top-right
            t = time.time()
            bob_y = int(14 + 3 * math.sin(t * 2.0))
            x_pos = self.pet_size - 14

            if not self._sleep_item_id:
                self._sleep_item_id = self.canvas.create_text(
                    x_pos,
                    bob_y,
                    text="💤",
                    font=("Segoe UI Emoji", max(10, self.pet_size // 9)),
                    fill="#89B4FA",
                    tags="sleep_tag",
                )
            else:
                self.canvas.coords(self._sleep_item_id, x_pos, bob_y)
        except Exception:
            pass

        self.root.after(80, self._animate_sleep_bubble)

    def _wake_from_sleep(self):
        if self._pet_state == "sleeping":
            self._pet_state = "idle"
            if self._sleep_item_id:
                try:
                    self.canvas.delete(self._sleep_item_id)
                except Exception:
                    pass
                self._sleep_item_id = None
            self._last_token_change_time = time.time()
            self._schedule_next_roam(2500)

    def _enter_burn_mode(self):
        if self._pet_state == "burning":
            return
        self._pet_state = "burning"
        try:
            if not self._burn_item_id:
                self._burn_item_id = self.canvas.create_text(
                    self.pet_size - 14,
                    self.pet_size - 14,
                    text="🔥",
                    font=("Segoe UI Emoji", max(12, self.pet_size // 8)),
                    fill="#FFA000",
                    tags="burn_tag",
                )
        except Exception:
            pass
        # Auto cooldown after 25s
        self.root.after(25000, self._exit_burn_mode)

    def _exit_burn_mode(self):
        self._pet_state = "idle"
        if self._burn_item_id:
            try:
                self.canvas.delete(self._burn_item_id)
            except Exception:
                pass
            self._burn_item_id = None

    def open_dashboard(self, event=None):
        if self.on_open_dashboard:
            self.on_open_dashboard()

    def update_sprite(self):
        """Generates both right-facing and left-flipped PhotoImage frames for directional walking."""
        self.frames_right = []
        self.frames_left = []
        self.frame_idx = 0

        if self.store.is_egg:
            img = create_egg_image((self.pet_size, self.pet_size))
            tk_img = ImageTk.PhotoImage(img)
            self.frames_right = [tk_img]
            self.frames_left = [tk_img]
            self.current_loaded_species_id = 0
            self.current_loaded_shiny = False
        else:
            sp_id = self.store.active.species_id
            shiny = self.store.active.is_shiny
            self.current_loaded_species_id = sp_id
            self.current_loaded_shiny = shiny

            sprite_path = get_sprite_path(sp_id, shiny)
            if sprite_path and os.path.exists(sprite_path):
                try:
                    pil_img = Image.open(sprite_path)
                    for frame in ImageSequence.Iterator(pil_img):
                        # Original Showdown battle sprite naturally faces LEFT
                        f_left = frame.convert("RGBA").resize(
                            (self.pet_size, self.pet_size), Image.Resampling.NEAREST
                        )
                        # Flipped sprite faces RIGHT
                        f_right = f_left.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                        self.frames_left.append(ImageTk.PhotoImage(f_left))
                        self.frames_right.append(ImageTk.PhotoImage(f_right))
                except Exception:
                    pass

        if not self.frames_right:
            # Fallback egg
            img = create_egg_image((self.pet_size, self.pet_size))
            tk_img = ImageTk.PhotoImage(img)
            self.frames_right = [tk_img]
            self.frames_left = [tk_img]

        self.frames = self.frames_left if self.facing_direction == "left" else self.frames_right

    def animate(self):
        if self.frames:
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            self.canvas.delete("sprite")
            cx = (self.pet_size // 2) + self._wiggle_offset_x + self._step_sway_x
            cy = (self.pet_size // 2) + self._step_hop_y + self._bounce_offset_y
            self.canvas.create_image(cx, cy, image=self.frames[self.frame_idx], tags="sprite")

        # Egg wiggle when close to hatching (>=90% progress)
        if self.store.is_egg and self.store.progress_percentage >= 0.9:
            if not self._wiggling:
                self._wiggling = True
                self.anim.start_wiggle(self._set_wiggle_offset)
        elif self._wiggling:
            self._wiggling = False
            self.anim.stop_wiggle()
            self._wiggle_offset_x = 0

        # Dynamic Frame Cadence: 50ms while walking (accelerated pace), 100ms when resting
        delay = 50 if self._roam_state == "walking" else 100
        self.anim_job = self.root.after(delay, self.animate)

    def _set_wiggle_offset(self, offset: int):
        self._wiggle_offset_x = offset

    def _set_bounce_offset(self, offset: int):
        self._bounce_offset_y = offset

    def refresh_state(self, summary: TokenUsageSummary):
        self.summary = summary

        # Check if active pokemon changed
        current_id = 0 if self.store.is_egg else self.store.active.species_id
        current_shiny = False if self.store.is_egg else self.store.active.is_shiny

        if (
            current_id != self.current_loaded_species_id
            or current_shiny != self.current_loaded_shiny
        ):
            self.update_sprite()

        # Play any pending ceremonies in the queue
        self._process_ceremony_queue()

        if self.bubble_window and self.bubble_window.winfo_exists():
            self.update_bubble_content()

    def _process_ceremony_queue(self):
        """Pops and plays pending visual and audio ceremonies."""
        while self.store.ceremony_queue:
            event = self.store.ceremony_queue.popleft()
            self._play_ceremony(event)

    def _play_ceremony(self, event: CeremonyEvent):
        """Orchestrates rich celebration effects (flash, spring bounce, cries, sparkles)."""
        self._halt_walking()
        if event.event_type in (CeremonyEvent.HATCH, CeremonyEvent.EVOLVE):
            # 1. White flash overlay
            self.anim.flash_white(duration_ms=700)
            # 2. Delayed sprite switch for anticipation
            self.root.after(200, self.update_sprite)
            # 3. Spring bounce
            self.root.after(
                250,
                lambda: self.anim.bounce(
                    amplitude=20, duration_ms=550, on_offset=self._set_bounce_offset
                ),
            )
            # 4. Shiny sparkles if shiny
            if event.is_shiny:
                self.root.after(
                    450,
                    lambda: self.anim.sparkle_cluster(
                        self.pet_size // 2, self.pet_size // 2, duration_ms=1800
                    ),
                )
            # 5. Play Pokemon Cry
            if self.store.sound_enabled:
                self.root.after(350, lambda: play_cry(event.species_id, volume=0.7))
                self.root.after(350, lambda: play_sfx_levelup(volume=0.5))

        elif event.event_type == CeremonyEvent.GRADUATE:
            self.anim.flash_white(duration_ms=600)
            self.root.after(
                200,
                lambda: self.anim.sparkle_cluster(
                    self.pet_size // 2, self.pet_size // 2, duration_ms=1500
                ),
            )
            self.root.after(300, self.update_sprite)
            if self.store.sound_enabled:
                self.root.after(300, lambda: play_sfx_levelup(volume=0.6))

        elif event.event_type == CeremonyEvent.CANDY_XP:
            self.anim.float_emoji("+100M EXP", self.pet_size // 2, 10, duration_ms=1200)
            self.anim.bounce(amplitude=10, duration_ms=300, on_offset=self._set_bounce_offset)
            if self.store.sound_enabled:
                play_sfx_levelup(volume=0.4)

        elif event.event_type == CeremonyEvent.MINT_CHANGE:
            self.anim.sparkle_cluster(self.pet_size // 2, self.pet_size // 2, duration_ms=900)
            self.anim.float_emoji(
                f"🌿 {event.new_nature}", self.pet_size // 2, 10, duration_ms=1100
            )

        self._schedule_next_roam(4000)

    def show_bubble(self, event=None):
        self.pause_roaming()
        if self.bubble_window and self.bubble_window.winfo_exists():
            return

        self.bubble_window = tk.Toplevel(self.root)
        self.bubble_window.overrideredirect(True)
        self.bubble_window.wm_attributes("-topmost", True)
        self.bubble_window.config(bg="#181825", bd=1, relief="solid")

        self.bubble_frame = tk.Frame(self.bubble_window, bg="#181825", padx=12, pady=8)
        self.bubble_frame.pack()

        self.lbl_title = tk.Label(
            self.bubble_frame, text="", font=("Segoe UI", 10, "bold"), fg="#CDD6F4", bg="#181825"
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_sub = tk.Label(
            self.bubble_frame, text="", font=("Segoe UI", 8), fg="#A6ADC8", bg="#181825"
        )
        self.lbl_sub.pack(anchor="w", pady=(0, 4))

        self.progress_bar = ttk.Progressbar(
            self.bubble_frame, orient="horizontal", length=160, mode="determinate"
        )
        self.progress_bar.pack(anchor="w", pady=2)

        self.lbl_stats = tk.Label(
            self.bubble_frame, text="", font=("Segoe UI", 8), fg="#89B4FA", bg="#181825"
        )
        self.lbl_stats.pack(anchor="w", pady=(2, 0))

        self.update_bubble_content()
        self.position_bubble()

    def position_bubble(self):
        if not self.bubble_window or not self.bubble_window.winfo_exists():
            return
        self.bubble_window.update_idletasks()
        bw = self.bubble_window.winfo_width()
        bh = self.bubble_window.winfo_height()
        bx = max(10, self.x + (self.pet_size // 2) - (bw // 2))
        by = max(10, self.y - bh - 8)
        self.bubble_window.geometry(f"+{bx}+{by}")

    def update_bubble_content(self):
        if not self.bubble_window or not self.bubble_window.winfo_exists():
            return

        if self.store.is_egg:
            title = "🥚 Pokémon Egg"
            sub = f"Incubating: {format_tokens(self.store.egg_usage)} / {format_tokens(self.store.current_threshold)}"
            pct = self.store.progress_percentage * 100
            title_color = "#CDD6F4"
        else:
            shiny_star = " ✨" if self.store.active.is_shiny else ""
            title = f"{self.store.active.species_name}{shiny_star}"
            stage_str = f"Form {self.store.active.stage_index + 1}/{self.store.active.total_forms}"
            sub = f"{self.store.active.nature.value} • {self.store.active.rarity.value.capitalize()} ({stage_str})"
            pct = self.store.progress_percentage * 100
            title_color = RARITY_COLORS.get(self.store.active.rarity.value, "#CDD6F4")

        stats = f"🔥 Today's Tokens: {format_tokens(self.summary.today_tokens)}"

        self.lbl_title.config(text=title, fg=title_color)
        self.lbl_sub.config(text=sub)
        self.progress_bar["value"] = pct
        self.lbl_stats.config(text=stats)

    def hide_bubble(self, event=None):
        if self.bubble_window and self.bubble_window.winfo_exists():
            self.bubble_window.destroy()
            self.bubble_window = None
        self.resume_roaming()

    def destroy(self):
        if self.anim_job:
            self.root.after_cancel(self.anim_job)
        self._halt_walking()
        if self._idle_roam_job:
            try:
                self.root.after_cancel(self._idle_roam_job)
            except Exception:
                pass
        self.anim.cancel_all()
        self.hide_bubble()
        self.root.destroy()
