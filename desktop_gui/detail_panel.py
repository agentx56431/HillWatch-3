# desktop_gui/detail_panel.py
# Right pane: single scroll area, CG Data (open) + Custom (collapsed),
# vertical Review/Outreach/FinalTracking, clean spacing, section dividers, compact styles.

import tkinter as tk
from tkinter import ttk
import webbrowser

from desktop_gui.collapsible import Collapsible
from desktop_gui.editor_fields import BoolCheck, TextEntry, DateEntryValidated, CeiExpertPicker

# ----- Read-only CG keys display order -----
READONLY_KEYS_ORDER = [
    "billId","congress","billType","billNumber","title","originChamber",
    "introducedDate","sponsorFullName","sponsorParty","sponsorState","sponsorDistrict",
    "currentCommitteeName","currentSubcommitteeName","latestActionText","latestActionDate",
    "updateDate","updateDateIncludingText","sourceUrl","congressGovUrl","contentHash","committeeLastActionSeen",
]

# ----- Layout constants (tweak to taste) -----
P_INNER = (14, 12)    # padding for inner scroll frame
P_SECT  = (0, 6)      # spacing around top-level sections
P_BODY  = (6, 6)      # padding inside section bodies
ROW_PADY = 2          # vertical spacing per row
LABEL_W = 26          # label column width in CG grid
VALUE_W = 80          # value column width in CG grid

# ----- Typography helpers -----
DEFAULT_FONT      = ("Segoe UI", 9)
DEFAULT_FONT_BOLD = ("Segoe UI", 9, "bold")
SMALL_FONT        = ("Segoe UI", 8)

def apply_detail_styles(widget):
    """Apply minimal ttk styles used in the detail panel."""
    style = ttk.Style(widget)
    style.configure("HW.TLabel", font=DEFAULT_FONT)
    style.configure("HW.Small.TLabel", font=SMALL_FONT, foreground="#333333")
    style.configure("HW.Header.TLabel", font=("Segoe UI", 10, "bold"))
    style.configure("HW.Success.TLabel", foreground="#2e7d32", font=SMALL_FONT)


