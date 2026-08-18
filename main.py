"""
WinTokenMon for Windows — Main Entry Point
"""

import os
import sys
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

# Load developer environment variables from .env if present
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(ROOT_DIR, ".env"))
except ImportError:
    pass

DEBUG_MODE = os.environ.get("WINTOKENMON_DEBUG", "0").lower() in ("1", "true", "yes")
POLL_INTERVAL_MS = int(os.environ.get("WINTOKENMON_POLL_INTERVAL", "10")) * 1000

LOG_FILE = os.path.join(ROOT_DIR, "debug.log")


def log_error(err: str):
    if DEBUG_MODE:
        print(f"[DEBUG] {err}", file=sys.stderr)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {err}\n")
    except Exception:
        pass


def tk_safe(func):
    """Decorator to catch exceptions and log them safely without crashing the Tk mainloop."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            log_error(f"{func.__name__} Error: {traceback.format_exc()}")
    return wrapper


try:
    from core.companion_store import CompanionStore
    from core.token_reader import TokenUsageSummary, WindowsTokenReader
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
            self.reader = WindowsTokenReader()
            self.summary = TokenUsageSummary()
            self.dashboard_window = None
            self.starter_modal = None

            # Create Desktop Pet Window (Tkinter mainloop driver)
            self.pet = DesktopPetWindow(self.store, on_open_dashboard=self.open_dashboard)

            # Create System Tray
            self.tray = SystemTrayManager(
                store=self.store,
                on_open_dashboard=self.open_dashboard,
                on_toggle_pet=self.toggle_pet,
                on_refresh=self.poll_tokens_now,
                on_exit=self.exit_app,
                on_toggle_roaming=self.on_roaming_toggled,
            )
            self.tray.start()

            # Initial token read
            self.poll_tokens_now()

            # If starter not chosen yet on first launch, open starter selection wizard
            if not self.store.starter_chosen:
                self.pet.root.after(300, self.open_starter_selection)

            # Schedule recurring background poll (every 10s or custom interval)
            self.schedule_poll()
        except Exception:
            log_error(f"Init Error: {traceback.format_exc()}")
            raise

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

    def on_state_updated(self):
        self.pet.refresh_state(self.summary)
        self.tray.update_tooltip(self.summary)

    @tk_safe
    def poll_tokens_now(self):
        summary, delta = self.reader.get_summary()
        self.summary = summary
        if delta > 0:
            self.store.add_tokens(delta)

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
        self.pet.refresh_state(self.summary)
        self.tray.update_tooltip(self.summary)
        if self.dashboard_window and self.dashboard_window.win.winfo_exists():
            self.dashboard_window.update_summary(self.summary)

    def schedule_poll(self):
        self.poll_tokens_now()
        self.pet.root.after(POLL_INTERVAL_MS, self.schedule_poll)

    def exit_app(self):
        try:
            self.tray.stop()
            self.pet.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        try:
            self.pet.root.mainloop()
        except Exception:
            log_error(f"Mainloop Error: {traceback.format_exc()}")
            raise

    def __del__(self):
        try:
            if hasattr(self, "tray") and self.tray:
                self.tray.stop()
        except Exception:
            pass


if __name__ == "__main__":
    app = WinTokenMonApp()
    app.run()
