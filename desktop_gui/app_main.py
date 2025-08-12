# HillWatch 2 – Desktop (Tkinter)
# Split window: left = tabs with scrollable cards, right = details pane/editor
# Tabs: Bills (all), WatchList (filtered), Rejected, Complete
# - Cards: fixed size, ellipsized title, WatchList star persists, ⋮ opens right-side pane
# - Right-side: JSON view OR live "customData" editor (with collapsible sections)
#
# Run: python desktop_gui/app_main.py

import json, os, re, webbrowser, platform, tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from pathlib import Path
from datetime import datetime

# ---------- Config / Paths ----------
try:
    from config import DB_PATH
except Exception:
    DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bills_119.json"

# ---------- Visual constants ----------
CARD_BG     = "#F2F5FF"   # Ghost White
BORDER_BG   = "#235789"   # Lapis Lazuli
CARD_HEIGHT = 60          # fixed card height
CARD_WIDTH  = 540         # fixed card width (~half page)
TITLE_FONT  = ("Segoe UI", 9, "bold")
BATCH_SIZE  = 40          # cards per batch
MAX_CARDS   = 200         # limit to first 200 per tab
INNER_PAD_L = 16
INNER_PAD_R = 12
BUTTONS_PAD = 8

# ---------- Data helpers ----------
def load_db():
    if not Path(DB_PATH).exists():
        raise FileNotFoundError(f"Database not found at: {DB_PATH}")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def atomic_save_db(db: dict):
    tmp = Path(DB_PATH).with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
    os.replace(tmp, DB_PATH)

def bill_sort_key(item):
    bill_id, rec = item
    cg = rec.get("congressGovData", {})
    bt = (cg.get("billType") or "").upper()
    num = cg.get("billNumber") or "0"
    try:
        n = int(num)
    except Exception:
        n = 0
    return (bt, -n)

