# desktop_gui/editor_fields.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DATE_FMT = "%Y-%m-%d"

def is_valid_date(text: str) -> bool:
    if text is None:
        return True
    s = str(text).strip()
    if s == "":
        return True  # blank = null
    try:
        datetime.strptime(s, DATE_FMT)
        return True
    except Exception:
        return False

class BoolCheck(ttk.Checkbutton):
    """
    Checkbox that autosaves on toggle.
    """
    def __init__(self, parent, bill_id: str, group: str, key: str, get_value, set_value_callback, label: str):
        self.var = tk.BooleanVar(value=bool(get_value()))
        super().__init__(parent, text=label, variable=self.var, command=self._on_change)
        self.bill_id = bill_id
        self.group = group
        self.key = key
        self.set_value_callback = set_value_callback

    def _on_change(self):
        new_val = bool(self.var.get())
        ok = self.set_value_callback(self.bill_id, self.group, self.key, new_val)
        if not ok:
            # revert
            self.var.set(not new_val)

class TextEntry(ttk.Frame):
    """
    Single-line text that autosaves on focus-out (and Enter).
    """
    def __init__(self, parent, bill_id: str, group: str, key: str, get_value, set_value_callback, width=36):
        super().__init__(parent)
        self.bill_id = bill_id
        self.group = group
        self.key = key
        self.set_value_callback = set_value_callback

        self.var = tk.StringVar(value=str(get_value() or ""))
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(fill="x", expand=True)
        self.entry.bind("<FocusOut>", self._save)
        self.entry.bind("<Return>", self._save)

    def _save(self, _event=None):
        new_val = self.var.get()
        ok = self.set_value_callback(self.bill_id, self.group, self.key, new_val)
        if not ok:
            # we could show an error; for now just leave it as is
            pass

class DateEntryValidated(ttk.Frame):
    """
    Date entry that enforces YYYY-MM-DD on blur; blank => null.
    Shows inline error and keeps focus until valid.
    """
    def __init__(self, parent, bill_id: str, group: str, key: str, get_value, set_value_callback, width=16):
        super().__init__(parent)
        self.bill_id = bill_id
        self.group = group
        self.key = key
        self.set_value_callback = set_value_callback

        self.err_var = tk.StringVar(value="")
        self.var = tk.StringVar(value=str(get_value() or ""))

        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(side="left")
        self.entry.bind("<FocusOut>", self._on_blur)
        self.entry.bind("<Return>", self._on_blur)

        self.err_lbl = ttk.Label(self, textvariable=self.err_var, foreground="#b00020")
        self.err_lbl.pack(side="left", padx=(8, 0))

    def _on_blur(self, _event=None):
        s = self.var.get().strip()
        if s == "":
            # blank => null
            self.err_var.set("")
            ok = self.set_value_callback(self.bill_id, self.group, self.key, None)
            if not ok:
                self.err_var.set("Save failed")
            return

        if not is_valid_date(s):
            self.err_var.set("Invalid date (YYYY-MM-DD)")
            self.entry.focus_set()
            self.entry.selection_range(0, "end")
            return

        self.err_var.set("")
        ok = self.set_value_callback(self.bill_id, self.group, self.key, s)
        if not ok:
            self.err_var.set("Save failed")
            self.entry.focus_set()
            self.entry.selection_range(0, "end")

class CeiExpertPicker(ttk.Frame):
    """
    Single-select picker for CeiExpert from CeiExpertOptions.
    Stores as a one-item list, or [] for none.
    """
    def __init__(self, parent, bill_id: str, get_options, get_current, set_value_callback):
        super().__init__(parent)
        self.bill_id = bill_id
        self.get_options = get_options
        self.get_current = get_current
        self.set_value_callback = set_value_callback

        self.var = tk.StringVar(value=self._current_name())

        self.btn = ttk.Button(self, text="Select CEI Expert…", command=self._open_popup)
        self.btn.pack(side="left")

        self.sel_lbl = ttk.Label(self, textvariable=self.var)
        self.sel_lbl.pack(side="left", padx=(8, 6))

        self.clear_btn = ttk.Button(self, text="Clear", command=self._clear)
        self.clear_btn.pack(side="left")

    def _current_name(self) -> str:
        cur = self.get_current() or []
        return cur[0] if cur else "(none)"

    def _clear(self):
        ok = self.set_value_callback(self.bill_id, "Review", "CeiExpert", [])
        if ok:
            self.var.set("(none)")

    def _open_popup(self):
        opts = self.get_options() or []
        # Prepend a virtual "(none)" entry
        opts_display = ["(none)"] + list(opts)

        top = tk.Toplevel(self)
        top.title("Select CEI Expert")
        top.resizable(False, False)
        top.transient(self.winfo_toplevel())
        top.grab_set()

        lb = tk.Listbox(top, selectmode="browse", width=42, height=min(10, max(4, len(opts_display))))
        for o in opts_display:
            lb.insert("end", o)
        lb.pack(padx=12, pady=12)

        def on_choose(_e=None):
            idx = lb.curselection()
            if not idx:
                top.destroy()
                return
            val = lb.get(idx[0])
            if val == "(none)":
                ok = self.set_value_callback(self.bill_id, "Review", "CeiExpert", [])
                if ok:
                    self.var.set("(none)")
            else:
                ok = self.set_value_callback(self.bill_id, "Review", "CeiExpert", [val])
                if ok:
                    self.var.set(val)
            top.destroy()

        lb.bind("<Double-Button-1>", on_choose)
        ttk.Button(top, text="Choose", command=on_choose).pack(pady=(0, 12))
        top.bind("<Escape>", lambda e: top.destroy())
        self.after(10, lambda: top.geometry(f"+{self.winfo_rootx()+80}+{self.winfo_rooty()+40}"))
