import tkinter as tk

class BillCard(tk.Frame):
    """Simple placeholder card; later you’ll add buttons, etc."""
    def __init__(self, parent, title, on_select=None):
        super().__init__(parent, bd=1, relief="solid", padx=8, pady=4)
        self.title = title
        lbl = tk.Label(self, text=title, anchor="w")
        lbl.pack(fill="x")
        # Entire card clickable
        if on_select:
            self.bind("<Button-1>", lambda e: on_select(title))
            lbl.bind("<Button-1>", lambda e: on_select(title))
