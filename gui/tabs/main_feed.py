from tkinter import ttk
from gui.widgets.scroll_frame import ScrollFrame
from gui.widgets.bill_card import BillCard


class MainFeedTab(ttk.Frame):
    """Shows all bills in a scrollable list."""
    def __init__(self, parent, on_select):
        super().__init__(parent)
        sf = ScrollFrame(self)
        sf.pack(fill="both", expand=True)

        # Demo data; replace with real bill list later
        sample_titles = [
            "S.1748 – Kids Online Safety Act",
            "H.R.5678 – Example House Bill",
            "S.99 – Another Senate Bill",
        ]
        for title in sample_titles:
            card = BillCard(sf.inner, title, on_select=on_select)
            card.pack(fill="x", padx=4, pady=2)