class DetailPanel(ttk.Frame):
    def __init__(self, parent, on_toggle_watchlist, on_set_custom_field=None):
        super().__init__(parent)

        apply_detail_styles(self)

        self.on_toggle_watchlist = on_toggle_watchlist
        self.on_set_custom_field = on_set_custom_field
        self.bill_id = None
        self._record = {}
        self._congress_url = None
        self._saved_after_id = None

        # ===== Single scroll area =====
        outer = ttk.Frame(self); outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(outer, highlightthickness=0)
        vscroll = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vscroll.set)

        self.inner = ttk.Frame(self.canvas, padding=P_INNER)
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        # ===== Header =====
        self.header_var = tk.StringVar(value="Select a row to view details")
        ttk.Label(self.inner, textvariable=self.header_var, style="HW.Header.TLabel").pack(anchor="w")

        hdr_row = ttk.Frame(self.inner); hdr_row.pack(anchor="w", pady=(8, 6), fill="x")
        self.view_btn = ttk.Button(hdr_row, text="View Legislation in Browser",
                                   command=self._open_in_browser, state="disabled")
        self.view_btn.pack(side="left")

        self.watch_var = tk.BooleanVar(value=False)
        self.watch_btn = ttk.Checkbutton(hdr_row, text="⭐ WatchList", variable=self.watch_var,
                                         command=self._toggle_watchlist, state="disabled")
        self.watch_btn.pack(side="left", padx=(12, 0))

        self.saved_var = tk.StringVar(value="")
        ttk.Label(self.inner, textvariable=self.saved_var, style="HW.Success.TLabel").pack(anchor="w")

        ttk.Separator(self.inner, orient="horizontal").pack(fill="x", pady=(10, 8))

        # ===== Congress.gov Data (OPEN) =====
        self.cg_section = Collapsible(self.inner, "Congress.gov Data", start_open=True)
        self.cg_section.pack(fill="x", expand=False, pady=P_SECT)
        self.cg_body = ttk.Frame(self.cg_section.body, padding=P_BODY); self.cg_body.pack(fill="x", expand=True)
        self.cg_grid = ttk.Frame(self.cg_body); self.cg_grid.pack(fill="x", expand=True)

        ttk.Separator(self.inner, orient="horizontal").pack(fill="x", pady=(8, 8))

        # ===== Custom (COLLAPSED) =====
        self.custom_section = Collapsible(self.inner, "Custom", start_open=False)
        self.custom_section.pack(fill="x", expand=True, pady=P_SECT)

        # Sub-collapsibles (vertical)
        self.rev_section = Collapsible(self.custom_section.body, "Review", start_open=True)
        self.out_section = Collapsible(self.custom_section.body, "Outreach", start_open=False)
        self.fin_section = Collapsible(self.custom_section.body, "FinalTracking", start_open=False)

        self.rev_section.pack(fill="x", pady=(4, 4))
        ttk.Separator(self.custom_section.body, orient="horizontal").pack(fill="x", padx=6, pady=(2, 2))
        self.out_section.pack(fill="x", pady=(4, 4))
        ttk.Separator(self.custom_section.body, orient="horizontal").pack(fill="x", padx=6, pady=(2, 2))
        self.fin_section.pack(fill="x", pady=(4, 4))

        # Bodies for vertical form rows
        self.rev_body = ttk.Frame(self.rev_section.body, padding=P_BODY); self.rev_body.pack(fill="x")
        self.out_body = ttk.Frame(self.out_section.body, padding=P_BODY); self.out_body.pack(fill="x")
        self.fin_body = ttk.Frame(self.fin_section.body, padding=P_BODY); self.fin_body.pack(fill="x")

    # ===== mouse wheel =====
    def _on_mousewheel(self, event): self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # ===== link / star =====
    def _open_in_browser(self):
        if self._congress_url: webbrowser.open(self._congress_url)

    def _toggle_watchlist(self):
        if not self.bill_id: return
        new_val = bool(self.watch_var.get())
        ok = False
        try: ok = bool(self.on_toggle_watchlist(self.bill_id, new_val))
        except Exception: ok = False
        if ok: self._toast("Saved")
        else:  self.watch_var.set(not new_val)

    def _toast(self, msg):
        self.saved_var.set(msg)
        if self._saved_after_id: self.after_cancel(self._saved_after_id)
        self._saved_after_id = self.after(1200, lambda: self.saved_var.set(""))

    def _set_custom(self, group: str, key: str, value):
        if not callable(self.on_set_custom_field) or not self.bill_id: return False
        ok = self.on_set_custom_field(self.bill_id, group, key, value)
        if ok: self._toast("Saved")
        return ok

    # ===== row builders (vertical) =====
    def _line_check(self, parent, group, key, label, src_dict):
        row = ttk.Frame(parent); row.pack(fill="x", pady=ROW_PADY)
        BoolCheck(row, self.bill_id, group, key,
                  lambda: src_dict.get(key, False),
                  lambda bid, grp, k, v: self._set_custom(grp, k, v),
                  label).pack(side="left")

    def _line_text(self, parent, group, key, label, get_value, width=56):
        row = ttk.Frame(parent); row.pack(fill="x", pady=ROW_PADY)
        ttk.Label(row, text=label, style="HW.TLabel").pack(side="left", padx=(0, 6))
        TextEntry(row, self.bill_id, group, key,
                  get_value,
                  lambda bid, grp, k, v: self._set_custom(grp, k, v),
                  width=width).pack(side="left", fill="x", expand=True)

    def _line_date(self, parent, group, key, label, get_value):
        row = ttk.Frame(parent); row.pack(fill="x", pady=ROW_PADY)
        ttk.Label(row, text=label, style="HW.TLabel").pack(side="left", padx=(0, 6))
        DateEntryValidated(row, self.bill_id, group, key,
                           get_value,
                           lambda bid, grp, k, v: self._set_custom(grp, k, v)).pack(side="left")

    def _line_widget(self, parent, label_text, widget):
        row = ttk.Frame(parent); row.pack(fill="x", pady=ROW_PADY)
        ttk.Label(row, text=label_text, style="HW.TLabel").pack(side="left", padx=(0, 6))
        widget.pack(side="left")

    # ===== render selection =====
    def show_bill(self, bill_id: str, record: dict):
        self.bill_id = bill_id
        self._record = record or {}

        cg = self._record.get("congressGovData", {}) or {}
        cd = self._record.get("customData", {}) or {}
        review   = cd.get("Review", {}) or {}
        outreach = cd.get("Outreach", {}) or {}
        final    = cd.get("FinalTracking", {}) or {}

        # Header
        bt, num, title = cg.get("billType", ""), cg.get("billNumber", ""), cg.get("title", "")
        self.header_var.set(f"{bt} {num} — {title}")

        # Link & Watch
        self._congress_url = cg.get("congressGovUrl") or None
        self.view_btn.configure(state="normal" if self._congress_url else "disabled")
        self.watch_var.set(bool(review.get("WatchList", False)))
        self.watch_btn.configure(state="normal")

        # ---- Congress.gov Data grid ----
        for w in self.cg_grid.winfo_children(): w.destroy()

        r = 0
        def add_kv(label, value):
            nonlocal r
            ttk.Label(self.cg_grid, text=f"{label}:", width=LABEL_W, style="HW.Small.TLabel")\
               .grid(row=r, column=0, sticky="w", padx=(4, 8), pady=ROW_PADY)
            ttk.Label(self.cg_grid, text="" if value is None else str(value), width=VALUE_W, style="HW.TLabel")\
               .grid(row=r, column=1, sticky="w", padx=(0, 4), pady=ROW_PADY)
            r += 1

        seen = set()
        for k in READONLY_KEYS_ORDER:
            if k in cg: add_kv(k, cg.get(k)); seen.add(k)
        for k, v in cg.items():
            if k not in seen: add_kv(k, v)

        # ---- Custom editor (VERTICAL) ----
        for f in self.rev_body.winfo_children(): f.destroy()
        for f in self.out_body.winfo_children(): f.destroy()
        for f in self.fin_body.winfo_children(): f.destroy()

        # === REVIEW (reorder these for your preferred order) ===
        self._line_check(self.rev_body, "Review", "CEIExpertAcceptOrReject", "Accept (CEIExpertAcceptOrReject)", review)
        self._line_check(self.rev_body, "Review", "Review_Done", "Review_Done", review)
        self._line_check(self.rev_body, "Review", "StatementRequested", "StatementRequested", review)
        self._line_date(self.rev_body, "Review", "StatementRequestedDate", "StatementRequestedDate:",
                        lambda: review.get("StatementRequestedDate"))
        self._line_widget(
            self.rev_body, "CeiExpert:",
            CeiExpertPicker(
                self.rev_body, self.bill_id,
                get_options=lambda: review.get("CeiExpertOptions", []),
                get_current=lambda: review.get("CeiExpert", []),
                set_value_callback=lambda bid, grp, key, val: self._set_custom(grp, key, val),
            )
        )

        # === OUTREACH ===
        for key, label in [
            ("Worked_Directly_with_Office", "Worked_Directly_with_Office"),
            ("Statement_Complete", "Statement_Complete"),
        ]:
            self._line_check(self.out_body, "Outreach", key, label, outreach)
        self._line_date(self.out_body, "Outreach", "Statement_Complete_Date", "Statement_Complete_Date:",
                        lambda: outreach.get("Statement_Complete_Date"))
        for key, label in [
            ("Statement_Emailed_Directly", "Statement_Emailed_Directly"),
            ("Statement_Emailed_Quorum", "Statement_Emailed_Quorum"),
            ("InternalLed_Coalition_Letter", "InternalLed_Coalition_Letter"),
            ("ExternalLed_Coalition_Letter", "ExternalLed_Coalition_Letter"),
            ("Support_Posted_Website", "Support_Posted_Website"),
        ]:
            self._line_check(self.out_body, "Outreach", key, label, outreach)
        self._line_text(self.out_body, "Outreach", "Other_Support", "Other_Support:",
                        lambda: outreach.get("Other_Support", ""), width=56)
        self._line_check(self.out_body, "Outreach", "Outreach_Done", "Outreach_Done", outreach)

        # === FINAL TRACKING ===
        self._line_check(self.fin_body, "FinalTracking", "Press_Release_Mention", "Press_Release_Mention", final)
        self._line_text(self.fin_body, "FinalTracking", "Press Release Mention_Source",
                        "Press Release Mention_Source:", lambda: final.get("Press Release Mention_Source", ""), width=56)
        self._line_check(self.fin_body, "FinalTracking", "Any_Public_Mention", "Any_Public_Mention", final)
        self._line_text(self.fin_body, "FinalTracking", "Any_Public_Mention_Source",
                        "Any_Public_Mention_Source:", lambda: final.get("Any_Public_Mention_Source", ""), width=56)
        self._line_text(self.fin_body, "FinalTracking", "Notes_or_Other",
                        "Notes_or_Other:", lambda: final.get("Notes_or_Other", ""), width=56)
        self._line_date(self.fin_body, "FinalTracking", "Public_Mention_Date",
                        "Public_Mention_Date:", lambda: final.get("Public_Mention_Date"))
        self._line_check(self.fin_body, "FinalTracking", "Final_Tracking_Done", "Final_Tracking_Done", final)