# ---------- Scrollable container ----------
class ScrollFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self._bind_mousewheel()

    def _bind_mousewheel(self):
        sys = platform.system()
        if sys == "Windows":
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        elif sys == "Darwin":
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_mac)
        else:
            self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _on_mousewheel_windows(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_mac(self, event):
        self.canvas.yview_scroll(int(-1 * event.delta), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(3, "units")

    def _on_inner_configure(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.inner_id, width=event.width)

# ---------- Card widget ----------
class BillCard(tk.Frame):
    def __init__(self, parent, owner_window, bill_id: str, record: dict):
        super().__init__(parent, bg=BORDER_BG, bd=0, highlightthickness=0,
                         width=CARD_WIDTH, height=CARD_HEIGHT + 4)
        self.pack_propagate(False)
        self.owner = owner_window
        self.bill_id = bill_id
        self.record = record

        cg = record.get("congressGovData", {})
        cd = (record.get("customData") or {})
        review = (cd.get("Review") or {})
        self.watchlist = bool(review.get("WatchList", False))
        self.congress_url = cg.get("congressGovUrl")

        # Inner content
        self.inner = tk.Frame(self, bg=CARD_BG)
        self.inner.pack(fill="both", expand=True, padx=2, pady=2)

        # Header row (grid)
        self.header = tk.Frame(self.inner, bg=CARD_BG)
        self.header.pack(fill="both", expand=True, pady=10, padx=(INNER_PAD_L, INNER_PAD_R))
        self.header.columnconfigure(0, weight=1)
        self.header.columnconfigure(1, weight=0)

        # Title
        self.title_full = f"{cg.get('billType','')} {cg.get('billNumber','')} – {cg.get('title','')}"
        self.title_lbl = tk.Label(self.header, text=self.title_full, font=TITLE_FONT,
                                  bg=CARD_BG, fg="black", anchor="w", justify="left")
        self.title_lbl.grid(row=0, column=0, sticky="w")

        # Buttons
        self.btns = tk.Frame(self.header, bg=CARD_BG)
        self.btns.grid(row=0, column=1, sticky="e", padx=(BUTTONS_PAD, BUTTONS_PAD))

        self.more_btn = ttk.Button(
            self.btns, text="⋮", width=2,
            command=lambda: self.owner.show_details(self.bill_id, self.record)
        )
        self.more_btn.pack(side="right")

        self.star_btn = ttk.Button(
            self.btns, text="★" if self.watchlist else "☆", width=2, command=self.toggle_watchlist
        )
        self.star_btn.pack(side="right", padx=(0, 6))

        # Clickable card (except buttons)
        self.inner.configure(cursor="hand2")
        self.inner.bind("<Button-1>", self.open_link)
        self.title_lbl.bind("<Button-1>", self.open_link)
        self.star_btn.bind("<Button-1>", lambda e: None)
        self.more_btn.bind("<Button-1>", lambda e: None)

        # Ellipsize on resize
        self.header.bind("<Configure>", lambda e: self._refresh_title_ellipsis())
        self.after(0, self._refresh_title_ellipsis)

    def _refresh_title_ellipsis(self):
        header_w = max(0, self.header.winfo_width())
        btns_w = max(self.btns.winfo_width(), self.btns.winfo_reqwidth())
        avail = max(0, header_w - btns_w - 10)
        if avail <= 0:
            return
        font = tkfont.Font(font=self.title_lbl.cget("font"))
        text = self.title_full
        if font.measure(text) <= avail:
            if self.title_lbl.cget("text") != text:
                self.title_lbl.config(text=text)
            return
        lo, hi = 0, len(text)
        best = "..."
        while lo <= hi:
            mid = (lo + hi) // 2
            candidate = text[:mid].rstrip() + "..."
            if font.measure(candidate) <= avail:
                best = candidate
                lo = mid + 1
            else:
                hi = mid - 1
        if self.title_lbl.cget("text") != best:
            self.title_lbl.config(text=best)

    def toggle_watchlist(self):
        new_val = not self.watchlist
        try:
            db = load_db()
            if self.bill_id not in db:
                raise KeyError(f"{self.bill_id} not found in DB.")
            db[self.bill_id].setdefault("customData", {}).setdefault("Review", {})
            db[self.bill_id]["customData"]["Review"]["WatchList"] = new_val
            atomic_save_db(db)
            self.watchlist = new_val
            self.star_btn.config(text="★" if new_val else "☆")
            self.owner.refresh_last_saved()
            self.owner.refresh_filtered_tabs()  # keep WatchList/Rejected/Complete in sync
        except Exception as e:
            messagebox.showerror("Save error", f"Could not save WatchList:\n{e}")

    def open_link(self, _event=None):
        if not self.congress_url:
            messagebox.showinfo("No link", "No Congress.gov URL available for this bill.")
            return
        try:
            webbrowser.open(self.congress_url, new=2)
        except Exception as e:
            messagebox.showerror("Open link error", str(e))

# ---------- Collapsible section ----------
class Collapsible(ttk.Frame):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.var = tk.BooleanVar(value=True)
        self.header = ttk.Frame(self)
        self.header.pack(fill="x")
        self.btn = ttk.Checkbutton(self.header, text=title, variable=self.var,
                                   command=self._toggle, style="Toolbutton")
        self.btn.pack(side="left", anchor="w")
        self.body = ttk.Frame(self)
        self.body.pack(fill="x", pady=(6, 2))

    def _toggle(self):
        if self.var.get():
            self.body.pack(fill="x", pady=(6, 2))
        else:
            self.body.forget()

# ---------- CustomData editor ----------
class CustomDataForm(ttk.Frame):
    """
    Live editor for customData with instant save on change.
    Booleans -> Checkbuttons, Strings -> Entry/Text, Dates -> validated Entry (YYYY-MM-DD),
    CeiExpert -> multi-select Listbox (from CeiExpertOptions).
    """
    # Field schema: section -> list of (key, kind, label)
    SCHEMA = {
        "Review": [
            ("WatchList", "bool", "Watch List"),
            ("CeiExpert", "multi", "CEI Expert(s)"),
            ("StatementRequested", "bool", "Statement Requested"),
            ("StatementRequestedDate", "date", "Statement Requested Date"),
            ("CEIExpertAcceptOrReject", "bool", "CEI Expert Accept?"),
            ("Review_Done", "bool", "Review Done"),
        ],
        "Outreach": [
            ("Worked_Directly_with_Office", "bool", "Worked Directly with Office"),
            ("Statement_Complete", "bool", "Statement Complete"),
            ("Statement_Complete_Date", "date", "Statement Complete Date"),
            ("Statement_Emailed_Directly", "bool", "Statement Emailed Directly"),
            ("Statement_Emailed_Quorum", "bool", "Statement Emailed via Quorum"),
            ("InternalLed_Coalition_Letter", "bool", "Internal-led Coalition Letter"),
            ("ExternalLed_Coalition_Letter", "bool", "External-led Coalition Letter"),
            ("Support_Posted_Website", "bool", "Support Posted on Website"),
            ("Other_Support", "text", "Other Support"),
            ("Outreach_Done", "bool", "Outreach Done"),
        ],
        "FinalTracking": [
            ("Press_Release_Mention", "bool", "Press Release Mention"),
            ("Press Release Mention_Source", "text", "Press Release Source"),
            ("Any_Public_Mention", "bool", "Any Public Mention"),
            ("Any_Public_Mention_Source", "text", "Public Mention Source"),
            ("Notes_or_Other", "text", "Notes / Other"),
            ("Public_Mention_Date", "date", "Public Mention Date"),
            ("Final_Tracking_Done", "bool", "Final Tracking Done"),
        ],
    }

    DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # simple format check

    def __init__(self, parent, owner_window, bill_id: str, record: dict):
        super().__init__(parent)
        self.owner = owner_window
        self.bill_id = bill_id
        self.record = record
        self.inputs = {}  # (section,key) -> widget/var

        ttk.Label(self, text="customData (live)", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        # Build sections
        for section in ("Review", "Outreach", "FinalTracking"):
            sec = Collapsible(self, section)
            sec.pack(fill="x", pady=(4, 8))
            self._build_section(sec.body, section)

    def _get_cd(self):
        db = load_db()
        rec = db.get(self.bill_id, {})
        cd = rec.setdefault("customData", {})
        # ensure nested sections exist
        for s in ("Review", "Outreach", "FinalTracking"):
            cd.setdefault(s, {})
        return db, cd

    def _save_and_refresh(self, db):
        atomic_save_db(db)
        self.owner.refresh_last_saved()
        # tabs may need re-filtering (WatchList/Rejected/Complete)
        self.owner.refresh_filtered_tabs()

    def _build_section(self, parent, section_name):
        # grid layout: labels on left, widget on right
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)

        _, cd = self._get_cd()
        sec = cd.get(section_name, {})

        for row, (key, kind, label) in enumerate(self.SCHEMA[section_name]):
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 8))

            if kind == "bool":
                var = tk.BooleanVar(value=bool(sec.get(key, False)))
                cb = ttk.Checkbutton(parent, variable=var, command=lambda s=section_name, k=key, v=var: self._on_bool(s,k,v))
                cb.grid(row=row, column=1, sticky="w", pady=2)
                self.inputs[(section_name, key)] = var

            elif kind == "text":
                val = "" if sec.get(key) is None else str(sec.get(key))
                ent = ttk.Entry(parent)
                ent.insert(0, val)
                ent.grid(row=row, column=1, sticky="ew", pady=2)
                ent.bind("<FocusOut>", lambda e, s=section_name, k=key, w=ent: self._on_text(s,k,w))
                self.inputs[(section_name, key)] = ent

            elif kind == "date":
                val = "" if sec.get(key) in (None, "") else str(sec.get(key))
                vcmd = (self.register(self._validate_date), "%P")
                ent = ttk.Entry(parent, validate="focusout", validatecommand=vcmd)
                ent.insert(0, val)
                ent.grid(row=row, column=1, sticky="w", pady=2)
                ent.bind("<FocusOut>", lambda e, s=section_name, k=key, w=ent: self._on_date(s,k,w))
                # small hint
                ttk.Label(parent, text="YYYY-MM-DD", foreground="#666").grid(row=row, column=1, sticky="e", padx=(0, 8))
                self.inputs[(section_name, key)] = ent

            elif kind == "multi":
                # CeiExpert with options
                options = sec.get("CeiExpertOptions") or []
                current = set(sec.get("CeiExpert") or [])
                frame = ttk.Frame(parent)
                frame.grid(row=row, column=1, sticky="ew", pady=2)
                frame.columnconfigure(0, weight=1)

                lb = tk.Listbox(frame, selectmode="multiple", height=min(6, max(3, len(options))))
                for i, opt in enumerate(options):
                    lb.insert("end", opt)
                    if opt in current:
                        lb.selection_set(i)
                lb.grid(row=0, column=0, sticky="ew")
                lb.bind("<<ListboxSelect>>", lambda e, s=section_name, k=key, w=lb: self._on_multi(s,k,w))
                self.inputs[(section_name, key)] = lb

    def _validate_date(self, s: str):
        return s == "" or bool(self.DATE_RE.match(s))

    # --- change handlers (instant save) ---
    def _on_bool(self, section, key, var):
        try:
            db, cd = self._get_cd()
            cd[section][key] = bool(var.get())
            self._save_and_refresh(db)
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def _on_text(self, section, key, widget):
        try:
            db, cd = self._get_cd()
            cd[section][key] = widget.get()
            self._save_and_refresh(db)
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def _on_date(self, section, key, widget):
        val = widget.get().strip()
        if val and not self.DATE_RE.match(val):
            messagebox.showerror("Invalid date", "Please use YYYY-MM-DD")
            widget.focus_set()
            return
        try:
            db, cd = self._get_cd()
            cd[section][key] = val if val else None
            self._save_and_refresh(db)
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def _on_multi(self, section, key, listbox):
        try:
            db, cd = self._get_cd()
            selected = [listbox.get(i) for i in listbox.curselection()]
            cd[section][key] = selected
            self._save_and_refresh(db)
        except Exception as e:
            messagebox.showerror("Save error", str(e))

