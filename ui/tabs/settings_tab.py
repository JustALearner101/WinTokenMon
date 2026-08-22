"""
Preferences & Settings Tab for WinTokenMon Dashboard
"""

import customtkinter as ctk

from core.audio_manager import play_cry, play_sfx_levelup
from core.companion_store import CompanionStore
from ui.desktop_pet import format_tokens


class SettingsTabView:
    """Manages the Preferences tab: Pet display settings, sound toggles, daily token limit, and danger zone."""

    def __init__(self, parent: ctk.CTkFrame, dashboard):
        self.parent = parent
        self.dashboard = dashboard
        self.store: CompanionStore = dashboard.store

        self._build_ui()

    def _build_ui(self):
        frame = ctk.CTkScrollableFrame(self.parent, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            frame, text="⚙️ Preferences & Customization", font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=14, pady=(8, 12))

        # Desktop Pet Display
        pet_card = ctk.CTkFrame(frame, corner_radius=10)
        pet_card.pack(fill="x", padx=6, pady=(0, 10))

        ctk.CTkLabel(
            pet_card,
            text="🐾 Desktop Pet Display & Position",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        # Size Selector
        size_frame = ctk.CTkFrame(pet_card, fg_color="transparent")
        size_frame.pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkLabel(size_frame, text="Pet Size:", font=ctk.CTkFont(size=11)).pack(
            side="left", padx=(0, 10)
        )

        self.size_btn = ctk.CTkSegmentedButton(
            size_frame,
            values=["Small (80px)", "Medium (110px)", "Large (150px)"],
            command=self.action_change_size,
        )
        current_preset = self.store.pet_size_preset
        preset_map_rev = {
            "small": "Small (80px)",
            "medium": "Medium (110px)",
            "large": "Large (150px)",
        }
        self.size_btn.set(preset_map_rev.get(current_preset, "Medium (110px)"))
        self.size_btn.pack(side="left")

        # Opacity Slider
        op_frame = ctk.CTkFrame(pet_card, fg_color="transparent")
        op_frame.pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkLabel(op_frame, text="Opacity:", font=ctk.CTkFont(size=11)).pack(
            side="left", padx=(0, 14)
        )

        self.opacity_slider = ctk.CTkSlider(
            op_frame,
            from_=50,
            to=100,
            number_of_steps=10,
            command=self.action_change_opacity,
            width=180,
        )
        self.opacity_slider.set(self.store.pet_opacity)
        self.opacity_slider.pack(side="left", padx=(0, 10))

        self.lbl_opacity_val = ctk.CTkLabel(
            op_frame, text=f"{self.store.pet_opacity}%", font=ctk.CTkFont(size=11)
        )
        self.lbl_opacity_val.pack(side="left")

        # Taskbar Snap & Roaming Row
        pos_frame = ctk.CTkFrame(pet_card, fg_color="transparent")
        pos_frame.pack(fill="x", padx=14, pady=(0, 10))

        self.btn_snap = ctk.CTkButton(
            pos_frame,
            text="📌 Snap Above Taskbar",
            width=150,
            height=28,
            command=self.action_snap_taskbar,
        )
        self.btn_snap.pack(side="left", padx=(0, 14))

        self.switch_roaming = ctk.CTkSwitch(
            pos_frame,
            text="Autonomous Roaming (Walk Around)",
            command=self.action_toggle_roaming,
        )
        if getattr(self.store, "roaming_enabled", True):
            self.switch_roaming.select()
        else:
            self.switch_roaming.deselect()
        self.switch_roaming.pack(side="left")

        # Spawn Intro Animation Switch Row
        intro_row = ctk.CTkFrame(pet_card, fg_color="transparent")
        intro_row.pack(fill="x", padx=14, pady=(0, 10))

        self.switch_spawn_intro = ctk.CTkSwitch(
            intro_row,
            text="🔴 Pokéball Entrance Animation on Startup",
            command=self.action_toggle_spawn_intro,
        )
        if getattr(self.store, "spawn_intro_enabled", True):
            self.switch_spawn_intro.select()
        else:
            self.switch_spawn_intro.deselect()
        self.switch_spawn_intro.pack(side="left")

        # Auto-Evolve Switch Row
        evolve_row = ctk.CTkFrame(pet_card, fg_color="transparent")
        evolve_row.pack(fill="x", padx=14, pady=(0, 10))

        self.switch_auto_evolve = ctk.CTkSwitch(
            evolve_row,
            text="⚡ Auto-Evolve Immediately on 100% Token EXP",
            command=self.action_toggle_auto_evolve,
        )
        if getattr(self.store, "auto_evolve_enabled", False):
            self.switch_auto_evolve.select()
        else:
            self.switch_auto_evolve.deselect()
        self.switch_auto_evolve.pack(side="left")

        # Windows Startup Switch Row
        startup_row = ctk.CTkFrame(pet_card, fg_color="transparent")
        startup_row.pack(fill="x", padx=14, pady=(0, 10))

        self.switch_autostart = ctk.CTkSwitch(
            startup_row,
            text="🚀 Launch WinTokenMon on Windows Startup",
            command=self.action_toggle_autostart,
        )
        if getattr(self.store, "autostart_enabled", False):
            self.switch_autostart.select()
        else:
            self.switch_autostart.deselect()
        self.switch_autostart.pack(side="left")

        # Audio Section
        sound_card = ctk.CTkFrame(frame, corner_radius=10)
        sound_card.pack(fill="x", padx=6, pady=(0, 10))

        ctk.CTkLabel(
            sound_card, text="🔊 Audio & Sound Effects", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=14, pady=(10, 4))

        sound_row = ctk.CTkFrame(sound_card, fg_color="transparent")
        sound_row.pack(fill="x", padx=14, pady=(0, 10))

        self.switch_sound = ctk.CTkSwitch(
            sound_row,
            text="Enable Pokémon cries & level-up jingles",
            command=self.action_toggle_sound,
        )
        if self.store.sound_enabled:
            self.switch_sound.select()
        else:
            self.switch_sound.deselect()
        self.switch_sound.pack(side="left", padx=(0, 14))

        self.btn_test_sound = ctk.CTkButton(
            sound_row,
            text="🎵 Test Sound",
            width=110,
            height=28,
            fg_color="#1565C0",
            hover_color="#0D47A1",
            command=self.action_test_sound,
        )
        self.btn_test_sound.pack(side="left")

        # Daily Token Limit & Alerts Section
        limit_card = ctk.CTkFrame(frame, corner_radius=10)
        limit_card.pack(fill="x", padx=6, pady=(0, 10))

        ctk.CTkLabel(
            limit_card,
            text="🎯 Daily Token Limit & Threshold Alerts",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            limit_card,
            text="Set your daily token budget. Windows toast notifications will alert you when you reach 80% and 100% of this limit.",
            font=ctk.CTkFont(size=10),
            text_color="gray70",
            justify="left",
            wraplength=580,
        ).pack(anchor="w", padx=14, pady=(0, 6))

        presets_frame = ctk.CTkFrame(limit_card, fg_color="transparent")
        presets_frame.pack(anchor="w", padx=14, pady=(0, 6))

        ctk.CTkLabel(presets_frame, text="Presets:", font=ctk.CTkFont(size=11)).pack(
            side="left", padx=(0, 6)
        )
        for label, val in [
            ("10M", 10_000_000),
            ("20M", 20_000_000),
            ("50M", 50_000_000),
            ("100M", 100_000_000),
            ("Off", 0),
        ]:
            btn = ctk.CTkButton(
                presets_frame,
                text=label,
                width=55,
                height=24,
                command=lambda v=val: self.action_set_preset_limit(v),
            )
            btn.pack(side="left", padx=3)

        entry_frame = ctk.CTkFrame(limit_card, fg_color="transparent")
        entry_frame.pack(anchor="w", padx=14, pady=(0, 6))

        ctk.CTkLabel(entry_frame, text="Limit (tokens):", font=ctk.CTkFont(size=11)).pack(
            side="left", padx=(0, 6)
        )
        self.entry_limit = ctk.CTkEntry(entry_frame, width=160, height=28)
        self.entry_limit.insert(0, str(self.store.daily_token_limit))
        self.entry_limit.pack(side="left", padx=(0, 6))

        self.btn_save_limit = ctk.CTkButton(
            entry_frame,
            text="💾 Save Limit",
            width=90,
            height=28,
            command=self.action_save_limit,
        )
        self.btn_save_limit.pack(side="left", padx=(0, 6))

        self.btn_test_notif = ctk.CTkButton(
            entry_frame,
            text="🔔 Test Toast Alert",
            fg_color="#E65100",
            hover_color="#BF360C",
            width=130,
            height=28,
            command=self.action_test_notification,
        )
        self.btn_test_notif.pack(side="left")

        self.lbl_limit_status = ctk.CTkLabel(
            limit_card, text="", font=ctk.CTkFont(size=10), text_color="#89B4FA"
        )
        self.lbl_limit_status.pack(anchor="w", padx=14, pady=(0, 10))
        self.refresh_limit_status()

        # Connected Local AI Tools Section
        tools_card = ctk.CTkFrame(frame, corner_radius=10)
        tools_card.pack(fill="x", padx=6, pady=(0, 10))

        ctk.CTkLabel(
            tools_card,
            text="🤖 Connected Local AI Tools",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        tools_list = [
            "• Antigravity CLI (~/.gemini/antigravity-cli/conversations/*.db)",
            "• Claude Code (~/.claude/projects/**/*.jsonl)",
            "• Cursor IDE (%APPDATA%/Cursor/.../state.vscdb)",
            "• Codex CLI (~/.codex/sessions/**/rollout-*.jsonl)",
            "• GitHub Copilot CLI (~/.copilot/session-store.db)",
            "• Koma (~/.koma/sessions/*, ~/.koma/ledger/*)",
            "• Aider (~/.aider.chat.history.md)",
            "• Windsurf / Cascade (%APPDATA%/Windsurf/.../state.vscdb)",
            "• Cline (VS Code) (%APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev)",
            "• Roo Code (%APPDATA%/Code/User/globalStorage/rooveterinaryinc.roo-cline)",
        ]
        ctk.CTkLabel(
            tools_card,
            text="\n".join(tools_list),
            font=ctk.CTkFont(size=10),
            text_color="gray70",
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 6))

        # Per-provider enable/disable switches
        self.provider_switches: dict[str, ctk.CTkSwitch] = {}
        provider_labels = {
            "antigravity": "Antigravity CLI",
            "claude": "Claude Code",
            "cursor": "Cursor IDE",
            "codex": "Codex CLI",
            "copilot": "GitHub Copilot",
            "koma": "Koma",
            "aider": "Aider",
            "windsurf": "Windsurf (Cascade)",
            "cline": "Cline (VS Code)",
            "roo": "Roo Code",
        }
        switches_frame = ctk.CTkFrame(tools_card, fg_color="transparent")
        switches_frame.pack(fill="x", padx=14, pady=(0, 4))
        for col in range(2):
            switches_frame.grid_columnconfigure(col, weight=1)
        for i, (key, label) in enumerate(provider_labels.items()):
            sw = ctk.CTkSwitch(
                switches_frame,
                text=label,
                command=lambda k=key: self.action_toggle_provider(k),
            )
            if self.store.tracked_providers.get(key, True):
                sw.select()
            sw.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 8), pady=2)
            self.provider_switches[key] = sw

        # Danger Zone
        reset_card = ctk.CTkFrame(frame, corner_radius=10)
        reset_card.pack(fill="x", padx=6, pady=(0, 6))

        ctk.CTkLabel(
            reset_card,
            text="⚠️ Danger Zone",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#EF5350",
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.btn_reset = ctk.CTkButton(
            reset_card,
            text="Reset Active Companion to Fresh Egg",
            fg_color="#C62828",
            hover_color="#8E0000",
            height=28,
            command=self.action_reset_active,
        )
        self.btn_reset.pack(anchor="w", padx=14, pady=(0, 10))

    def action_change_size(self, val_str: str):
        preset_map = {
            "Small (80px)": "small",
            "Medium (110px)": "medium",
            "Large (150px)": "large",
        }
        preset = preset_map.get(val_str, "medium")
        self.store.pet_size_preset = preset
        self.store.save()
        self.dashboard.show_toast(f"🐾 Pet size updated to {val_str}!")
        if self.dashboard.on_size_change:
            self.dashboard.on_size_change(preset)

    def action_change_opacity(self, val: float):
        op_int = int(val)
        self.lbl_opacity_val.configure(text=f"{op_int}%")
        self.store.pet_opacity = op_int
        self.store.save()
        if self.dashboard.on_opacity_change:
            self.dashboard.on_opacity_change(op_int)

    def action_snap_taskbar(self):
        if self.dashboard.on_taskbar_snap:
            self.dashboard.on_taskbar_snap()
        self.dashboard.show_toast("📌 Pet snapped above taskbar!")

    def action_toggle_roaming(self):
        val = bool(self.switch_roaming.get())
        self.store.roaming_enabled = val
        self.store.save()
        status_str = "enabled" if val else "disabled"
        self.dashboard.show_toast(f"🐾 Autonomous roaming {status_str}!")
        if self.dashboard.on_roaming_toggle:
            self.dashboard.on_roaming_toggle(val)

    def action_toggle_spawn_intro(self):
        val = bool(self.switch_spawn_intro.get())
        self.store.spawn_intro_enabled = val
        self.store.save()
        status_str = "enabled" if val else "disabled"
        self.dashboard.show_toast(f"🔴 Pokéball entrance animation {status_str}!")

    def action_toggle_sound(self):
        val = bool(self.switch_sound.get())
        self.store.sound_enabled = val
        self.store.save()
        status_str = "enabled" if val else "disabled"
        self.dashboard.show_toast(f"🔊 Audio sounds {status_str}!")

    def action_toggle_provider(self, key: str):
        sw = self.provider_switches[key]
        enabled = bool(sw.get())
        self.store.tracked_providers[key] = enabled
        self.store.save()
        if self.dashboard.on_update_callback:
            # Rebuild the scanner filter from saved toggles
            self.dashboard.on_update_callback()

    def action_test_sound(self):
        if not self.store.is_egg:
            play_cry(self.store.active.species_id, volume=0.7)
        else:
            play_cry(25, volume=0.7)
        play_sfx_levelup(volume=0.5)

    def action_reset_active(self):
        self.store.reset_to_fresh_egg()
        self.dashboard.show_toast("🥚 Reset active companion to fresh egg!", bg_color="#E67E22")
        self.dashboard.refresh_home_view()
        self.dashboard.refresh_pokedex_tab()
        self.dashboard.refresh_shop_tab()
        if self.dashboard.on_update_callback:
            self.dashboard.on_update_callback()

    def refresh_limit_status(self):
        lim = self.store.daily_token_limit
        if lim <= 0:
            self.lbl_limit_status.configure(text="ℹ️ Daily Limit: Disabled (No alerts)")
        else:
            w80 = int(lim * 0.8)
            self.lbl_limit_status.configure(
                text=f"ℹ️ Active Limit: {format_tokens(lim)} tokens (Warning alert at 80% = {format_tokens(w80)})"
            )

    def action_set_preset_limit(self, val: int):
        self.entry_limit.delete(0, "end")
        self.entry_limit.insert(0, str(val))
        self.store.set_daily_token_limit(val)
        self.refresh_limit_status()
        self.dashboard.refresh_home_view()
        self.dashboard.show_toast(f"🎯 Daily limit set to {format_tokens(val)} tokens!")
        if self.dashboard.on_update_callback:
            self.dashboard.on_update_callback()

    def action_save_limit(self):
        try:
            val_str = self.entry_limit.get().strip().replace(",", "").replace("_", "")
            val = int(val_str)
            self.store.set_daily_token_limit(val)
            self.refresh_limit_status()
            self.dashboard.refresh_home_view()
            self.dashboard.show_toast(f"🎯 Daily limit saved: {format_tokens(val)} tokens!")
            if self.dashboard.on_update_callback:
                self.dashboard.on_update_callback()
        except ValueError:
            self.lbl_limit_status.configure(
                text="❌ Invalid number! Please enter numbers only (e.g. 20000000)."
            )

    def action_test_notification(self):
        if self.dashboard.on_test_notification:
            self.dashboard.on_test_notification()

    def action_toggle_auto_evolve(self):
        self.store.auto_evolve_enabled = bool(self.switch_auto_evolve.get())
        self.store.save()
        state_str = (
            "Enabled (Automatic)"
            if self.store.auto_evolve_enabled
            else "Disabled (Manual Evolve Prompt)"
        )
        self.dashboard.show_toast(f"⚡ Evolution Mode: {state_str}")
        self.dashboard.refresh_home_view()
        if self.dashboard.on_update_callback:
            self.dashboard.on_update_callback()

    def action_toggle_autostart(self):
        enabled = bool(self.switch_autostart.get())
        success = self.store.set_autostart(enabled)
        if success:
            state_str = "Enabled (Starts on login)" if enabled else "Disabled (Manual start only)"
            self.dashboard.show_toast(f"🚀 Windows Startup: {state_str}")
        else:
            self.dashboard.show_toast(
                "⚠️ Failed to update Windows Registry for startup!",
                bg_color="#E74C3C",
                text_color="#FFF",
            )
