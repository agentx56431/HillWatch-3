from tkinter import ttk
from ..widgets.scroll_frame import ScrollFrame
from ..widgets.bill_card import BillCard

class StatementsTab(ttk.Frame):
    """Placeholder for later watch‑list workflow."""
    def __init__(self, parent, on_select):
        super().__init__(parent)
        sf = ScrollFrame(self)
        sf.pack(fill="both", expand=True)

        sample_titles = [
            "S.100 – Sample WatchList Bill",
            "H.R.222 – Another Placeholder Bill",
        ]
        for title in sample_titles:
            card = BillCard(sf.inner, title, on_select=on_select)
            card.pack(fill="x", padx=4, pady=2)
