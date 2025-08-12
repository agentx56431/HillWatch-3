# desktop_gui/table_view.py
# Minimal table widget for HillWatch v3
# - Two columns: Title and Latest Action Date
# - set_rows(items) where items = [(bill_id, record), ...]
# - Calls on_select(bill_id) when a row is clicked

import tkinter as tk
from tkinter import ttk

class TableView(ttk.Frame):
    def __init__(self, parent, on_select=None):
        super().__init__(parent)
        self.on_select = on_select
        self._items = []  # backing list [(bill_id, record)]

        # Treeview with two columns
        columns = ("title", "latestActionDate")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("title", text="Title")
        self.tree.heading("latestActionDate", text="Latest Action Date")

        # Column widths / stretch
        self.tree.column("title", width=680, anchor="w", stretch=True)
        self.tree.column("latestActionDate", width=140, anchor="center", stretch=False)

        # Attach scrollbar
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Style tweak so text truncates nicely (OS default handles ellipsis visually)
        style = ttk.Style(self)
        # You can adjust fonts if you want, e.g.:
        # style.configure("Treeview", font=("Segoe UI", 9))

    def set_rows(self, items):
        """items: list of (bill_id, record) tuples."""
        self._items = items or []
        # Clear existing
        for iid in self.tree.get_children(""):
            self.tree.delete(iid)

        # Insert rows
        for bill_id, rec in self._items:
            cg = (rec or {}).get("congressGovData", {}) or {}
            title_text = f"{cg.get('billType','')}.{cg.get('billNumber','')} - {cg.get('title','')}"
            lad = cg.get("latestActionDate") or ""
            # Keep iid = bill_id so we can map selection back
            self.tree.insert("", "end", iid=bill_id, values=(title_text, lad))

        # Auto-select first row (optional)
        if self._items:
            first_id = self._items[0][0]
            # only auto-select if nothing selected
            if not self.tree.selection():
                try:
                    self.tree.selection_set(first_id)
                    self.tree.see(first_id)
                    self._notify_select(first_id)
                except Exception:
                    pass

    def _on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        bill_id = sel[0]
        self._notify_select(bill_id)

    def _notify_select(self, bill_id: str):
        if callable(self.on_select):
            try:
                self.on_select(bill_id)
            except Exception:
                # swallow to avoid breaking UI on callback issues
                pass
