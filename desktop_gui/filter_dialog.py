# desktop_gui/filter_dialog.py
# Modal dialog to edit table filters & sorting.
# Returns a dict (same shape as app.py's self.filters) or None if canceled.

import tkinter as tk
from tkinter import ttk

def _unique_values(db, key):
    """Collect unique non-empty values from record['congressGovData'][key]."""
    vals = set()
    for rec in db.values():
        cg = (rec or {}).get("congressGovData", {}) or {}
        v = cg.get(key)
        if v:
            vals.add(str(v))
    return sorted(vals)

class FilterDialog(tk.Toplevel):
    BILL_TYPES = ["HR", "S", "HJRES", "SJRES", "HCONRES", "SCONRES"]
    CHAMBERS   = ["House", "Senate"]

    def __init__(self, parent, initial_filters: dict, db: dict):
        super().__init__(parent)
        self.title("Filters")
        self.resizable(False, False)
        self.transient(parent)
        self.result = None

        # Build option lists from DB
        self.committee_options = _unique_values(db, "currentCommitteeName")
        self.sponsor_options   = _unique_values(db, "sponsorFullName")

        # Clone initial filters
        f = initial_filters or {}
        self.init_committees = set(f.get("committees") or [])
        self.init_sponsors   = set(f.get("sponsors") or [])
        self.init_types      = set(f.get("types") or [])
        self.init_chambers   = set(f.get("chambers") or [])
        self.init_date_field = f.get("date_field") or "latestActionDate"
        self.init_date_from  = f.get("date_from") or ""
        self.init_date_to    = f.get("date_to") or ""
        self.init_sort_field = f.get("sort_field") or "latestActionDate"
        self.init_sort_dir   = f.get("sort_dir") or "desc"

        # Layout: two columns
        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)

        left  = ttk.Frame(body); left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ttk.Frame(body); right.grid(row=0, column=1, sticky="nsew")

        # ---- Left column: Committees, Sponsors ----
        ttk.Label(left, text="Committees").pack(anchor="w")
        self.lb_comm = tk.Listbox(left, selectmode="extended", height=10, width=36)
        for i, val in enumerate(self.committee_options):
            self.lb_comm.insert("end", val)
            if val in self.init_committees:
                self.lb_comm.selection_set(i)
        self.lb_comm.pack(fill="x", pady=(2, 10))

        ttk.Label(left, text="Sponsors").pack(anchor="w")
        self.lb_spons = tk.Listbox(left, selectmode="extended", height=10, width=36)
        for i, val in enumerate(self.sponsor_options):
            self.lb_spons.insert("end", val)
            if val in self.init_sponsors:
                self.lb_spons.selection_set(i)
        self.lb_spons.pack(fill="x", pady=(2, 0))

        # ---- Right column: Types, Chambers, Date filter, Sort ----
        grp_types = ttk.LabelFrame(right, text="Bill Types")
        grp_types.pack(fill="x", pady=(0, 8))
        self.var_types = {t: tk.BooleanVar(value=(t in self.init_types)) for t in self.BILL_TYPES}
        row = ttk.Frame(grp_types); row.pack(anchor="w", pady=4)
        for i, t in enumerate(self.BILL_TYPES):
            ttk.Checkbutton(row, text=t, variable=self.var_types[t]).grid(row=0, column=i, padx=4, sticky="w")

        grp_ch = ttk.LabelFrame(right, text="Origin Chamber")
        grp_ch.pack(fill="x", pady=(0, 8))
        self.var_chambers = {c: tk.BooleanVar(value=(c in self.init_chambers)) for c in self.CHAMBERS}
        row = ttk.Frame(grp_ch); row.pack(anchor="w", pady=4)
        for i, c in enumerate(self.CHAMBERS):
            ttk.Checkbutton(row, text=c, variable=self.var_chambers[c]).grid(row=0, column=i, padx=4, sticky="w")

        grp_date = ttk.LabelFrame(right, text="Date Filter")
        grp_date.pack(fill="x", pady=(0, 8))
        self.var_date_field = tk.StringVar(value=self.init_date_field)
        frow = ttk.Frame(grp_date); frow.pack(anchor="w", pady=(4, 6))
        ttk.Radiobutton(frow, text="Latest Action Date", value="latestActionDate",
                        variable=self.var_date_field).grid(row=0, column=0, padx=4, sticky="w")
        ttk.Radiobutton(frow, text="Introduced Date", value="introducedDate",
                        variable=self.var_date_field).grid(row=0, column=1, padx=12, sticky="w")

        dr = ttk.Frame(grp_date); dr.pack(anchor="w", pady=(0, 4))
        ttk.Label(dr, text="From (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        self.var_date_from = tk.StringVar(value=self.init_date_from)
        ttk.Entry(dr, textvariable=self.var_date_from, width=14).grid(row=0, column=1, padx=(6, 12))
        ttk.Label(dr, text="To (YYYY-MM-DD):").grid(row=0, column=2, sticky="w")
        self.var_date_to = tk.StringVar(value=self.init_date_to)
        ttk.Entry(dr, textvariable=self.var_date_to, width=14).grid(row=0, column=3, padx=(6, 0))

        grp_sort = ttk.LabelFrame(right, text="Sort")
        grp_sort.pack(fill="x", pady=(0, 8))
        self.var_sort_field = tk.StringVar(value=self.init_sort_field)
        self.var_sort_dir   = tk.StringVar(value=self.init_sort_dir)
        sf = ttk.Frame(grp_sort); sf.pack(anchor="w", pady=(4, 6))
        ttk.Radiobutton(sf, text="Latest Action Date", value="latestActionDate",
                        variable=self.var_sort_field).grid(row=0, column=0, padx=4, sticky="w")
        ttk.Radiobutton(sf, text="Introduced Date", value="introducedDate",
                        variable=self.var_sort_field).grid(row=0, column=1, padx=12, sticky="w")
        sd = ttk.Frame(grp_sort); sd.pack(anchor="w")
        ttk.Radiobutton(sd, text="Newest → Oldest", value="desc",
                        variable=self.var_sort_dir).grid(row=0, column=0, padx=4, sticky="w")
        ttk.Radiobutton(sd, text="Oldest → Newest", value="asc",
                        variable=self.var_sort_dir).grid(row=0, column=1, padx=12, sticky="w")

        # Buttons
        btns = ttk.Frame(self); btns.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(btns, text="Clear", command=self._on_clear).pack(side="left")
        ttk.Button(btns, text="Cancel", command=self._on_cancel).pack(side="right")
        ttk.Button(btns, text="Apply", command=self._on_apply).pack(side="right", padx=(0, 8))

        # Center near parent and modalize
        self.update_idletasks()
        self._center_over_parent(parent)
        self.grab_set()
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _center_over_parent(self, parent):
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            w  = self.winfo_reqwidth()
            h  = self.winfo_reqheight()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 3
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _collect_listbox(self, listbox, options):
        sel = listbox.curselection()
        return { options[i] for i in sel }

    def _on_apply(self):
        committees = self._collect_listbox(self.lb_comm, self.committee_options)
        sponsors   = self._collect_listbox(self.lb_spons, self.sponsor_options)
        types      = { t for t, var in self.var_types.items() if var.get() }
        chambers   = { c for c, var in self.var_chambers.items() if var.get() }
        date_field = self.var_date_field.get()
        date_from  = self.var_date_from.get().strip() or None
        date_to    = self.var_date_to.get().strip() or None
        sort_field = self.var_sort_field.get()
        sort_dir   = self.var_sort_dir.get()

        self.result = {
            # text search stays as-is in app.py (not edited here)
            "committees": committees,
            "sponsors": sponsors,
            "types": types,
            "chambers": chambers,
            "date_field": date_field,
            "date_from": date_from,
            "date_to": date_to,
            "sort_field": sort_field,
            "sort_dir": sort_dir,
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

    def _on_clear(self):
        # Reset all controls to "no filters" but keep sort defaults
        self.lb_comm.selection_clear(0, "end")
        self.lb_spons.selection_clear(0, "end")
        for var in self.var_types.values():
            var.set(False)
        for var in self.var_chambers.values():
            var.set(False)
        self.var_date_from.set("")
        self.var_date_to.set("")
        # sort + date field remain unchanged (user can change if desired)

    def show(self):
        self.wait_window(self)
        return self.result
