# desktop_gui/collapsible.py
import tkinter as tk
from tkinter import ttk

class Collapsible(ttk.Frame):
    def __init__(self, parent, title: str, start_open: bool = True):
        super().__init__(parent)
        self._open = tk.BooleanVar(value=start_open)

        # Header row
        header = ttk.Frame(self)
        header.pack(fill="x")
        self.toggle_btn = ttk.Checkbutton(
            header,
            text=title,
            variable=self._open,
            command=self._toggle,
            style="Toolbutton",
        )
        self.toggle_btn.pack(side="left", anchor="w")

        # Body container (caller will pack content inside)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

    def _toggle(self):
        if self._open.get():
            self.body.pack(fill="both", expand=True)
        else:
            self.body.forget()
