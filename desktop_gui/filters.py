# desktop_gui/filters.py
# Search/filter helpers for HillWatch v3

from typing import Dict, Tuple, List

def _cg_text(rec: dict) -> str:
    """
    Build a searchable text blob from congressGovData fields.
    Only congressGovData is searched (not customData).
    """
    cg = rec.get("congressGovData", {}) or {}
    parts = [
        str(cg.get("billType", "")),
        str(cg.get("billNumber", "")),
        str(cg.get("title", "")),
        str(cg.get("originChamber", "")),
        str(cg.get("latestActionText", "")),
        str(cg.get("sponsorFullName", "")),
        str(cg.get("sponsorParty", "")),
        str(cg.get("sponsorState", "")),
        str(cg.get("currentCommitteeName", "")),
        str(cg.get("currentSubcommitteeName", "")),
        str(cg.get("introducedDate", "")),
        str(cg.get("latestActionDate", "")),
    ]
    # Lowercase + single string for fast substring checks
    return " ".join(parts).lower()

def _matches(query: str, blob: str) -> bool:
    """
    AND match on tokens: every token in the query must be present in the blob.
    """
    q = (query or "").strip().lower()
    if not q:
        return True
    tokens = [t for t in q.split() if t]
    return all(t in blob for t in tokens)

def search_items(db: Dict[str, dict], query: str) -> List[Tuple[str, dict]]:
    """
    Return a list of (bill_id, record) that match the query across congressGovData.
    """
    if not query or not query.strip():
        return list(db.items())
    out = []
    for bid, rec in db.items():
        blob = _cg_text(rec)
        if _matches(query, blob):
            out.append((bid, rec))
    return out

# -------- FILTERS DIALOG (UI only for Phase 4) --------
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Tuple

FIXED_BILL_TYPES = ["HR", "S", "HJRES", "SJRES", "HCONRES", "SCONRES"]
FIXED_ORIGIN_CHAMBERS = ["House", "Senate"]

def build_unique_committees(db: Dict[str, dict]) -> List[str]:
    s = set()
    for _, rec in db.items():
        cg = rec.get("congressGovData", {}) or {}
        name = (cg.get("currentCommitteeName") or "").strip()
        if name:
            s.add(name)
    return sorted(s)

def build_unique_sponsors(db: Dict[str, dict]) -> List[str]:
    s = set()
    for _, rec in db.items():
        cg = rec.get("congressGovData", {}) or {}
        name = (cg.get("sponsorFullName") or "").strip()
        if name:
            s.add(name)
    return sorted(s)

