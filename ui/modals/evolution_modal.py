"""
Cinematic Evolution Ceremony Modal for WinTokenMon
Features classic Game Boy / DS style pulsing morphing animation,
sound effects, Pokémon cries, and celebration sparkles.
"""

import math
import os
import random
import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk
from PIL import Image, ImageTk

from core.audio_manager import play_cry, play_sfx_levelup
from core.companion_store import CompanionStore
from core.poke_api import get_sprite_path
from ui.dashboard_theme import TYPE_THEMES, get_pokemon_element_type


class EvolutionModal:
    """Dramatic, cinematic Evolution Modal window."""

    def __init__(
        self,
        parent,
        store: CompanionStore,
        old_species_id: int,
        old_species_name: str,
        new_species_id: int,
        new_species_name: str,
        is_shiny: bool = False,
        on_complete: Callable | None = None,
    ):
        self.parent = parent
        self.store = store
        self.old_species_id = old_species_id
        self.old_species_name = old_species_name
        self.new_species_id = new_species_id
        self.new_species_name = new_species_name
        self.is_shiny = is_shiny
        self.on_complete = on_complete

        self.win = ctk.CTkToplevel(parent)
        self.win.title("✨ Pokémon Evolution")
        self.win.geometry("500x540")
        self.win.minsize(460, 500)
        self.win.lift()
        self.win.grab_set()

        elem = get_pokemon_element_type(new_species_id)
        self.theme = TYPE_THEMES.get(elem, TYPE_THEMES["normal"])

        self._anim_running = True
        self._anim_frame = 0
        self._particles = []

        self._load_sprites()
        self._build_ui()
        self._start_ceremony()

    def _load_sprites(self):
        """Loads and pre-processes sprites for old and new forms."""
        old_path = get_sprite_path(self.old_species_id, self.is_shiny)
        new_path = get_sprite_path(self.new_species_id, self.is_shiny)

        def load_img(path):
            if path and os.path.exists(path):
                try:
                    im = Image.open(path)
                    im.seek(0)
                    return im.convert("RGBA")
                except Exception:
                    pass
            # Fallback placeholder
            im = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
            return im

        self.img_old_raw = load_img(old_path)
        self.img_new_raw = load_img(new_path)

        # Silhouette versions (bright glowing white)
        def make_silhouette(img):
            r, g, b, a = img.split()
            white = Image.new("RGBA", img.size, (255, 255, 255, 255))
            white.putalpha(a)
            return white

        self.img_old_white = make_silhouette(self.img_old_raw)
        self.img_new_white = make_silhouette(self.img_new_raw)

    def _build_ui(self):
        self.main_card = ctk.CTkFrame(
            self.win,
            fg_color="#181825",
            corner_radius=14,
            border_width=2,
            border_color=self.theme.get("border", "#313244"),
        )
        self.main_card.pack(fill="both", expand=True, padx=16, pady=16)

        # Top Badge
        badge_frame = ctk.CTkFrame(
            self.main_card, fg_color=self.theme.get("badge_bg", "#313244"), corner_radius=20
        )
        badge_frame.pack(pady=(16, 6))

        shiny_str = " ✨ SHINY" if self.is_shiny else ""
        self.lbl_badge = ctk.CTkLabel(
            badge_frame,
            text=f"🧬 EVOLUTION CEREMONY{shiny_str}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.theme.get("primary", "#F9E79F"),
        )
        self.lbl_badge.pack(padx=16, pady=4)

        # Header Question / Status
        self.lbl_title = ctk.CTkLabel(
            self.main_card,
            text=f"What? {self.old_species_name} is evolving!",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#CDD6F4",
            wraplength=420,
            justify="center",
        )
        self.lbl_title.pack(pady=(4, 10))

        # Canvas for Particle Animation and Pulsing Sprites
        self.canvas = tk.Canvas(
            self.main_card, width=380, height=240, bg="#11111B", highlightthickness=0
        )
        self.canvas.pack(pady=4)

        # Progress / Subtitle description
        self.lbl_desc = ctk.CTkLabel(
            self.main_card,
            text="✨ The power of token energy is surging...",
            font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
            text_color="#A6ADC8",
        )
        self.lbl_desc.pack(pady=(8, 12))

        # Action Button (initially disabled/hidden until evolution finishes)
        self.btn_done = ctk.CTkButton(
            self.main_card,
            text="⏳ Evolving...",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#313244",
            hover_color="#45475A",
            state="disabled",
            height=36,
            command=self._finish_and_close,
        )
        self.btn_done.pack(fill="x", padx=40, pady=(0, 16))

        self.win.protocol("WM_DELETE_WINDOW", self._finish_and_close)

    def _start_ceremony(self):
        """Starts the multi-phase evolution animation loop."""
        self._anim_frame = 0
        self._particles = []
        self._animate_step()

    def _animate_step(self):
        if not self._anim_running or not self.win.winfo_exists():
            return

        self._anim_frame += 1
        frame = self._anim_frame
        cw, ch = 380, 240
        cx, cy = cw // 2, ch // 2

        self.canvas.delete("all")

        # Phase 1: Anticipation & Build-up (Frames 0 - 45, ~1.5s)
        if frame < 45:
            # Pulsing background glow rings
            pulse = math.sin(frame * 0.2) * 15
            r = int(55 + pulse)
            self.canvas.create_oval(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                fill="#1E1E2E",
                outline=self.theme.get("border", "#313244"),
                width=2,
            )
            # Render old sprite gently breathing
            scale = 1.0 + math.sin(frame * 0.15) * 0.08
            self._render_sprite(self.img_old_raw, cx, cy, scale)

        # Phase 2: Morphing Flash (Frames 45 - 120, ~2.5s)
        elif frame < 120:
            rel = (frame - 45) / 75.0
            freq = 0.2 + rel * 0.6  # Frequency increases over time
            toggle = math.sin(frame * freq) > 0

            # Scale pulses dramatically
            scale = 1.0 + math.sin(frame * freq * 0.8) * 0.25

            # Background glowing energy sphere
            glow_r = int(60 + rel * 35 + random.randint(-5, 5))
            self.canvas.create_oval(
                cx - glow_r,
                cy - glow_r,
                cx + glow_r,
                cy + glow_r,
                fill="#313244" if toggle else "#1E1E2E",
                outline=self.theme.get("primary", "#F9E79F"),
                width=2,
            )

            # Alternate between silhouette and actual sprites
            if toggle:
                img = self.img_new_white if rel > 0.5 else self.img_old_white
            else:
                img = self.img_new_raw if rel > 0.5 else self.img_old_raw

            self._render_sprite(img, cx, cy, scale)

            # Spawn energetic spark particles
            if random.random() < 0.6:
                angle = random.uniform(0, 2 * math.pi)
                spd = random.uniform(2, 6)
                self._particles.append(
                    {
                        "x": cx,
                        "y": cy,
                        "vx": math.cos(angle) * spd,
                        "vy": math.sin(angle) * spd,
                        "life": random.randint(12, 24),
                        "color": random.choice(
                            [self.theme.get("primary", "#F9E79F"), "#FFFFFF", "#89B4FA"]
                        ),
                        "size": random.randint(2, 4),
                    }
                )

        # Phase 3: Climax Explosion & Reveal (Frame 120, triggers sound & final state)
        elif frame == 120:
            # Trigger actual evolution logic in companion store!
            if self.store.is_ready_to_evolve:
                self.store.evolve()

            if self.store.sound_enabled:
                play_sfx_levelup(volume=0.7)
                self.win.after(300, lambda: play_cry(self.new_species_id, volume=0.8))

            # Spawn huge particle explosion
            for _ in range(40):
                angle = random.uniform(0, 2 * math.pi)
                spd = random.uniform(3, 9)
                self._particles.append(
                    {
                        "x": cx,
                        "y": cy,
                        "vx": math.cos(angle) * spd,
                        "vy": math.sin(angle) * spd,
                        "life": random.randint(25, 45),
                        "color": random.choice(
                            [
                                self.theme.get("primary", "#F9E79F"),
                                "#FFFFFF",
                                "#F38BA8",
                                "#A6E3A1",
                                "#89B4FA",
                            ]
                        ),
                        "size": random.randint(3, 6),
                    }
                )

            # Update UI labels
            self.lbl_title.configure(
                text=f"🎉 Congratulations!\nYour {self.old_species_name} evolved into {self.new_species_name}!",
                text_color=self.theme.get("primary", "#A6E3A1"),
            )
            self.lbl_desc.configure(
                text=f"Form {self.store.active.stage_index + 1}/{self.store.active.total_forms} • {self.store.active.rarity.value.capitalize()}",
                text_color="#CDD6F4",
            )
            self.btn_done.configure(
                text="🌟 Continue Journey",
                state="normal",
                fg_color=self.theme.get("primary", "#2563EB"),
                hover_color=self.theme.get("secondary", "#1D4ED8"),
            )

        # Phase 4: Final Celebration & Idle Sparkles (Frame > 120)
        else:
            # Glowing celebration aura
            r = int(75 + math.sin(frame * 0.1) * 6)
            self.canvas.create_oval(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                fill="#181825",
                outline=self.theme.get("primary", "#A6E3A1"),
                width=2,
            )
            self._render_sprite(self.img_new_raw, cx, cy, 1.15)

            # Gentle floating sparkles
            if random.random() < 0.3:
                self._particles.append(
                    {
                        "x": cx + random.randint(-60, 60),
                        "y": cy + random.randint(-60, 60),
                        "vx": random.uniform(-0.5, 0.5),
                        "vy": random.uniform(-1.5, -0.5),
                        "life": random.randint(15, 30),
                        "color": random.choice(
                            ["#F9E79F", "#FFFFFF", self.theme.get("primary", "#89B4FA")]
                        ),
                        "size": random.randint(2, 4),
                    }
                )

        # Update and render particles
        for p in self._particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0:
                self._particles.remove(p)
            else:
                sz = p["size"]
                self.canvas.create_oval(
                    p["x"] - sz, p["y"] - sz, p["x"] + sz, p["y"] + sz, fill=p["color"], outline=""
                )

        self.win.after(33, self._animate_step)

    def _render_sprite(self, base_img: Image.Image, cx: int, cy: int, scale: float):
        """Renders scaled PIL image onto canvas."""
        base_w, base_h = base_img.size
        w = max(10, int(base_w * scale))
        h = max(10, int(base_h * scale))

        resized = base_img.resize((w, h), Image.Resampling.NEAREST)
        self._cur_tk_img = ImageTk.PhotoImage(resized)
        self.canvas.create_image(cx, cy, image=self._cur_tk_img)

    def _finish_and_close(self):
        self._anim_running = False
        try:
            if self.on_complete:
                self.on_complete()
            self.win.destroy()
        except Exception:
            pass
