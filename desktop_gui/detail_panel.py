# desktop_gui/detail_panel.py
# Right-side panel: header, browser link, WatchList star (autosave) + Congress.gov Data (read-only)

import tkinter as tk
from tkinter import ttk
import webbrowser

from desktop_gui.collapsible import Collapsible

READONLY_KEYS_ORDER = [
    "billId",
    "congress",
    "billType",
    "billNumber",
    "title",
    "originChamber",
    "introducedDate",
    "sponsorFullName",
    "sponsorParty",
    "sponsorState",
    "sponsorDistrict",
    "currentCommitteeName",
    "currentSubcommitteeName",
    "latestActionText",
    "latestActionDate",
    "updateDate",
    "updateDateIncludingText",
    "sourceUrl",
    "congressGovUrl",
    "contentHash",
    "committeeLastActionSeen",
]

class DetailPanel(ttk.Frame):
    def __init__(self, parent, on_toggle_watchlist):
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

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(10, 6))

        # ===== Congress.gov Data (collapsible) =====
        self.cg_section = Collapsible(self, "Congress.gov Data", start_open=True)
        self.cg_section.pack(fill="both", expand=True, pady=(6, 0))

        # Scrollable area inside cg_section.body
        sc = ttk.Frame(self.cg_section.body)
        sc.pack(fill="both", expand=True)

        self.cg_canvas = tk.Canvas(sc, highlightthickness=0)
        self.cg_scroll = ttk.Scrollbar(sc, orient="vertical", command=self.cg_canvas.yview)
        self.cg_canvas.configure(yscrollcommand=self.cg_scroll.set)

        self.cg_inner = ttk.Frame(self.cg_canvas)
        self.cg_canvas.create_window((0, 0), window=self.cg_inner, anchor="nw")

        self.cg_canvas.pack(side="left", fill="both", expand=True)
        self.cg_scroll.pack(side="right", fill="y")

        # Update scrollregion when content changes
        self.cg_inner.bind("<Configure>", lambda e: self.cg_canvas.configure(scrollregion=self.cg_canvas.bbox("all")))
        # Mouse wheel support (Windows)
        self.cg_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Placeholder for future phases (Custom editor)
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(10, 6))
        ttk.Label(self, text="(Custom editor will appear in the next phases.)", foreground="#555").pack(anchor="w", pady=(6, 0))

    # ---------- Events ----------
    def _on_mousewheel(self, event):
        # Only scroll if mouse is over the canvas to avoid hijacking global wheel
        if self.cg_canvas.winfo_containing(event.x_root, event.y_root) == self.cg_canvas:
            self.cg_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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

    # ---------- Render ----------
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

        # Rebuild the Congress.gov Data list
        for w in self.cg_inner.winfo_children():
            w.destroy()

        # Render keys in preferred order, but include any extras that might appear
        keys_seen = set()
        row = 0

        def add_row(label: str, value: str):
            nonlocal row
            # label
            ttk.Label(self.cg_inner, text=label + ":", width=26).grid(row=row, column=0, sticky="w", padx=(4, 8), pady=2)
            # value (wrapped/ellipsized via limited width)
            lbl = ttk.Label(self.cg_inner, text=value, width=80)
            lbl.grid(row=row, column=1, sticky="w", padx=(0, 4), pady=2)
            row += 1

        # First the common keys
        for k in READONLY_KEYS_ORDER:
            if k in cg:
                v = cg.get(k, "")
                add_row(k, "" if v is None else str(v))
                keys_seen.add(k)

        # Then any extra fields present in the JSON
        for k, v in cg.items():
            if k in keys_seen:
                continue
            add_row(k, "" if v is None else str(v))

        # Ensure the inner frame width tracks the visible canvas width
        self.after(50, lambda: self.cg_canvas.configure(scrollregion=self.cg_canvas.bbox("all")))
