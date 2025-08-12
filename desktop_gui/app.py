# desktop_gui/app.py
# HillWatch v3 desktop GUI: tabs + tables on the left, detail pane on the right.
# Dynamic routing across WatchList / Rejected / Complete. Search, filters, load-more.

import tkinter as tk
from tkinter import ttk, messagebox

from desktop_gui.table_view import TableView
from desktop_gui.detail_panel import DetailPanel
from desktop_gui.filter_dialog import FilterDialog

from desktop_gui.data_access import (
    load_db,
    set_watchlist_and_save,
    set_custom_field_and_save,
)

APP_TITLE = "HillWatch v3"
START_LIMIT = 200
LOAD_STEP = 200


# ---------- Routing predicates ----------
def classify_watch_tab(rec):
    """
    Returns: "complete" | "reject" | "watch" | None
    Only bills with Review.WatchList == True get classified; others return None.
    Rules (mutually exclusive):
      - Complete: CEIExpertAcceptOrReject == True AND Final_Tracking_Done == True
      - Rejected: CEIExpertAcceptOrReject == False AND Review_Done == True
      - Watch:    all other watchlisted bills
    """
    cd = (rec or {}).get("customData", {}) or {}
    r  = cd.get("Review", {}) or {}
    f  = cd.get("FinalTracking", {}) or {}

    if not bool(r.get("WatchList")):
        return None

    cei_accept = r.get("CEIExpertAcceptOrReject")
    review_done = bool(r.get("Review_Done"))
    final_done = bool(f.get("Final_Tracking_Done"))

    # Complete
    if cei_accept is True and final_done is True:
        return "complete"

    # Rejected (must be explicitly False AND review finished)
    if cei_accept is False and review_done is True:
        return "reject"

    # Otherwise still in WatchList
    return "watch"


