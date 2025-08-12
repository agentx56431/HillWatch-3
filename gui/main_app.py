import tkinter as tk
from tkinter import ttk
from tabs.main_feed import MainFeedTab
from tabs.statements import StatementsTab

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HillWatch GUI")

        # Split window: left = tabs, right = details
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # ----- Left side: Notebook with two tabs -----
        notebook = ttk.Notebook(paned)
        paned.add(notebook, weight=1)  # weight gives it more space

        main_tab = MainFeedTab(notebook, on_select=self.show_details)
        stmt_tab = StatementsTab(notebook, on_select=self.show_details)
        notebook.add(main_tab, text="Main Bill Feed")
        notebook.add(stmt_tab, text="Legislative Statements")

        # ----- Right side: detail viewer -----
        self.detail_frame = ttk.Frame(paned, padding=10)
        self.detail_label = ttk.Label(self.detail_frame, text="Select a bill to view details")
        self.detail_label.pack()
        paned.add(self.detail_frame, weight=2)  # bigger area

    def show_details(self, title):
        self.detail_label.config(text=f"Details for:\n{title}")

if __name__ == "__main__":
    app = MainApp()
    app.geometry("900x500")   # optional window size
    app.mainloop()
