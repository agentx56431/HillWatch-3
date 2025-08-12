# desktop_gui/collapsible.py
import tkinter as tk
from tkinter import ttk

class Collapsible(ttk.Frame):
    """
    Simple collapsible with a chevron and a body frame you can pack into.
    Use .body to place your content. Works with pack() inside; content persists
    when collapsed/expanded (we only pack/forget the container).
    """
    def __init__(self, parent, title: str, start_open: bool = True):
        super().__init__(parent)
        self._open = tk.BooleanVar(value=start_open)
        self._title = title

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x")

        self._btn_text = tk.StringVar()
        self._sync_btn_text()

        self.toggle_btn = ttk.Checkbutton(
            header,
            textvariable=self._btn_text,
            variable=self._open,
            command=self._toggle,
            style="Toolbutton",
            takefocus=False,
        )
        self.toggle_btn.pack(side="left", anchor="w")

        # Thin separator under header
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(3, 0))

        # Body
        self.body = ttk.Frame(self)
        if start_open:
            self.body.pack(fill="both", expand=True)

    def _sync_btn_text(self):
        self._btn_text.set(("▼  " if self._open.get() else "►  ") + self._title)

    def _toggle(self):
        self._sync_btn_text()
        if self._open.get():
            self.body.pack(fill="both", expand=True)
        else:
            self.body.forget()