# ---------- Main window ----------
class HillWatchDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HillWatch 2 – Desktop")
        self.geometry("1200x760")
        self.minsize(1000, 620)

        # Paned window: left (tabs), right (details/editor)
        self.paned = ttk.Panedwindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        self.left = ttk.Frame(self.paned)
        self.right = ttk.Frame(self.paned)
        self.paned.add(self.left, weight=1)
        self.paned.add(self.right, weight=1)

        # ----- LEFT: top bar + tabs -----
        topbar = ttk.Frame(self.left, padding=(12, 10))
        topbar.pack(fill="x")
        self.path_lbl = ttk.Label(topbar, text=f"DB: {Path(DB_PATH).resolve()}")
        self.path_lbl.pack(side="left")
        self.time_lbl = ttk.Label(topbar, text="")
        self.time_lbl.pack(side="left", padx=(12, 0))
        ttk.Button(topbar, text="Reload", command=self.reload_all_tabs).pack(side="right")

        self.nb = ttk.Notebook(self.left)
        self.nb.pack(fill="both", expand=True)

        # Create tabs
        self.tabs = {}
        for name in ("Bills", "WatchList", "Rejected", "Complete"):
            frame = ttk.Frame(self.nb)
            self.nb.add(frame, text=name)
            status = ttk.Label(frame, text="", padding=(12, 0))
            status.pack(fill="x")
            scroll = ScrollFrame(frame)
            scroll.pack(fill="both", expand=True, padx=12, pady=(6, 12))
            self.tabs[name] = {"frame": frame, "status": status, "scroll": scroll,
                               "items": [], "batch_i": 0}

        # ----- RIGHT: details/editor -----
        self._build_details_pane()

        # Data
        self.db = {}
        self.reload_all_tabs()

    # ====== Details Pane ======
    def _build_details_pane(self):
        hdr = ttk.Frame(self.right, padding=(12, 10))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Details", font=("Segoe UI", 11, "bold")).pack(side="left")
        self.detail_title = ttk.Label(hdr, text="", foreground="#555")
        self.detail_title.pack(side="left", padx=(10, 0))

        self.detail_container = ttk.Frame(self.right)
        self.detail_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # default message
        self._show_message("Click ⋮ on a bill. If it's on your WatchList, you'll get an editor here.")

    def _clear_detail(self):
        for c in self.detail_container.winfo_children():
            c.destroy()

    def _show_message(self, text):
        self._clear_detail()
        lbl = ttk.Label(self.detail_container, text=text, foreground="#555", padding=12)
        lbl.pack(anchor="nw")

    def _show_json(self, data_obj, title=""):
        import json as _json
        self._clear_detail()
        self.detail_title.config(text=title)
        txt = tk.Text(self.detail_container, wrap="none")
        vbar = ttk.Scrollbar(self.detail_container, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=vbar.set)
        txt.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")
        try:
            txt.insert("1.0", _json.dumps(data_obj, indent=2))
        except Exception:
            txt.insert("1.0", str(data_obj))
        txt.config(state="disabled")

    def show_details(self, bill_id, record):
        self.db = load_db()  # get the latest before deciding
        rec = self.db.get(bill_id, record)
        cg = rec.get("congressGovData", {})
        cd = (rec.get("customData") or {})
        review = (cd.get("Review") or {})
        title = f"  {cg.get('billType','')} {cg.get('billNumber','')}"

        if review.get("WatchList", False):
            # show the live form editor
            self._clear_detail()
            self.detail_title.config(text=title)
            form = CustomDataForm(self.detail_container, self, bill_id, rec)
            form.pack(fill="both", expand=True, padx=4, pady=4)
        else:
            # not on watchlist: show read-only congressGovData JSON
            self._show_json(cg, title=title)

    # ====== Common helpers ======
    def refresh_last_saved(self):
        try:
            mtime = datetime.fromtimestamp(Path(DB_PATH).stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            mtime = "N/A"
        self.time_lbl.config(text=f"Last saved: {mtime}")

    def clear_feed(self, name):
        scroll = self.tabs[name]["scroll"]
        for child in scroll.inner.winfo_children():
            child.destroy()

    # ====== Loading & Rendering ======
    def reload_all_tabs(self):
        try:
            self.db = load_db()
        except Exception as e:
            messagebox.showerror("Load error", str(e))
            return
        self.refresh_last_saved()

        all_items = sorted(self.db.items(), key=bill_sort_key)
        self._set_tab_items("Bills", all_items[:MAX_CARDS])
        self._rebuild_filtered_tabs(all_items)

        # render visible tab immediately
        current = self.nb.tab(self.nb.select(), "text")
        for name in ("Bills", "WatchList", "Rejected", "Complete"):
            if name == current:
                self.render_tab(name)
            else:
                self.after(50, lambda n=name: self.render_tab(n))

    def _rebuild_filtered_tabs(self, all_items):
        # WatchList: WatchList == True and Review_Done == False
        wl = []
        # Rejected: CEIExpertAcceptOrReject == False and Review_Done == True
        rejected = []
        # Complete: Final_Tracking_Done == True
        complete = []

        for k, v in all_items:
            cd = (v.get("customData") or {})
            r = (cd.get("Review") or {})
            o = (cd.get("Outreach") or {})
            f = (cd.get("FinalTracking") or {})

            if r.get("WatchList") and not r.get("Review_Done", False):
                wl.append((k, v))
            if (r.get("Review_Done") is True) and (r.get("CEIExpertAcceptOrReject") is False):
                rejected.append((k, v))
            if f.get("Final_Tracking_Done") is True:
                complete.append((k, v))

        self._set_tab_items("WatchList", wl[:MAX_CARDS])
        self._set_tab_items("Rejected", rejected[:MAX_CARDS])
        self._set_tab_items("Complete", complete[:MAX_CARDS])

    def _set_tab_items(self, name, items):
        tab = self.tabs[name]
        tab["items"] = items
        tab["batch_i"] = 0
        self.clear_feed(name)
        total = len(items)
        tab["status"].config(text=f"{name}: {total} items (showing up to {MAX_CARDS}).")

    def render_tab(self, name):
        tab = self.tabs[name]
        start = tab["batch_i"] * BATCH_SIZE
        end = start + BATCH_SIZE
        chunk = tab["items"][start:end]
        if not chunk:
            return
        for bill_id, rec in chunk:
            card = BillCard(tab["scroll"].inner, self, bill_id, rec)
            card.pack(pady=6, anchor="n")  # centered fixed-size card
        tab["batch_i"] += 1
        self.after(10, lambda n=name: self.render_tab(n))

    # Refresh filtered tabs after any data change
    def refresh_filtered_tabs(self):
        try:
            self.db = load_db()
        except Exception:
            pass
        all_items = sorted(self.db.items(), key=bill_sort_key)
        self._rebuild_filtered_tabs(all_items)
        # re-render visible filtered tab (minor optimization)
        for name in ("WatchList", "Rejected", "Complete"):
            self.render_tab(name)

def main():
    app = HillWatchDesktop()
    app.mainloop()

if __name__ == "__main__":
    main()
