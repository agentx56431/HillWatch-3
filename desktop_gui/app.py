# desktop_gui/app.py
# HillWatch v3 – Bills table + search/filters + right pane (header/link/watchlist)

import tkinter as tk
from tkinter import ttk, messagebox

from desktop_gui.data_access import load_db, set_watchlist_and_save
from desktop_gui.table_view import BillsTable
from desktop_gui.filters import open_filters_dialog, filter_and_sort_items
from desktop_gui.detail_panel import DetailPanel

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
        ttk.Label(top, text=APP_TITLE, font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(top, text="Reload", command=self.on_reload_clicked).pack(side="right")

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

        # --- Bills Feed content: count + search row + table ---
        feed = self.tabs["Bills Feed"]

        self.count_var = tk.StringVar(value="Showing 0 of 0")
        ttk.Label(feed, textvariable=self.count_var).pack(anchor="w", padx=12, pady=(8, 0))

        sr = ttk.Frame(feed)
        sr.pack(fill="x", padx=12, pady=(6, 6))
        ttk.Label(sr, text="Search:").pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(sr, textvariable=self.search_var, width=50)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search_key)

        ttk.Button(sr, text="Clear", command=self.clear_search_and_filters).pack(side="left", padx=(8, 0))
        ttk.Button(sr, text="Filters…", command=self.on_filters_clicked).pack(side="left", padx=(8, 0))

        # Table (with render-count callback so the label updates after Load more)
        self.table = BillsTable(
            feed,
            on_select_row=self.on_select_row,
            on_render_change=self.on_table_render_change,
        )
        self.table.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        # --- Right pane detail panel ---
        self.detail = DetailPanel(self.right, on_toggle_watchlist=self.on_toggle_watchlist)
        self.detail.pack(fill="both", expand=True)

        # --- Data/search/filter state ---
        self.db = {}
        self.filtered_items = []
        self._search_after_id = None
        self.active_filters = None  # keep even if "empty" so sort options stick

        self.load_data()
        self.apply_search(initial=True)

    # ===== Data =====
    def load_data(self):
        try:
            self.db = load_db()
        except Exception as e:
            messagebox.showerror("Load error", str(e))
            self.db = {}

    # ===== Search / Filters =====
    def on_filters_clicked(self):
        result = open_filters_dialog(self, self.db, current_filters=self.active_filters)
        if result is None:
            return  # canceled
        # Keep result even if it's "empty" so sort_field/sort_dir are honored
        self.active_filters = result
        self.apply_search()

    def clear_search_and_filters(self):
        self.search_var.set("")
        # also reset filters to default "no filters, default sort"
        self.active_filters = {
            "committees": [],
            "sponsors": [],
            "bill_types": [],
            "origin_chambers": [],
            "date_mode": "none",
            "date_from": "",
            "date_to": "",
            "sort_field": "latest",
            "sort_dir": "desc",
        }
        self.apply_search()

    def on_search_key(self, _event=None):
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(SEARCH_DEBOUNCE_MS, self.apply_search)

    def apply_search(self, initial: bool=False):
        query = (self.search_var.get() or "").strip()
        items, sort_field, sort_dir = filter_and_sort_items(self.db, query, self.active_filters)
        self.filtered_items = items
        self.table.set_rows(self.filtered_items, sort_field=sort_field, sort_dir=sort_dir)

    # called by table after initial render and each "Load more"
    def on_table_render_change(self, rendered: int, total: int):
        self.count_var.set(f"Showing {rendered} of {total}")

    # ===== Events =====
    def on_reload_clicked(self):
        messagebox.showinfo("Reload", "Reload will be wired in a later phase.")

    def on_select_row(self, bill_id: str):
        rec = self.db.get(bill_id, {})
        self.detail.show_bill(bill_id, rec)

    def on_toggle_watchlist(self, bill_id: str, new_value: bool) -> bool:
        try:
            set_watchlist_and_save(self.db, bill_id, new_value)
            # Phase 9 will reflow tabs here
            return True
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return False

def main():
    app = HillWatchApp()
    app.mainloop()

if __name__ == "__main__":
    main()
