# desktop_gui/detail_panel.py
# Right-side panel: header, browser link, WatchList star (autosave)

import tkinter as tk
from tkinter import ttk
import webbrowser

class DetailPanel(ttk.Frame):
    def __init__(self, parent, on_toggle_watchlist):
        """
        on_toggle_watchlist(bill_id: str, new_value: bool) -> bool
          Should return True on success (so we show 'Saved'), False on failure.
        """
        super().__init__(parent, padding=(12, 12))
        self.on_toggle_watchlist = on_toggle_watchlist
        self.bill_id = None
        self._saved_after_id = None
        self._congress_url = None

        # Header
        self.header_var = tk.StringVar(value="Select a row to view details")
        ttk.Label(self, textvariable=self.header_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

        # Link button
        row = ttk.Frame(self); row.pack(anchor="w", pady=(8, 6))
        self.view_btn = ttk.Button(row, text="View Legislation in Browser", command=self._open_in_browser, state="disabled")
        self.view_btn.pack(side="left")

        # WatchList toggle (star)
        self.watch_var = tk.BooleanVar(value=False)
        self.watch_btn = ttk.Checkbutton(self, text="⭐ WatchList", variable=self.watch_var,
                                         command=self._toggle_watchlist, state="disabled")
        self.watch_btn.pack(anchor="w", pady=(6, 6))

        # Saved toast
        self.saved_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.saved_var, foreground="#2e7d32").pack(anchor="w")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(10, 0))
        ttk.Label(self, text="(Congress.gov Data + Custom editor will appear in later phases.)",
                  foreground="#555").pack(anchor="w", pady=(10, 0))

    def _open_in_browser(self):
        if self._congress_url:
            webbrowser.open(self._congress_url)

    def _toggle_watchlist(self):
        if not self.bill_id:
            return
        new_val = bool(self.watch_var.get())
        ok = False
        try:
            ok = bool(self.on_toggle_watchlist(self.bill_id, new_val))
        except Exception:
            ok = False
        if ok:
            self._show_saved("Saved")
        else:
            self.watch_var.set(not new_val)  # revert on failure

    def _show_saved(self, msg: str):
        self.saved_var.set(msg)
        if self._saved_after_id:
            self.after_cancel(self._saved_after_id)
        self._saved_after_id = self.after(1200, lambda: self.saved_var.set(""))

    def show_bill(self, bill_id: str, record: dict):
        """Render selected bill."""
        self.bill_id = bill_id
        cg = (record or {}).get("congressGovData", {}) or {}
        bt, num, title = cg.get("billType", ""), cg.get("billNumber", ""), cg.get("title", "")
        self.header_var.set(f"{bt} {num} — {title}")
        self._congress_url = cg.get("congressGovUrl") or None
        self.view_btn.configure(state="normal" if self._congress_url else "disabled")

        cd = (record or {}).get("customData", {}) or {}
        review = cd.get("Review", {}) or {}
        self.watch_var.set(bool(review.get("WatchList", False)))
        self.watch_btn.configure(state="normal")