class FiltersDialog(tk.Toplevel):
    """
    UI-only dialog that gathers filter selections.
    Returns selections in a dict on Apply, or None on Cancel.
    """
    def __init__(self, parent, db: Dict[str, dict], current_filters: Optional[dict] = None):
        super().__init__(parent)
        self.title("Filters")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.db = db
        self.result = None

        # Defaults from current filters (or empty)
        cf = current_filters or {}
        selected_committees = set(cf.get("committees") or [])
        selected_sponsors = set(cf.get("sponsors") or [])
        selected_bill_types = set(cf.get("bill_types") or [])
        selected_chambers = set(cf.get("origin_chambers") or [])
        date_mode = cf.get("date_mode") or "none"   # "introduced" | "latest" | "none"
        date_from = cf.get("date_from") or ""
        date_to = cf.get("date_to") or ""
        sort_field = cf.get("sort_field") or "latest"  # "latest" | "introduced"
        sort_dir = cf.get("sort_dir") or "desc"        # "asc" | "desc"

        pad = {"padx": 12, "pady": 6}

        # --- Committees ---
        frame_comm = ttk.Labelframe(self, text="Committees (multi-select)")
        frame_comm.grid(row=0, column=0, sticky="ew", **pad)
        committees = build_unique_committees(self.db)
        self.comm_list = tk.Listbox(frame_comm, selectmode="extended", width=50, height=min(8, max(3, len(committees))))
        for i, c in enumerate(committees):
            self.comm_list.insert("end", c)
            if c in selected_committees:
                self.comm_list.selection_set(i)
        self.comm_list.pack(fill="both", expand=True, padx=8, pady=6)

        # --- Sponsors ---
        frame_spon = ttk.Labelframe(self, text="Sponsor Full Name (multi-select)")
        frame_spon.grid(row=1, column=0, sticky="ew", **pad)
        sponsors = build_unique_sponsors(self.db)
        self.spon_list = tk.Listbox(frame_spon, selectmode="extended", width=50, height=min(8, max(3, len(sponsors))))
        for i, s in enumerate(sponsors):
            self.spon_list.insert("end", s)
            if s in selected_sponsors:
                self.spon_list.selection_set(i)
        self.spon_list.pack(fill="both", expand=True, padx=8, pady=6)

        # --- Bill Type & Origin Chamber ---
        row2 = ttk.Frame(self)
        row2.grid(row=2, column=0, sticky="ew", **pad)
        # Bill types (multi)
        bt_frame = ttk.Labelframe(row2, text="Bill Type")
        bt_frame.pack(side="left", padx=(0, 12))
        self.bt_vars = {}
        for bt in FIXED_BILL_TYPES:
            var = tk.BooleanVar(value=(bt in selected_bill_types))
            self.bt_vars[bt] = var
            ttk.Checkbutton(bt_frame, text=bt, variable=var).pack(anchor="w")

        # Origin chamber (multi)
        oc_frame = ttk.Labelframe(row2, text="Origin Chamber")
        oc_frame.pack(side="left")
        self.oc_vars = {}
        for oc in FIXED_ORIGIN_CHAMBERS:
            var = tk.BooleanVar(value=(oc in selected_chambers))
            self.oc_vars[oc] = var
            ttk.Checkbutton(oc_frame, text=oc, variable=var).pack(anchor="w")

        # --- Date range (exclusive mode) ---
        frame_date = ttk.Labelframe(self, text="Date range (choose one)")
        frame_date.grid(row=3, column=0, sticky="ew", **pad)
        self.date_mode = tk.StringVar(value=date_mode)
        mode_row = ttk.Frame(frame_date)
        mode_row.pack(fill="x", padx=8, pady=(6, 0))
        ttk.Radiobutton(mode_row, text="None", value="none", variable=self.date_mode).pack(side="left")
        ttk.Radiobutton(mode_row, text="Introduced Date", value="introduced", variable=self.date_mode).pack(side="left", padx=(12, 0))
        ttk.Radiobutton(mode_row, text="Latest Action Date", value="latest", variable=self.date_mode).pack(side="left", padx=(12, 0))

        range_row = ttk.Frame(frame_date)
        range_row.pack(fill="x", padx=8, pady=(6, 8))
        ttk.Label(range_row, text="From (YYYY-MM-DD):").pack(side="left")
        self.date_from = ttk.Entry(range_row, width=16)
        self.date_from.insert(0, date_from)
        self.date_from.pack(side="left", padx=(6, 12))
        ttk.Label(range_row, text="To (YYYY-MM-DD):").pack(side="left")
        self.date_to = ttk.Entry(range_row, width=16)
        self.date_to.insert(0, date_to)
        self.date_to.pack(side="left", padx=(6, 12))

        # --- Sort override ---
        frame_sort = ttk.Labelframe(self, text="Sort")
        frame_sort.grid(row=4, column=0, sticky="ew", **pad)
        srow = ttk.Frame(frame_sort)
        srow.pack(fill="x", padx=8, pady=6)
        ttk.Label(srow, text="Field:").pack(side="left")
        self.sort_field = tk.StringVar(value=sort_field)
        ttk.Radiobutton(srow, text="Latest Action Date", value="latest", variable=self.sort_field).pack(side="left", padx=(6, 12))
        ttk.Radiobutton(srow, text="Introduced Date", value="introduced", variable=self.sort_field).pack(side="left")
        ttk.Label(srow, text="Direction:").pack(side="left", padx=(12, 0))
        self.sort_dir = tk.StringVar(value=sort_dir)
        ttk.Radiobutton(srow, text="Newest → Oldest", value="desc", variable=self.sort_dir).pack(side="left", padx=(6, 12))
        ttk.Radiobutton(srow, text="Oldest → Newest", value="asc", variable=self.sort_dir).pack(side="left")

        # --- Buttons ---
        btns = ttk.Frame(self)
        btns.grid(row=5, column=0, sticky="e", **pad)
        ttk.Button(btns, text="Clear Filters", command=self.on_clear).pack(side="left", padx=(0, 12))
        ttk.Button(btns, text="Cancel", command=self.on_cancel).pack(side="left")
        ttk.Button(btns, text="Apply", command=self.on_apply).pack(side="left", padx=(12, 0))

        self.bind("<Escape>", lambda e: self.on_cancel())
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # center relative to parent
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx()+60}+{parent.winfo_rooty()+60}")

    def _selected_from_list(self, listbox: tk.Listbox) -> List[str]:
        return [listbox.get(i) for i in listbox.curselection()]

    def on_clear(self):
        self.result = {
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
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

    def on_apply(self):
        self.result = {
            "committees": self._selected_from_list(self.comm_list),
            "sponsors": self._selected_from_list(self.spon_list),
            "bill_types": [k for k, v in self.bt_vars.items() if v.get()],
            "origin_chambers": [k for k, v in self.oc_vars.items() if v.get()],
            "date_mode": self.date_mode.get(),
            "date_from": self.date_from.get().strip(),
            "date_to": self.date_to.get().strip(),
            "sort_field": self.sort_field.get(),
            "sort_dir": self.sort_dir.get(),
        }
        self.destroy()

def open_filters_dialog(parent, db: Dict[str, dict], current_filters: Optional[dict] = None) -> Optional[dict]:
    dlg = FiltersDialog(parent, db, current_filters=current_filters)
    parent.wait_window(dlg)
    return dlg.result
