# HillWatch 2 – Single-Card Preview (Tkinter)
# Run: python desktop_gui/app_onecard.py

import json, os, webbrowser, tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from pathlib import Path
from datetime import datetime

try:
    from config import DB_PATH
except Exception:
    DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bills_119.json"

TARGET_BILL_ID = "S_2682"  # change as needed

# Colors & sizing
CARD_BG = "#F2F5FF"     # Ghost White
BORDER_BG = "#235789"   # Lapis Lazuli
CARD_HEIGHT = 60       # fixed height for consistent cards

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

def pick_bill(db: dict):
    if TARGET_BILL_ID and TARGET_BILL_ID in db:
        return TARGET_BILL_ID, db[TARGET_BILL_ID]
    def iso_key(v):
        if not v: return ""
        return str(v).replace("Z", "")
    best = None; best_pair = None
    for k, v in db.items():
        key = (iso_key(v.get("congressGovData", {}).get("updateDateIncludingText")), k)
        if best is None or key > best:
            best = key; best_pair = (k, v)
    return best_pair or next(iter(db.items()))

class BillCard(tk.Frame):
    def __init__(self, parent, owner_window, bill_id: str, record: dict, *args, **kwargs):
        super().__init__(parent, bg=BORDER_BG, bd=0, highlightthickness=0, *args, **kwargs)
        self.owner = owner_window
        self.bill_id = bill_id
        self.record = record

        cg = record.get("congressGovData", {})
        cd = (record.get("customData") or {})
        review = (cd.get("Review") or {})
        self.watchlist = bool(review.get("WatchList", False))
        self.congress_url = cg.get("congressGovUrl")

        # Inner content (ghost white) with fixed height
        self.inner = tk.Frame(self, bg=CARD_BG, height=CARD_HEIGHT)
        self.inner.pack(fill="x", padx=2, pady=2)
        self.inner.pack_propagate(False)  # keep fixed height

        # Header row: title (single line) + right buttons
        self.header = tk.Frame(self.inner, bg=CARD_BG)
        self.header.pack(fill="x", pady=16)

        # Full title text; we will ellipsize it
        self.title_full = f"{cg.get('billType','')} {cg.get('billNumber','')} – {cg.get('title','')}"
        self.title_lbl = tk.Label(
            self.header, text=self.title_full, font=("Segoe UI", 12, "bold"),
            bg=CARD_BG, fg="black", anchor="w", justify="left"
        )
        self.title_lbl.pack(side="left", fill="x", expand=True)

        # Right-side buttons container
        self.btns = tk.Frame(self.header, bg=CARD_BG)
        self.btns.pack(side="right")

        self.more_btn = ttk.Button(self.btns, text="⋮", width=2, command=self.on_more)
        self.more_btn.pack(side="right")

        self.star_btn = ttk.Button(
            self.btns, text="★" if self.watchlist else "☆",
            width=2, command=self.toggle_watchlist
        )
        self.star_btn.pack(side="right", padx=(0, 6))

        # Make the whole card act as a link (except clicking the buttons)
        self.inner.configure(cursor="hand2")
        self.inner.bind("<Button-1>", self.open_link)
        self.title_lbl.bind("<Button-1>", self.open_link)
        self.star_btn.bind("<Button-1>", lambda e: None)  # don't bubble to link
        self.more_btn.bind("<Button-1>", lambda e: None)

        # Ellipsize title to available width and keep it updated on resize
        self.header.bind("<Configure>", lambda e: self._refresh_title_ellipsis())
        self.after(0, self._refresh_title_ellipsis)

    # ---------- Title ellipsis ----------
    def _refresh_title_ellipsis(self):
        # Available pixels = header width - buttons width - some padding
        header_w = max(0, self.header.winfo_width())
        btns_w = self.btns.winfo_width()
        avail = max(0, header_w - btns_w - 20)  # padding fudge

        if avail <= 0:
            return

        font = tkfont.Font(font=self.title_lbl.cget("font"))
        text = self.title_full

        # If it already fits, use full
        if font.measure(text) <= avail:
            if self.title_lbl.cget("text") != text:
                self.title_lbl.config(text=text)
            return

        # Binary search the largest substring that fits with "..."
        lo, hi = 0, len(text)
        best = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            candidate = text[:mid].rstrip() + "..."
            if font.measure(candidate) <= avail:
                best = candidate
                lo = mid + 1
            else:
                hi = mid - 1

        if not best:  # fallback, at least show ellipsis
            best = "..."

        if self.title_lbl.cget("text") != best:
            self.title_lbl.config(text=best)

    # ---------- Behaviors ----------
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
        except Exception as e:
            messagebox.showerror("Save error", f"Could not save WatchList:\n{e}")

    def open_link(self, event=None):
        if not self.congress_url:
            messagebox.showinfo("No link", "No Congress.gov URL available for this bill.")
            return
        try:
            webbrowser.open(self.congress_url, new=2)
        except Exception as e:
            messagebox.showerror("Open link error", str(e))

    def on_more(self):
        messagebox.showinfo("More", f"More actions for {self.bill_id} (coming soon).")

class OneCardWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HillWatch 2 – Card Preview")
        self.geometry("1000x260")      # balanced height now that card is fixed-height
        self.minsize(820, 220)

        top = ttk.Frame(self, padding=(12, 10))
        top.pack(fill="x")

        self.path_lbl = ttk.Label(top, text=f"DB: {Path(DB_PATH).resolve()}")
        self.path_lbl.pack(side="left")
        self.time_lbl = ttk.Label(top, text="")
        self.time_lbl.pack(side="left", padx=(12, 0))
        ttk.Button(top, text="Reload", command=self.reload).pack(side="right")

        self.container = ttk.Frame(self, padding=(12, 0))
        self.container.pack(fill="both", expand=True)

        self.db = {}; self.card_widget = None
        self.reload()

    def refresh_last_saved(self):
        try:
            mtime = datetime.fromtimestamp(Path(DB_PATH).stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            mtime = "N/A"
        self.time_lbl.config(text=f"Last saved: {mtime}")

    def reload(self):
        try:
            self.db = load_db()
        except Exception as e:
            messagebox.showerror("Load error", str(e)); return

        self.refresh_last_saved()
        for child in self.container.winfo_children():
            child.destroy()

        bill_id, rec = pick_bill(self.db)
        wrapper = ttk.Frame(self.container)
        wrapper.pack(expand=True, fill="x")
        card = BillCard(wrapper, self, bill_id, rec)
        card.pack(fill="x", padx=8, pady=8)
        self.card_widget = card

def main():
    OneCardWindow().mainloop()

if __name__ == "__main__":
    main()
