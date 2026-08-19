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
from core.audio_manager import (
    play_cry,
    play_sfx_crunch,
    play_sfx_heart,
    play_sfx_levelup,
    play_sfx_pokeball_bounce,
    play_sfx_pokeball_release,
)
from core.companion_store import CeremonyEvent, CompanionStore
from core.models import ItemKind
from core.poke_api import DATA_DIR, get_sprite_path
from core.token_reader import TokenUsageSummary
from ui.dashboard_theme import TYPE_THEMES, get_pokemon_element_type
from ui.treat_overlay import TreatDropWindow

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


def create_pokeball_image(size=(48, 48), is_open=False) -> Image.Image:
    """Generates an aesthetic vector-like Pokéball sprite with optional open lid & energy glow."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size

    # Outer diameter
    pad = int(w * 0.08)
    bbox = (pad, pad, w - pad, h - pad)
    cx, cy = w // 2, h // 2

    if not is_open:
        # Top Red Dome
        draw.pieslice(
            bbox,
            start=180,
            end=360,
            fill=(238, 21, 21, 255),
            outline=(30, 30, 40, 255),
            width=max(2, w // 24),
        )
        # Bottom White Dome
        draw.pieslice(
            bbox,
            start=0,
            end=180,
            fill=(245, 245, 250, 255),
            outline=(30, 30, 40, 255),
            width=max(2, w // 24),
        )
        # Middle Black Band
        band_h = max(2, int(h * 0.10))
        draw.rectangle((pad, cy - band_h // 2, w - pad, cy + band_h // 2), fill=(30, 30, 40, 255))
        # Outer Center Ring
        btn_r = int(w * 0.16)
        draw.ellipse((cx - btn_r, cy - btn_r, cx + btn_r, cy + btn_r), fill=(30, 30, 40, 255))
        # Inner White Button
        inner_r = int(w * 0.10)
        draw.ellipse(
            (cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r),
            fill=(255, 255, 255, 255),
            outline=(180, 180, 190, 255),
            width=1,
        )
        # Specular Highlight on Top Dome
        hl_box = (int(w * 0.22), int(h * 0.16), int(w * 0.40), int(h * 0.28))
        draw.ellipse(hl_box, fill=(255, 120, 120, 200))
    else:
        # Energy Burst Light from inside
        glow_box = (int(w * 0.10), int(h * 0.25), int(w * 0.90), int(h * 0.75))
        draw.ellipse(glow_box, fill=(255, 255, 200, 240))
        # Bottom Half
        draw.pieslice(
            bbox,
            start=0,
            end=180,
            fill=(245, 245, 250, 255),
            outline=(30, 30, 40, 255),
            width=max(2, w // 24),
        )
        # Opened Top Half (Shifted & Rotated upward)
        top_bbox = (pad, pad - int(h * 0.22), w - pad, h - pad - int(h * 0.22))
        draw.pieslice(
            top_bbox,
            start=195,
            end=345,
            fill=(238, 21, 21, 255),
            outline=(30, 30, 40, 255),
            width=max(2, w // 24),
        )
        # Bright center energy core
        draw.ellipse(
            (cx - int(w * 0.14), cy - int(h * 0.08), cx + int(w * 0.14), cy + int(h * 0.14)),
            fill=(255, 255, 255, 255),
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
        self.canvas.bind("<Button-3>", self._show_context_menu)
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

        # Behavioral states: "idle", "sleeping", "burning", "seeking_food", "eating"
        self._pet_state = "idle"
        self._last_token_change_time = time.time()
        self._sleep_item_id = None
        self._burn_item_id = None
        self._wiggle_offset_x = 0
        self._bounce_offset_y = 0
        self._wiggling = False

        # Active treat overlay
        self._active_treat: TreatDropWindow | None = None

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

        # Play Pokéball Entrance Intro Animation on startup if enabled
        if (
            getattr(self.store, "spawn_intro_enabled", True)
            and not self.store.is_egg
            and self.store.active
        ):
            self.root.after(120, self.play_spawn_intro_animation)

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
        if self._is_dragging or (self.bubble_window and self.bubble_window.winfo_exists()):
            self._halt_walking()
            return

        # Food Seeking State Machine
        if self._pet_state == "seeking_food":
            if not self._active_treat or self._active_treat.is_despawned:
                self._pet_state = "idle"
                self._halt_walking()
                self._schedule_next_roam(2000)
                return

            treat_cx, _ = self._active_treat.get_center_coords()
            target_pet_x = treat_cx - (self.pet_size // 2)
            distance = target_pet_x - self.x

            if abs(distance) <= 14:
                # Arrived at treat! Trigger eating sequence
                self._eat_active_treat()
                return

            # Turn towards treat
            if distance < 0 and self.facing_direction != "left":
                self.set_facing_direction("left")
            elif distance > 0 and self.facing_direction != "right":
                self.set_facing_direction("right")

            step_size = 4 if distance > 0 else -4
            self.x += step_size
            self._walk_step_counter += 1

            # Rapid energetic bouncing hop towards food
            self._step_hop_y = -abs(int(8.0 * math.sin(self._walk_step_counter * 0.65)))
            self._step_sway_x = int(3.0 * math.sin(self._walk_step_counter * 0.35))

            if self._walk_step_counter % 4 == 0:
                dust_x = (
                    (self.pet_size // 2) - 20
                    if self.facing_direction == "right"
                    else (self.pet_size // 2) + 20
                )
                dust_y = self.pet_size - 18
                self.anim.float_emoji("💨", dust_x, dust_y, duration_ms=220)

            self.root.geometry(f"{self.pet_size}x{self.pet_size}+{self.x}+{self.y}")
            self._walk_step_job = self.root.after(25, self._walk_step)
            return

        # Normal Autonomous Roaming
        if not self.store.roaming_enabled or self._roam_state != "walking":
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
            self.y = max(top, min(bottom - 20, event.y_root - self._drag_offset_y))
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

    def _show_context_menu(self, event):
        """Displays interactive popup context menu on right-click."""
        self.pause_roaming()
        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#181825",
            fg="#CDD6F4",
            activebackground="#313244",
            activeforeground="#89B4FA",
            font=("Segoe UI", 9),
        )

        candies = self.store.inventory.get(ItemKind.RARE_CANDY.value, 0)
        berries = self.store.inventory.get(ItemKind.ORAN_BERRY.value, 0)
        is_active_poke = not self.store.is_egg and self.store.active is not None

        # Treat dropping options
        candy_state = tk.NORMAL if (candies > 0 and is_active_poke) else tk.DISABLED
        berry_state = tk.NORMAL if (berries > 0 and is_active_poke) else tk.DISABLED
        pet_state = tk.NORMAL if is_active_poke else tk.DISABLED

        menu.add_command(
            label=f"🍬 Drop Rare Candy ({candies} in Bag)",
            command=lambda: self.drop_treat(ItemKind.RARE_CANDY.value),
            state=candy_state,
        )
        menu.add_command(
            label=f"🫐 Drop Oran Berry ({berries} in Bag)",
            command=lambda: self.drop_treat(ItemKind.ORAN_BERRY.value),
            state=berry_state,
        )
        menu.add_command(
            label="🖐️ Pet Companion (+💖 Affection)",
            command=self._on_pet_clicked,
            state=pet_state,
        )
        menu.add_separator()
        menu.add_command(label="📊 Open Dashboard", command=self.open_dashboard)

        roam_label = (
            "🐾 Roaming: Wandering ON"
            if self.store.roaming_enabled
            else "🐾 Roaming: Stationary OFF"
        )
        menu.add_command(label=roam_label, command=self.toggle_roaming)
        menu.add_command(label="🧲 Snap to Taskbar", command=self.snap_to_taskbar)
        menu.add_command(label="🎪 Replay Entrance Intro", command=self.play_spawn_intro_animation)
        menu.add_separator()
        menu.add_command(label="❌ Hide Companion", command=self.hide_pet)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def toggle_roaming(self):
        """Toggles autonomous wandering on/off."""
        self.set_roaming_enabled(not self.store.roaming_enabled)

    def hide_pet(self):
        """Hides the desktop pet window."""
        self.root.withdraw()
        self.hide_bubble()

    def drop_treat(self, item_kind: str, start_x: int | None = None, start_y: int | None = None):
        """Spawns falling treat on desktop and directs pet to run and eat it."""
        if self.store.is_egg or not self.store.active:
            return

        if self._active_treat and not self._active_treat.is_despawned:
            return

        if self.store.inventory.get(item_kind, 0) <= 0:
            self.anim.float_emoji("❌ Out of Treats!", self.pet_size // 2, 10, duration_ms=1000)
            return

        left, top, right, bottom = get_screen_work_area(self.root)

        if start_x is None or start_y is None:
            # Drop 130px to side of pet
            offset_x = -130 if (self.x > left + 180) else 130
            start_x = max(left + 30, min(right - 70, self.x + offset_x))
            start_y = max(top + 60, self.y - 100)

        # Spawn treat overlay
        self._active_treat = TreatDropWindow(
            item_kind=item_kind,
            start_x=start_x,
            start_y=start_y,
            floor_y=bottom,
            on_landed=self._on_treat_landed,
            on_despawn=self._on_treat_despawned,
        )

        # Wake pet and start food seeking
        self._wake_from_sleep()
        self._halt_walking()
        self._pet_state = "seeking_food"

        # Face treat direction immediately
        if start_x < self.x:
            self.set_facing_direction("left")
        else:
            self.set_facing_direction("right")

        self._walk_step_counter = 0
        self._walk_step()

    def _on_treat_landed(self, center_x: int, center_y: int):
        """Called when treat finishes bouncing and rests on floor."""
        if self._pet_state == "seeking_food" and self._walk_step_job is None:
            self._walk_step()

    def _on_treat_despawned(self):
        """Called if treat expires or is destroyed."""
        self._active_treat = None
        if self._pet_state == "seeking_food":
            self._pet_state = "idle"
            self._schedule_next_roam(2000)

    def _eat_active_treat(self):
        """Eats the treat: plays chewing animation, plays SFX, consumes item, and rewards EXP."""
        if not self._active_treat:
            return

        item_k = self._active_treat.item_kind
        self._active_treat.despawn()
        self._active_treat = None

        self._pet_state = "eating"
        self._halt_walking()

        # Play crunch audio
        if self.store.sound_enabled:
            play_sfx_crunch(volume=0.6)

        # Nibble chewing bounce
        self.anim.bounce(amplitude=8, duration_ms=300, on_offset=self._set_bounce_offset)
        self.anim.float_emoji("😋", self.pet_size // 2, 8, duration_ms=1100)

        # Apply feed mechanics
        success, xp_gained, new_friendship = self.store.feed_treat(item_k)

        # Sparkles and heart burst on happy meal
        self.root.after(
            200,
            lambda: self.anim.sparkle_cluster(
                self.pet_size // 2, self.pet_size // 2, duration_ms=1200
            ),
        )
        self.root.after(
            350,
            lambda: self.anim.float_emoji(
                f"💖 {new_friendship}%", self.pet_size // 2, 4, duration_ms=1000
            ),
        )

        # Check if high friendship milestone reached
        if new_friendship >= 80:
            self.root.after(
                600,
                lambda: self.anim.float_emoji(
                    "⭐ EXP Boost!", self.pet_size // 2, 2, duration_ms=1200
                ),
            )

        if self.bubble_window and self.bubble_window.winfo_exists():
            self.update_bubble_content()

        # Finish eating state in 1.4s
        self.root.after(1400, self._finish_eating)

    def _finish_eating(self):
        self._pet_state = "idle"
        self._schedule_next_roam(3500)

    def _on_pet_clicked(self, event=None):
        """Click reaction: petting interaction (increases friendship), halts walk, turns to user, hops."""
        self._wake_from_sleep()
        self._halt_walking()

        if not self.store.is_egg and self.store.active:
            success, new_f, msg = self.store.pet_companion()
            if success:
                if self.store.sound_enabled:
                    play_sfx_heart(volume=0.6)
                self.anim.bounce(amplitude=20, duration_ms=450, on_offset=self._set_bounce_offset)
                self.anim.float_emoji(f"💖 +5% ({new_f}%)", self.pet_size // 2, 8, duration_ms=1000)
                if self.bubble_window and self.bubble_window.winfo_exists():
                    self.update_bubble_content()
                self._schedule_next_roam(3500)
                return

        # Spring bounce animation fallback
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

    def play_spawn_intro_animation(self):
        """Plays a cinematic Pokéball throw, floor bounce, and emergence flash intro animation."""
        if self.store.is_egg or not self.store.active:
            # Gentle greeting hop for incubating egg
            self.anim.bounce(amplitude=12, duration_ms=350, on_offset=self._set_bounce_offset)
            return

        self._halt_walking()
        self._wake_from_sleep()
        self._pet_state = "intro"

        # Pre-render pokeball images
        ball_size = max(36, int(self.pet_size * 0.52))
        pil_closed = create_pokeball_image((ball_size, ball_size), is_open=False)
        pil_open = create_pokeball_image((ball_size, ball_size), is_open=True)

        self._intro_ball_closed = ImageTk.PhotoImage(pil_closed)
        self._intro_ball_open = ImageTk.PhotoImage(pil_open)

        # Clear canvas
        self.canvas.delete("all")

        cx = self.pet_size // 2
        start_offset_y = -85
        floor_cy = self.pet_size - (ball_size // 2) - 6

        ball_item = self.canvas.create_image(
            cx, cx + start_offset_y, image=self._intro_ball_closed, tags="pokeball_intro"
        )

        def _step_drop(i, total_steps):
            if self._pet_state != "intro":
                return
            t = i / total_steps  # 0.0 -> 1.0
            # Parabolic drop acceleration: y = start_y + (floor_y - start_y) * (t^2)
            current_y = (cx + start_offset_y) + (floor_cy - (cx + start_offset_y)) * (t * t)
            wobble_x = cx + int(3.0 * math.sin(t * math.pi * 3))
            self.canvas.coords(ball_item, wobble_x, current_y)

            if i < total_steps:
                self.root.after(16, lambda: _step_drop(i + 1, total_steps))
            else:
                _on_landed()

        def _on_landed():
            if self.store.sound_enabled:
                play_sfx_pokeball_bounce(0.6)

            # Bounce 1: Jump up 14px
            def _step_bounce1(i, total):
                if self._pet_state != "intro":
                    return
                t = i / total
                h_offset = -int(14 * math.sin(math.pi * t))
                self.canvas.coords(ball_item, cx, floor_cy + h_offset)
                if i < total:
                    self.root.after(15, lambda: _step_bounce1(i + 1, total))
                else:
                    _bounce2()

            def _bounce2():
                if self.store.sound_enabled:
                    play_sfx_pokeball_bounce(0.4)

                def _step_bounce2(i, total):
                    if self._pet_state != "intro":
                        return
                    t = i / total
                    h_offset = -int(5 * math.sin(math.pi * t))
                    self.canvas.coords(ball_item, cx, floor_cy + h_offset)
                    if i < total:
                        self.root.after(15, lambda: _step_bounce2(i + 1, total))
                    else:
                        self.root.after(80, _pop_open)

                _step_bounce2(0, 10)

            _step_bounce1(0, 14)

        def _pop_open():
            if self._pet_state != "intro":
                return
            # Switch to open pokeball image
            self.canvas.itemconfig(ball_item, image=self._intro_ball_open)

            # Play release beam sound
            if self.store.sound_enabled:
                play_sfx_pokeball_release(0.7)

            # Flash white & sparkle cluster
            self.anim.flash_white(duration_ms=450)
            self.anim.sparkle_cluster(cx, floor_cy - 10, duration_ms=900)

            # Emerge Pokémon!
            self.root.after(180, _emerge_pokemon)

        def _emerge_pokemon():
            if self._pet_state != "intro":
                return
            # Delete pokeball
            self.canvas.delete("pokeball_intro")
            self._intro_ball_closed = None
            self._intro_ball_open = None

            # Reset state to idle so animate() draws sprite
            self._pet_state = "idle"

            # Triumphant emergence double jump
            self.anim.bounce(amplitude=22, duration_ms=500, on_offset=self._set_bounce_offset)
            self.anim.float_emoji("✨", cx, 8, duration_ms=1100)

            # Play Pokemon Cry
            if self.store.sound_enabled and self.store.active:
                play_cry(self.store.active.species_id, volume=0.7)

            # Schedule normal wandering
            self._schedule_next_roam(3500)

        # Start drop animation: 18 frames (~280ms)
        _step_drop(0, 18)

    def animate(self):
        if self._pet_state == "intro":
            # Intro animation is actively controlling the canvas
            self.anim_job = self.root.after(80, self.animate)
            return

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
            xp_txt = (
                f"+{format_tokens(event.xp_amount)} EXP" if event.xp_amount > 0 else "🍬 Delicious!"
            )
            self.anim.float_emoji(xp_txt, self.pet_size // 2, 10, duration_ms=1200)
            self.anim.bounce(amplitude=10, duration_ms=300, on_offset=self._set_bounce_offset)
            if self.store.sound_enabled:
                play_sfx_levelup(volume=0.4)

        elif event.event_type == CeremonyEvent.FRIENDSHIP_UP:
            self.anim.float_emoji(
                f"💖 +{event.friendship_amount}%", self.pet_size // 2, 10, duration_ms=1200
            )
            self.anim.bounce(amplitude=14, duration_ms=350, on_offset=self._set_bounce_offset)
            if self.store.sound_enabled:
                play_sfx_heart(volume=0.5)

        elif event.event_type == CeremonyEvent.MINT_CHANGE:
            self.anim.sparkle_cluster(self.pet_size // 2, self.pet_size // 2, duration_ms=900)
            self.anim.float_emoji(
                f"🌿 {event.new_nature}", self.pet_size // 2, 10, duration_ms=1100
            )

        self._schedule_next_roam(4000)

    def _draw_pill(
        self, canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, r: int, color: str
    ):
        w = x2 - x1
        h = y2 - y1
        if w <= 0 or h <= 0:
            return
        if w < 2 * r:
            r = max(1, w // 2)
        if h < 2 * r:
            r = max(1, h // 2)
        canvas.create_arc(
            x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=180, fill=color, outline=color
        )
        canvas.create_arc(
            x2 - 2 * r, y1, x2, y2, start=270, extent=180, fill=color, outline=color
        )
        if x2 - r > x1 + r:
            canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline=color)

    def _draw_progress_bar(self, pct: float, fill_color: str, bg_color: str = "#313244"):
        if not self.progress_canvas or not self.progress_canvas.winfo_exists():
            return
        self.progress_canvas.delete("all")
        w = self.progress_canvas.winfo_width()
        if w <= 1:
            w = 190
        h = self.progress_canvas.winfo_height()
        if h <= 1:
            h = 8
        r = h // 2

        # Background trough
        self._draw_pill(self.progress_canvas, 0, 0, w, h, r, bg_color)

        # Progress fill
        clamped_pct = min(100.0, max(0.0, pct))
        fill_w = int((w * clamped_pct) / 100.0)
        if fill_w > 0:
            fill_w = max(fill_w, h)
            fill_w = min(fill_w, w)
            self._draw_pill(self.progress_canvas, 0, 0, fill_w, h, r, fill_color)

    def show_bubble(self, event=None):
        self.pause_roaming()
        if self.bubble_window and self.bubble_window.winfo_exists():
            return

        self.bubble_window = tk.Toplevel(self.root)
        self.bubble_window.overrideredirect(True)
        self.bubble_window.wm_attributes("-topmost", True)
        self.bubble_window.config(bg="#313244")

        # Outer border frame for crisp 1px theme border
        self.bubble_border = tk.Frame(self.bubble_window, bg="#313244", padx=1, pady=1)
        self.bubble_border.pack(fill="both", expand=True)

        self.bubble_frame = tk.Frame(self.bubble_border, bg="#181825", padx=14, pady=10)
        self.bubble_frame.pack(fill="both", expand=True)

        # Header Row
        header_row = tk.Frame(self.bubble_frame, bg="#181825")
        header_row.pack(fill="x", pady=(0, 2))

        self.lbl_title = tk.Label(
            header_row, text="", font=("Segoe UI", 10, "bold"), fg="#CDD6F4", bg="#181825"
        )
        self.lbl_title.pack(side="left")

        self.lbl_badge = tk.Label(
            header_row,
            text="",
            font=("Segoe UI", 8, "bold"),
            fg="#CDD6F4",
            bg="#313244",
            padx=6,
            pady=1,
        )
        self.lbl_badge.pack(side="right")

        self.lbl_sub = tk.Label(
            self.bubble_frame, text="", font=("Segoe UI", 8), fg="#A6ADC8", bg="#181825"
        )
        self.lbl_sub.pack(anchor="w", pady=(0, 6))

        # Progress Section
        prog_header = tk.Frame(self.bubble_frame, bg="#181825")
        prog_header.pack(fill="x", pady=(0, 2))

        self.lbl_prog_title = tk.Label(
            prog_header,
            text="Evolution Progress",
            font=("Segoe UI", 8, "bold"),
            fg="#BAC2DE",
            bg="#181825",
        )
        self.lbl_prog_title.pack(side="left")

        self.lbl_prog_pct = tk.Label(
            prog_header, text="0%", font=("Segoe UI", 8, "bold"), fg="#89B4FA", bg="#181825"
        )
        self.lbl_prog_pct.pack(side="right")

        # Custom Canvas Progress Bar
        self.progress_canvas = tk.Canvas(
            self.bubble_frame, width=190, height=8, bg="#181825", highlightthickness=0
        )
        self.progress_canvas.pack(fill="x", pady=(2, 3))

        self.lbl_prog_detail = tk.Label(
            self.bubble_frame, text="", font=("Segoe UI", 8), fg="#6C7086", bg="#181825"
        )
        self.lbl_prog_detail.pack(anchor="w", pady=(0, 4))

        # Separator Line
        self.bubble_sep = tk.Frame(self.bubble_frame, bg="#313244", height=1)
        self.bubble_sep.pack(fill="x", pady=(2, 6))

        # Stats Section
        self.lbl_friendship = tk.Label(
            self.bubble_frame, text="", font=("Segoe UI", 8), fg="#F472B6", bg="#181825"
        )
        self.lbl_friendship.pack(anchor="w", pady=(0, 2))

        self.lbl_today = tk.Label(
            self.bubble_frame, text="", font=("Segoe UI", 8), fg="#FAB387", bg="#181825"
        )
        self.lbl_today.pack(anchor="w")

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
            sub = f"Incubating • Tier {self.store.egg_tier.value.capitalize()}"
            pct = self.store.progress_percentage * 100
            prog_title = "Incubation Progress"
            prog_detail = f"{format_tokens(self.store.egg_usage)} / {format_tokens(self.store.current_threshold)} Tokens"
            fill_color = "#89B4FA"
            border_color = "#45475A"
            title_color = "#CDD6F4"
            badge_text = "EGG"
            badge_bg = "#313244"
            badge_fg = "#89B4FA"
            self.lbl_friendship.pack_forget()
            today_text = f"🔥 Today: {format_tokens(self.summary.today_tokens)} Tokens"
        else:
            elem_type = get_pokemon_element_type(self.store.active.species_id)
            theme = TYPE_THEMES.get(elem_type, TYPE_THEMES["normal"])

            shiny_star = " ✨" if self.store.active.is_shiny else ""
            title = f"{self.store.active.species_name}{shiny_star}"
            stage_str = f"Form {self.store.active.stage_index + 1}/{self.store.active.total_forms}"
            sub = f"{theme.get('icon', '⭐')} {self.store.active.nature.value} • {stage_str}"
            pct = self.store.progress_percentage * 100
            title_color = "#F9E79F" if self.store.active.is_shiny else "#CDD6F4"

            rarity_val = self.store.active.rarity.value
            badge_text = rarity_val.upper()
            badge_fg = RARITY_COLORS.get(rarity_val, "#CDD6F4")
            badge_bg = theme.get("badge_bg", "#313244")

            prog_title = "Evolution Progress"
            prog_detail = f"{format_tokens(self.store.active.used_at_stage)} / {format_tokens(self.store.current_threshold)} Tokens"
            fill_color = theme.get("primary", "#2ECC71")
            border_color = theme.get("border", "#313244")

            f_bonus = " (⭐ +10% EXP Boost)" if self.store.active.friendship >= 80 else ""
            friendship_text = f"💖 Friendship: {self.store.active.friendship}%{f_bonus}"
            today_text = f"🔥 Today: {format_tokens(self.summary.today_tokens)} Tokens"

            self.lbl_friendship.pack(anchor="w", pady=(0, 2), before=self.lbl_today)
            self.lbl_friendship.config(text=friendship_text)

        self.bubble_border.config(bg=border_color)
        self.lbl_title.config(text=title, fg=title_color)
        self.lbl_badge.config(text=badge_text, fg=badge_fg, bg=badge_bg)
        self.lbl_sub.config(text=sub)
        self.lbl_prog_title.config(text=prog_title)
        self.lbl_prog_pct.config(text=f"{pct:.1f}%", fg=fill_color)
        self.lbl_prog_detail.config(text=prog_detail)
        self.lbl_today.config(text=today_text)

        # Redraw smooth progress bar
        self.bubble_window.update_idletasks()
        self._draw_progress_bar(pct, fill_color)

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
        if self._active_treat:
            try:
                self._active_treat.despawn()
            except Exception:
                pass
            self._active_treat = None
        self.anim.cancel_all()
        self.hide_bubble()
        self.root.destroy()