# ---------- App ----------
class HillWatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x720")

        # Data
        self.db = load_db()  # dict: bill_id -> record

        # UI state
        self.current_tab = "feed"      # "feed" | "watch" | "reject" | "complete"
        self.current_limit = START_LIMIT
        self.filters = {
            "text": "",
            "committees": set(),
            "sponsors": set(),
            "types": set(),            # HR,S,HJRES,SJRES,HCONRES,SCONRES
            "chambers": set(),         # House, Senate
            "date_field": "latestActionDate",  # or "introducedDate"
            "date_from": None,         # YYYY-MM-DD or None
            "date_to": None,           # YYYY-MM-DD or None
            "sort_field": "latestActionDate",  # or "introducedDate"
            "sort_dir": "desc",        # "desc" | "asc"
        }

        # Main layout: left/right
        self.pw = ttk.Panedwindow(self, orient="horizontal")
        self.left = ttk.Frame(self.pw)
        self.right = ttk.Frame(self.pw)
        self.pw.add(self.left, weight=3)
        self.pw.add(self.right, weight=5)
        self.pw.pack(fill="both", expand=True)

        # Left top toolbar (count + search + buttons)
        self._build_left_toolbar()

        # Tabs area
        self._build_tabs_and_tables()

        # Right detail panel
        self.detail = DetailPanel(
            self.right,
            on_toggle_watchlist=self.on_toggle_watchlist,
            on_set_custom_field=self.on_set_custom_field,
        )
        self.detail.pack(fill="both", expand=True)

        # Initial data fill
        self.recompute_views()

    # ---------- Left: toolbar ----------
    def _build_left_toolbar(self):
        top = ttk.Frame(self.left)
        top.pack(fill="x", padx=8, pady=(8, 4))

        self.count_var = tk.StringVar(value="Showing 0 of 0")
        ttk.Label(top, textvariable=self.count_var).pack(side="left")

        # spacer
        ttk.Label(top, text="  ").pack(side="left")

        # Search box
        ttk.Label(top, text="Search:").pack(side="left", padx=(8, 4))
        self.search_var = tk.StringVar(value="")
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, width=36)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # spacer
        ttk.Label(top, text="  ").pack(side="left")

        # Filter dialog
        ttk.Button(top, text="Filters…", command=self.open_filters).pack(side="left", padx=(0, 8))

        # Load more
        ttk.Button(top, text="+200", command=self.on_load_more).pack(side="left")

        # Reload updater (placeholder: we just pop a message; wire to your CLI if desired)
        ttk.Button(top, text="Reload DB", command=self.on_reload_db).pack(side="right")

    # ---------- Left: tabs + tables ----------
    def _build_tabs_and_tables(self):
        self.nb = ttk.Notebook(self.left)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.tabs = {}
        self.tables = {}

        for key, title in [
            ("feed", "Bills Feed"),
            ("watch", "WatchList"),
            ("reject", "Rejected"),
            ("complete", "Complete"),
        ]:
            frame = ttk.Frame(self.nb)
            self.nb.add(frame, text=title)
            self.tabs[key] = frame

            table = TableView(frame, on_select=self.on_select_row)
            table.pack(fill="both", expand=True)
            self.tables[key] = table

        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ---------- Events ----------
    def _on_tab_changed(self, _evt):
        idx = self.nb.index(self.nb.select())
        self.current_tab = ["feed", "watch", "reject", "complete"][idx]
        # reset limit when switching tabs (optional; comment if you prefer to keep)
        self.current_limit = START_LIMIT
        self.recompute_views()

    def _on_search_changed(self, _evt):
        self.filters["text"] = self.search_var.get().strip()
        # when searching, reset limit to show the newest 200 matches
        self.current_limit = START_LIMIT
        self.recompute_views()

    def on_load_more(self):
        self.current_limit += LOAD_STEP
        self.recompute_views()

    def on_reload_db(self):
        try:
            self.db = load_db()
            self.current_limit = START_LIMIT
            self.recompute_views()
            messagebox.showinfo("Reloaded", "Reloaded local JSON database.")
        except Exception as e:
            messagebox.showerror("Reload failed", str(e))

    def open_filters(self):
        try:
            dlg = FilterDialog(self, initial_filters=self.filters, db=self.db)
            result = dlg.show()  # expected to return dict or None
            if result:
                self.filters.update(result)
                self.current_limit = START_LIMIT
                self.recompute_views()
        except Exception as e:
            messagebox.showerror("Filters", f"Could not open filters dialog:\n{e}")

    # row selected in any table
    def on_select_row(self, bill_id: str):
        rec = self.db.get(bill_id)
        if not rec:
            return
        self.detail.show_bill(bill_id, rec)

    # star toggled from detail pane
    def on_toggle_watchlist(self, bill_id: str, new_value: bool) -> bool:
        try:
            set_watchlist_and_save(self.db, bill_id, new_value)
            self.recompute_views()
            return True
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return False

    # any custom field edited in detail pane
    def on_set_custom_field(self, bill_id: str, group: str, key: str, value) -> bool:
        try:
            set_custom_field_and_save(self.db, bill_id, group, key, value)
            self.recompute_views()
            return True
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return False

    # ---------- Core: recompute per-tab data ----------
    def recompute_views(self):
        """Rebuild lists for each tab from full DB using current search/filters/sort, then show the active tab."""
        all_items = list(self.db.items())  # [(bill_id, record)]

        # Bills Feed = everyone (apply search/filters/sort)
        feed_all = self._apply_search_and_filters(all_items)

        # Classify each watchlisted bill into exactly one tab
        watch_bucket, reject_bucket, complete_bucket = [], [], []
        for bid, rec in all_items:
            cls = classify_watch_tab(rec)
            if cls == "watch":
                watch_bucket.append((bid, rec))
            elif cls == "reject":
                reject_bucket.append((bid, rec))
            elif cls == "complete":
                complete_bucket.append((bid, rec))

        # Apply search/filters/sort to each bucket as well (so tabs respect the UI filters)
        watch_all    = self._apply_search_and_filters(watch_bucket)
        reject_all   = self._apply_search_and_filters(reject_bucket)
        complete_all = self._apply_search_and_filters(complete_bucket)

        # Save for load-more
        self.feed_items_all     = feed_all
        self.watch_items_all    = watch_all
        self.reject_items_all   = reject_all
        self.complete_items_all = complete_all

        # Limit slice
        def limited(lst): return lst[: self.current_limit]

        # Update active table + count label
        if self.current_tab == "feed":
            rows = limited(self.feed_items_all)
            self.tables["feed"].set_rows(rows)
            self._update_count_label(len(rows), len(self.feed_items_all))
        elif self.current_tab == "watch":
            rows = limited(self.watch_items_all)
            self.tables["watch"].set_rows(rows)
            self._update_count_label(len(rows), len(self.watch_items_all))
        elif self.current_tab == "reject":
            rows = limited(self.reject_items_all)
            self.tables["reject"].set_rows(rows)
            self._update_count_label(len(rows), len(self.reject_items_all))
        elif self.current_tab == "complete":
            rows = limited(self.complete_items_all)
            self.tables["complete"].set_rows(rows)
            self._update_count_label(len(rows), len(self.complete_items_all))

    # ---------- Helpers: search / filters / sort ----------
    def _apply_search_and_filters(self, items):
        """
        items: list[(bill_id, record)]
        returns: filtered/sorted list[(bill_id, record)]
        Applies keyword search, structured filters, and sort. Does NOT apply the limit.
        """
        f = self.filters
        text = (f.get("text") or "").lower().strip()
        committees = set(f.get("committees") or [])
        sponsors = set(f.get("sponsors") or [])
        types = set(f.get("types") or [])
        chambers = set(f.get("chambers") or [])
        date_field = f.get("date_field") or "latestActionDate"
        date_from = f.get("date_from") or None
        date_to = f.get("date_to") or None
        sort_field = f.get("sort_field") or "latestActionDate"
        sort_dir = f.get("sort_dir") or "desc"

        # --- keyword match function (search across many cong.gov fields)
        def match_text(rec):
            if not text:
                return True
            cg = rec.get("congressGovData", {}) or {}
            hay = " ".join([
                str(cg.get("billType", "")),
                str(cg.get("billNumber", "")),
                str(cg.get("title", "")),
                str(cg.get("sponsorFullName", "")),
                str(cg.get("currentCommitteeName", "")),
                str(cg.get("currentSubcommitteeName", "")),
                str(cg.get("latestActionText", "")),
            ]).lower()
            return text in hay

        # --- structured filters
        def match_filters(rec):
            cg = rec.get("congressGovData", {}) or {}
            if committees and (cg.get("currentCommitteeName") or "") not in committees:
                return False
            if sponsors and (cg.get("sponsorFullName") or "") not in sponsors:
                return False
            if types and (cg.get("billType") or "") not in types:
                return False
            if chambers and (cg.get("originChamber") or "") not in chambers:
                return False
            # date range (on selected field)
            val = (cg.get(date_field) or "").strip()  # YYYY-MM-DD or ''
            if date_from and (not val or val < date_from):
                return False
            if date_to and (not val or val > date_to):
                return False
            return True

        # filter pipeline
        filtered = [(bid, rec) for (bid, rec) in items if match_text(rec) and match_filters(rec)]

        # sort
        def sort_key(pair):
            rec = pair[1]
            cg = rec.get("congressGovData", {}) or {}
            # normalize date fields to string YYYY-MM-DD; missing -> ''
            a = (cg.get(sort_field) or "")
            b = (cg.get("title") or "")
            return (a, b)

        reverse = (sort_dir == "desc")
        filtered.sort(key=sort_key, reverse=reverse)

        return filtered

    def _update_count_label(self, shown, total):
        self.count_var.set(f"Showing {shown} of {total}")


def main():
    app = HillWatchApp()
    app.mainloop()


if __name__ == "__main__":
    main()
