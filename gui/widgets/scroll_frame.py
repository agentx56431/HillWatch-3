import tkinter as tk
from tkinter import ttk

class ScrollFrame(ttk.Frame):
    """A frame with a vertical scrollbar; child widgets go in self.inner."""
    def __init__(self, parent):
        super().__init__(parent)
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        vbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = ttk.Frame(canvas)

        inner_id = canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        def _on_inner(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas(event):
            canvas.itemconfig(inner_id, width=event.width)

        self.inner.bind("<Configure>", _on_inner)
        canvas.bind("<Configure>", _on_canvas)
