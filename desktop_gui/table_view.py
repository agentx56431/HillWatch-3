# desktop_gui/table_view.py
# Minimal table: two columns (Title, LatestActionDate) + load-more batching.

import tkinter as tk
from tkinter import ttk
from datetime import datetime

BATCH_SIZE = 200

def make_title(cg: dict) -> str:
    bt = cg.get("billType", "") or ""
    num = cg.get("billNumber", "") or ""
    title = cg.get("title", "") or ""
    return f"{bt}.{num} - {title}"

def parse_date(iso_str: str):
    if not iso_str:
        return None
    try:
        # Expect YYYY-MM-DD
        return datetime.strptime(iso_str, "%Y-%m-%d").date()
    except Exception:
        # Try full timestamp
        try:
            return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).date()
        except Exception:
            return None

class BillsTable(ttk.Frame):
    def __init__(self, parent, on_select_row, on_render_change=None):
        """
        on_select_row: callback(bill_id)
        on_render_change: callback(rendered_count:int, total_count:int)
        """
        super().__init__(parent)
        self.on_select_row = on_select_row
        self.on_render_change = on_render_change

        # Table (Treeview)
        self.tree = ttk.Treeview(self, columns=("title", "latest"), show="headings", height=20)
        self.tree.heading("title", text="Title")
        self.tree.heading("latest", text="LatestActionDate")
        self.tree.column("title", width=800, anchor="w")
        self.tree.column("latest", width=140, anchor="center")

        # Scrollbar
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Load more button
        self.load_more_btn = ttk.Button(self, text=f"Load more (+{BATCH_SIZE})", command=self.load_more)
        self.load_more_btn.grid(row=1, column=0, sticky="ew", pady=(6, 0), columnspan=2)

        # Layout weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Data state
        self.all_rows = []   # list of (bill_id, cg_dict)
        self.rendered = 0    # how many currently rendered

        # Bind select
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # change signature:
    def set_rows(self, items, sort_field="latest", sort_dir="desc"):
        """
        items: iterable of (bill_id, record_dict)
        sort_field: "latest" or "introduced"
        sort_dir: "asc" or "desc"
        """
        rows = []
        for bid, rec in items:
            cg = rec.get("congressGovData", {}) or {}
            rows.append((bid, cg))

        def _make_title(cg: dict) -> str:
            bt = cg.get("billType", "") or ""
            num = cg.get("billNumber", "") or ""
            title = cg.get("title", "") or ""
            return f"{bt}.{num} - {title}"

        def _parse_date(iso_str: str):
            from datetime import datetime
            if not iso_str:
                return None
            try:
                return datetime.strptime(iso_str, "%Y-%m-%d").date()
            except Exception:
                try:
                    return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).date()
                except Exception:
                    return None

        # Build a key that ALWAYS keeps title A→Z as the tiebreaker.
        # We flip just the DATE part depending on sort_dir.
        def sort_key(t):
            _, cg = t
            dstr = cg.get("latestActionDate") if sort_field == "latest" else cg.get("introducedDate")
            d = _parse_date(dstr)
            if d is None:
                date_ord = -10**9
            else:
                date_ord = d.toordinal()
            # Flip the date sign for DESC so we can keep title A→Z without using reverse=True
            if sort_dir == "desc":
                date_ord = -date_ord
            title_key = (_make_title(cg) or "").lower()
            return (date_ord, title_key)

        rows.sort(key=sort_key)

        # reset+render
        self.tree.delete(*self.tree.get_children())
        self.all_rows = rows
        self.rendered = 0
        self.load_more_btn.configure(state="normal")
        self.load_more()
        self._notify_render_change()


    def load_more(self):
        next_count = min(self.rendered + BATCH_SIZE, len(self.all_rows))
        for i in range(self.rendered, next_count):
            bill_id, cg = self.all_rows[i]
            title = make_title(cg)
            latest = cg.get("latestActionDate") or ""
            self.tree.insert("", "end", iid=bill_id, values=(title, latest))
        self.rendered = next_count

        if self.rendered >= len(self.all_rows):
            self.load_more_btn.configure(state="disabled")

        self._notify_render_change()

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        bill_id = sel[0]
        if callable(self.on_select_row):
            self.on_select_row(bill_id)

    def _notify_render_change(self):
        if callable(self.on_render_change):
            try:
                self.on_render_change(self.rendered, len(self.all_rows))
            except Exception:
                pass
