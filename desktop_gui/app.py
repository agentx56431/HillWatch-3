# desktop_gui/app.py
# HillWatch v3 – App skeleton + Bills Feed table + Search (full-DB, debounced)

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from desktop_gui.data_access import load_db
from desktop_gui.table_view import BillsTable
from desktop_gui import filters as hw_filters

APP_TITLE = "HillWatch v3"
SEARCH_DEBOUNCE_MS = 300

class HillWatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x760")
        self.minsize(1000, 620)

        # --- Top bar ---
        top = ttk.Frame(self, padding=(12, 8))
        top.pack(side="top", fill="x")
        self.title_lbl = ttk.Label(top, text=APP_TITLE, font=("Segoe UI", 11, "bold"))
        self.title_lbl.pack(side="left")
        self.reload_btn = ttk.Button(top, text="Reload", command=self.on_reload_clicked)
        self.reload_btn.pack(side="right")

        # --- Split panes ---
        self.paned = ttk.Panedwindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True)
        self.left = ttk.Frame(self.paned)
        self.right = ttk.Frame(self.paned)
        self.paned.add(self.left, weight=1)
        self.paned.add(self.right, weight=1)

        # --- Tabs ---
        self.nb = ttk.Notebook(self.left)
        self.nb.pack(fill="both", expand=True, padx=12, pady=12)
        self.tabs = {}
        for name in ("Bills Feed", "WatchList", "Rejected", "Complete"):
            frame = ttk.Frame(self.nb)
            self.nb.add(frame, text=name)
            self.tabs[name] = frame

        # --- Bills Feed content: count + search bar + table ---
        feed = self.tabs["Bills Feed"]

        # Row count (above search)
        self.count_var = tk.StringVar(value="Showing 0 of 0")
        count_lbl = ttk.Label(feed, textvariable=self.count_var)
        count_lbl.pack(anchor="w", padx=12, pady=(8, 0))

        # Search bar row
        search_row = ttk.Frame(feed)
        search_row.pack(fill="x", padx=12, pady=(6, 6))

        ttk.Label(search_row, text="Search:").pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=50)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search_key)

        self.clear_btn = ttk.Button(search_row, text="Clear", command=self.clear_search_and_filters)
        self.clear_btn.pack(side="left", padx=(8, 0))

        # Placeholder for Filters button (Phase 4 will wire the dialog)
        self.filters_btn = ttk.Button(search_row, text="Filters…", command=self.on_filters_clicked)
        self.filters_btn.pack(side="left", padx=(8, 0))

        # Table
        self.table = BillsTable(feed, on_select_row=self.on_select_row)
        self.table.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        # --- Right pane placeholder ---
        right_wrap = ttk.Frame(self.right, padding=(12, 12))
        right_wrap.pack(fill="both", expand=True)
        self.right_msg = ttk.Label(
            right_wrap,
            text="Select a row to view details here.\n(Details/editor will appear in later phases.)",
            foreground="#555"
        )
        self.right_msg.pack(anchor="nw")

        # Data & search state
        self.db = {}
        self.filtered_items = []   # list[(bill_id, record)]
        self._search_after_id = None
        self.active_filters = None  # will hold dict from dialog


        self.load_data()
        self.apply_search(initial=True)

    # ---- Data ----
    def load_data(self):
        try:
            self.db = load_db()
        except Exception as e:
            messagebox.showerror("Load error", str(e))
            self.db = {}

    # ---- Search / Filters ----
    def on_filters_clicked(self):
        # Open UI dialog (Phase 4) — returns dict or None
        result = hw_filters.open_filters_dialog(self, self.db, current_filters=self.active_filters)
        if result is None:
            return  # user canceled
        if result and not any(result.values()):
            # All empty? treat as cleared
            self.active_filters = None
            messagebox.showinfo("Filters", "Filters cleared (logic applies in next phase).")
        else:
            self.active_filters = result
            messagebox.showinfo("Filters", "Filters saved (logic applies in next phase).")
        # NOTE: Actual filtering will be implemented in Phase 5.

    def on_search_key(self, _event=None):
        # Debounce search to avoid lag while typing
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(SEARCH_DEBOUNCE_MS, self.apply_search)

    def apply_search(self, initial: bool=False):
        query = (self.search_var.get() or "").strip()
        self.filtered_items = hw_filters.search_items(self.db, query)
        # Set rows -> table will sort and render first batch
        self.table.set_rows(self.filtered_items)
        # Update count after table renders a batch
        self.after(50, self.update_count)

    def clear_search_and_filters(self):
        self.search_var.set("")
        self.active_filters = None
        self.apply_search()

    def update_count(self):
        total = len(self.filtered_items)
        shown = self.table.rendered
        self.count_var.set(f"Showing {shown} of {total}")

    # ---- Events ----
    def on_reload_clicked(self):
        messagebox.showinfo("Reload", "Reload will be wired in a later phase.")

    def on_select_row(self, bill_id: str):
        self.right_msg.configure(
            text=f"Selected: {bill_id}\n(Details/editor coming in later phases.)"
        )

def main():
    app = HillWatchApp()
    app.mainloop()

if __name__ == "__main__":
    main()
