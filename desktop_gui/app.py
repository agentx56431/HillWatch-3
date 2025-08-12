# desktop_gui/app.py
# HillWatch v3 – App skeleton (window, split panes, top bar, tabs)

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Title constant
APP_TITLE = "HillWatch v3"

class HillWatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x760")
        self.minsize(1000, 620)

        # ---- Top bar ----
        top = ttk.Frame(self, padding=(12, 8))
        top.pack(side="top", fill="x")
        # spacer label (left)
        self.title_lbl = ttk.Label(top, text=APP_TITLE, font=("Segoe UI", 11, "bold"))
        self.title_lbl.pack(side="left")
        # Reload button (stub)
        self.reload_btn = ttk.Button(top, text="Reload", command=self.on_reload_clicked)
        self.reload_btn.pack(side="right")

        # ---- Split panes (left = tabs, right = details) ----
        self.paned = ttk.Panedwindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        self.left = ttk.Frame(self.paned)   # will host tabs + tables (later)
        self.right = ttk.Frame(self.paned)  # will host details/editor (later)

        # add to paned
        self.paned.add(self.left, weight=1)
        self.paned.add(self.right, weight=1)

        # ---- Tabs on left ----
        self.nb = ttk.Notebook(self.left)
        self.nb.pack(fill="both", expand=True, padx=12, pady=12)

        self.tabs = {}
        for name in ("Bills Feed", "WatchList", "Rejected", "Complete"):
            frame = ttk.Frame(self.nb)
            self.nb.add(frame, text=name)
            self.tabs[name] = frame

            # placeholder content so you see each tab works
            ph = ttk.Label(frame, text=f"{name} (placeholder)", padding=(12, 8))
            ph.pack(anchor="nw")

        # ---- Right pane placeholder ----
        right_wrap = ttk.Frame(self.right, padding=(12, 12))
        right_wrap.pack(fill="both", expand=True)
        ttk.Label(
            right_wrap,
            text="Select a row to view details here.\n(Details/editor will appear in later phases.)",
            foreground="#555"
        ).pack(anchor="nw")

    # ---- Events ----
    def on_reload_clicked(self):
        # Stub for now: later this will run updater.py and then reload JSON
        messagebox.showinfo("Reload", "Reload will be wired in a later phase.")

def main():
    app = HillWatchApp()
    app.mainloop()

if __name__ == "__main__":
    main()
