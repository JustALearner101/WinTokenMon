"""
WinTokenMon for Windows — Main Entry Point
"""

import os
import queue
import sys
import threading
import time
import traceback

# make sure working directory is project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)
sys.path.insert(0, ROOT_DIR)

# Set Windows DPI Awareness so coordinate systems match physical screen pixels
if sys.platform.startswith("win"):
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

DEBUG_MODE = os.environ.get("WINTOKENMON_DEBUG", "0").lower() in ("1", "true", "yes")
POLL_INTERVAL_MS = int(os.environ.get("WINTOKENMON_POLL_INTERVAL", "10")) * 1000


def log_error(err: str):
    if DEBUG_MODE:
        print(f"[DEBUG] {err}", file=sys.stderr)
    from core.applog import log_error as _file_log

    _file_log(err)


def tk_safe(func):
    """Decorator to catch exceptions and log them safely without crashing the Tk mainloop."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            log_error(f"{func.__name__} Error: {traceback.format_exc()}")

    return wrapper


try:
    from core import __version__
    from core.achievement_engine import AchievementEngine
    from core.audio_manager import play_sfx_achievement
    from core.companion_store import CompanionStore
    from core.token_reader import TokenUsageSummary, WindowsTokenReader
    from core.updater import start_background_check
    from ui.compact_hud import CompactHUDWindow
    from ui.dashboard import DashboardWindow
    from ui.desktop_pet import DesktopPetWindow
    from ui.starter_modal import StarterSelectionModal
    from ui.system_tray import SystemTrayManager
except Exception:
    log_error(f"Import Error: {traceback.format_exc()}")
    raise


class WinTokenMonApp:
    def __init__(self):
        try:
            self.store = CompanionStore()
            self.achievement_engine = AchievementEngine(self.store)
            self.store.on_achievement_callbacks.append(self.on_achievement_unlocked)

            self.reader = WindowsTokenReader()
            self.summary = TokenUsageSummary()
            self.dashboard_window = None
            self.starter_modal = None
            self.compact_hud = None

            # Velocity sampler: (timestamp, today_tokens) rolling window (worker-thread only)
            self.velocity_samples: list[tuple[float, int]] = []
            self._last_velocity: float = 0.0

            # Scanner worker thread plumbing: worker scans on disk/network,
            # results are handed to the UI thread via a small queue.
            self._scan_wake = threading.Event()
            self._scan_stop = threading.Event()
            self._exit_requested = False
            self._scan_results: queue.Queue[tuple] = queue.Queue(maxsize=2)
            self._ui_events: queue.Queue[tuple] = queue.Queue()

            # Apply saved provider toggles to the scanner engine
            self.reader.enabled_sources = {
                src for src, on in self.store.tracked_providers.items() if on
            }

            # Create Desktop Pet Window (Tkinter mainloop driver)
            self.pet = DesktopPetWindow(self.store, on_open_dashboard=self.open_dashboard)

            # Create Compact HUD capsule (hidden unless display_mode == compact_hud)
            self.compact_hud = CompactHUDWindow(self.store, on_switch_mode=self.toggle_display_mode)
            if self.store.display_mode != "compact_hud":
                self.compact_hud.hide()

            # Create System Tray
            self.tray = SystemTrayManager(
                store=self.store,
                on_open_dashboard=self.open_dashboard,
                on_toggle_pet=self.toggle_pet,
                on_refresh=self.request_scan,
                on_exit=self.exit_app,
                on_toggle_roaming=self.on_roaming_toggled,
                on_switch_mode=self.toggle_display_mode,
            )
            self.tray.start()

            # Start background scanner worker + UI result pump
            threading.Thread(target=self._scanner_loop, daemon=True).start()
            self.request_scan()
            self.pet.root.after(250, self._pump_scan_results)

            # Daily (cooldown-aware) auto-update check in the background
            start_background_check(self._on_update_available)

            # Surface Tk mainloop exceptions to the log file instead of stderr void
            self.pet.root.report_callback_exception = self._on_tk_exception

            # If starter not chosen yet on first launch, open starter selection wizard
            if not self.store.starter_chosen:
                self.pet.root.after(300, self.open_starter_selection)
        except Exception:
            log_error(f"Init Error: {traceback.format_exc()}")
            raise

    @staticmethod
    def _on_tk_exception(exc_type, exc_value, exc_tb):
        log_error("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))

    def open_starter_selection(self):
        @tk_safe
        def _open():
            self.starter_modal = StarterSelectionModal(
                self.store, on_selected_callback=self.on_starter_selected
            )

        self.pet.root.after(0, _open)

    def on_starter_selected(self):
        self.on_state_updated()

    def open_dashboard(self):
        @tk_safe
        def _open():
            if self.dashboard_window is None or not self.dashboard_window.win.winfo_exists():
                self.dashboard_window = DashboardWindow(
                    self.store,
                    self.summary,
                    on_update_callback=self.on_state_updated,
                    on_test_notification=self.trigger_test_notification,
                    on_size_change=self.on_pet_size_changed,
                    on_opacity_change=self.on_pet_opacity_changed,
                    on_taskbar_snap=self.on_taskbar_snap,
                    on_roaming_toggle=self.on_roaming_toggled,
                    achievement_engine=self.achievement_engine,
                )
            else:
                self.dashboard_window.win.lift()
                self.dashboard_window.refresh_home_view()

        self.pet.root.after(0, _open)

    def on_pet_size_changed(self, preset: str):
        self.pet.apply_size(preset)

    def on_pet_opacity_changed(self, opacity: int):
        self.pet.apply_opacity(opacity)

    def on_taskbar_snap(self):
        self.pet.snap_to_taskbar()

    def on_roaming_toggled(self, enabled: bool):
        self.pet.set_roaming_enabled(enabled)

    @tk_safe
    def on_achievement_unlocked(self, badge):
        """Triggers audio fanfare, tray notification, and in-app toast when a badge is unlocked."""
        if self.store.sound_enabled:
            play_sfx_achievement()

        reward_txt = (
            f" (+{badge.reward_tokens // 1_000_000}M Tokens)" if badge.reward_tokens else ""
        )
        if badge.reward_item:
            reward_txt = f" (+{badge.reward_item_count}x {badge.reward_item.title})"

        self.tray.send_notification(
            "🎖️ Achievement Unlocked!",
            f"{badge.icon_emoji} {badge.title}{reward_txt}\n{badge.description}",
        )

        if self.dashboard_window and self.dashboard_window.win.winfo_exists():
            self.dashboard_window.show_toast(
                f"🏆 Achievement Unlocked: {badge.title}!{reward_txt}",
                bg_color="#F1C40F",
                text_color="#181825",
            )
            self.dashboard_window.refresh_trophies_tab()

    @tk_safe
    def trigger_test_notification(self):
        self.tray.send_notification(
            "WinTokenMon Notification",
            f"Windows native notifications are working! Today: {self.summary.today_tokens:,} tokens.",
        )

    def toggle_pet(self):
        @tk_safe
        def _toggle():
            if self.pet.root.winfo_viewable():
                self.pet.root.withdraw()
                self.pet.hide_bubble()
            else:
                self.pet.root.deiconify()

        self.pet.root.after(0, _toggle)

    @tk_safe
    def toggle_display_mode(self):
        """Switches between Full Desktop Pet mode and Compact HUD pill mode."""
        if self.store.display_mode == "compact_hud":
            self.store.display_mode = "full_pet"
            self.compact_hud.hide()
            self.pet.root.deiconify()
            self.pet.refresh_state(self.summary)
        else:
            self.store.display_mode = "compact_hud"
            self.pet.root.withdraw()
            self.pet.hide_bubble()
            self.compact_hud.show()
            self.compact_hud.update_metrics(self.summary, self._last_velocity)
        self.tray.refresh_mode_label()
        self.store.save()

    # ─────────────────────────────────────────────────────────────────────
    # BACKGROUND SCANNER WORKER (disk/network I/O stays off the UI thread)
    # ─────────────────────────────────────────────────────────────────────
    def request_scan(self):
        """Wakes the scanner worker for an immediate poll. Safe from any thread."""
        self._scan_wake.set()

    def _scanner_loop(self):
        """Worker loop: scans all token sources, hands results to the UI queue."""
        while not self._scan_stop.is_set():
            self._scan_wake.wait(POLL_INTERVAL_MS / 1000.0)
            self._scan_wake.clear()
            if self._scan_stop.is_set():
                break
            try:
                summary, delta = self.reader.get_summary()
                velocity = self._compute_velocity(summary.today_tokens)
                try:
                    self._scan_results.put_nowait((summary, delta, velocity))
                except queue.Full:
                    pass  # UI lagging behind; drop stale scan
            except Exception:
                log_error(f"Scanner Error: {traceback.format_exc()}")

    def _pump_scan_results(self):
        """Drains scanner results on the UI thread and applies them to all views."""
        if self._exit_requested:
            self._perform_exit()
            return
        try:
            while True:
                summary, delta, velocity = self._scan_results.get_nowait()
                self._apply_scan_results(summary, delta, velocity)
        except queue.Empty:
            pass
        try:
            while True:
                kind, payload = self._ui_events.get_nowait()
                if kind == "update_available":
                    self._show_update_dialog(payload)
        except queue.Empty:
            pass
        self.pet.root.after(250, self._pump_scan_results)

    def _on_update_available(self, info: dict):
        """Updater worker callback: queue dialog display for the UI thread."""
        self._ui_events.put(("update_available", info))

    @tk_safe
    def _show_update_dialog(self, info: dict):
        try:
            from ui.modals.update_modal import UpdateAvailableModal

            UpdateAvailableModal(
                self.pet.root,
                info,
                __version__,
                on_install_started=self.exit_app,
            )
        except Exception as exc:
            log_error(f"update dialog failed: {exc}")

    @tk_safe
    def _apply_scan_results(self, summary, delta: int, velocity: float):
        self.summary = summary
        self._last_velocity = velocity

        if delta > 0:
            self.store.add_tokens(delta)

        # Evaluate real-time achievements (Night Owl, Overclock, Multi-Tool, 100M Burn)
        self.achievement_engine.on_token_poll(delta, self.summary)

        # Record in 7-day daily history (throttled inside store)
        self.store.record_daily_tokens(self.summary.today_tokens)

        # Notify pet of token activity level (burn mode / wake)
        self.pet.on_tokens_changed(delta)

        # Check threshold notification alerts (80% / 100%)
        notif = self.store.check_and_trigger_notifications(self.summary.today_tokens)
        if notif:
            title, msg = notif
            self.tray.send_notification(title, msg)

        # Update UI components
        if self.store.display_mode == "compact_hud":
            self.compact_hud.update_metrics(self.summary, velocity)
        else:
            self.pet.refresh_state(self.summary)
        self.tray.update_tooltip(self.summary)
        if self.dashboard_window and self.dashboard_window.win.winfo_exists():
            self.dashboard_window.update_summary(self.summary)

    def _compute_velocity(self, today_tokens: int) -> float:
        """Computes tokens/min burn velocity from a rolling 5-minute sample window.
        Only called from the scanner worker thread."""
        now = time.time()
        self.velocity_samples.append((now, today_tokens))
        # Keep only the last 5 minutes of samples
        cutoff = now - 300
        self.velocity_samples = [(ts, tok) for ts, tok in self.velocity_samples if ts >= cutoff]
        if len(self.velocity_samples) < 2:
            return 0.0
        oldest_ts, oldest_tok = self.velocity_samples[0]
        elapsed_min = (now - oldest_ts) / 60.0
        if elapsed_min <= 0:
            return 0.0
        return max(0, today_tokens - oldest_tok) / elapsed_min

    def on_state_updated(self):
        # Re-sync scanner filters in case provider toggles changed
        self.reader.enabled_sources = {
            src for src, on in self.store.tracked_providers.items() if on
        }
        if self.store.display_mode != "compact_hud":
            self.pet.refresh_state(self.summary)
        else:
            self.compact_hud.update_metrics(self.summary, self._last_velocity)
        self.tray.update_tooltip(self.summary)

    def exit_app(self):
        """Requests shutdown. Safe to call from the tray (non-main) thread:
        only sets flags and stops pystray; the UI pump performs the teardown."""
        if self._exit_requested:
            return
        self._exit_requested = True
        self._scan_stop.set()
        try:
            if self.tray:
                self.tray.stop()
        except Exception as exc:
            log_error(f"tray.stop failed: {exc}")

    def _perform_exit(self):
        """Final teardown — always runs on the Tk main thread via the result pump."""
        try:
            if self.compact_hud:
                self.compact_hud.destroy()
            self.pet.destroy()
            self.pet.root.quit()  # ends mainloop; run() returns normally
        except Exception:
            log_error(f"Exit Error: {traceback.format_exc()}")

    def run(self):
        sys.excepthook = lambda t, v, tb: log_error(
            "".join(traceback.format_exception(t, v, tb))
        )
        try:
            self.pet.root.mainloop()
        except Exception:
            log_error(f"Mainloop Error: {traceback.format_exc()}")
            raise


if __name__ == "__main__":
    app = WinTokenMonApp()
    app.run()
