"""
Update Available Dialog for WinTokenMon.

Shows the new release version and changelog; downloads the Inno Setup
installer in a background thread, verifies its SHA256, launches it silently,
and asks the app to exit so setup can replace the binaries.
"""

import threading
from collections.abc import Callable

import customtkinter as ctk

from core.updater import download_and_verify_update, launch_installer


class UpdateAvailableModal:
    def __init__(self, parent, info: dict, current_version: str, on_install_started: Callable):
        self.info = info
        self.on_install_started = on_install_started
        self._downloading = False

        self.win = ctk.CTkToplevel(parent)
        self.win.title(f"🎉 Update {info['version']} Available")
        self.win.geometry("560x480")
        self.win.minsize(500, 420)
        self.win.lift()
        self.win.grab_set()

        ctk.CTkLabel(
            self.win,
            text=f"🎉 WinTokenMon {info['version']} is available!",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2ECC71",
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            self.win,
            text=f"You are running v{current_version}. Your save game is safe during updates.",
            font=ctk.CTkFont(size=11),
            text_color="gray70",
        ).pack(pady=(0, 10))

        self.txt_notes = ctk.CTkTextbox(self.win, wrap="word", font=ctk.CTkFont(size=12))
        self.txt_notes.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.txt_notes.insert("1.0", info.get("notes") or "No release notes provided.")
        self.txt_notes.configure(state="disabled")

        self.lbl_status = ctk.CTkLabel(
            self.win, text="", font=ctk.CTkFont(size=11), text_color="#F9E2AF", wraplength=520
        )
        self.lbl_status.pack(pady=(0, 6))

        buttons = ctk.CTkFrame(self.win, fg_color="transparent")
        buttons.pack(fill="x", padx=16, pady=(0, 16))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        self.btn_later = ctk.CTkButton(
            buttons, text="Remind Me Later", command=self.win.destroy, height=36
        )
        self.btn_later.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_install = ctk.CTkButton(
            buttons,
            text="⬇️ Download & Install Now",
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            command=self._start_download,
        )
        self.btn_install.grid(row=0, column=1, padx=(4, 0), sticky="ew")

    def _start_download(self):
        if self._downloading:
            return
        self._downloading = True
        self.btn_install.configure(state="disabled")
        self.lbl_status.configure(text="⬇️ Downloading installer…")

        def _work():
            path = download_and_verify_update(self.info)

            def _done():
                if path:
                    self.lbl_status.configure(text="✅ Verified! Launching setup…")
                    launch_installer(path)
                    self.on_install_started()
                else:
                    self.lbl_status.configure(
                        text="❌ Download or checksum verification failed. Try again later.",
                        text_color="#F38BA8",
                    )
                    self._downloading = False
                    self.btn_install.configure(state="normal")

            self.win.after(0, _done)

        threading.Thread(target=_work, daemon=True).start()
