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

# --- replace your existing CeiExpertPicker with this ---

class CeiExpertPicker(ttk.Frame):
    """
    Single-select picker with a dropdown of experts + a Clear button.
    Stored format remains a 1-item list (or [] when none).
    """
    def __init__(self, parent, bill_id, get_options, get_current, set_value_callback):
        super().__init__(parent)
        self.bill_id = bill_id
        self.get_options = get_options       # () -> list[str]
        self.get_current = get_current       # () -> list[str] (0 or 1 items)
        self.set_value_callback = set_value_callback  # (bill_id, "Review", "CeiExpert", list[str]) -> bool

        # Current value (text)
        cur_list = self.get_current() or []
        current = cur_list[0] if (isinstance(cur_list, list) and cur_list) else ""
        self.var = tk.StringVar(value=current)

        # Dropdown
        self.combo = ttk.Combobox(self, textvariable=self.var, state="readonly", width=36)
        opts = self.get_options() or []
        # Include a top "(none)" entry to visually indicate no selection. Selecting it won't save;
        # use Clear to actually write [] to the DB.
        display_opts = ["(none)"] + opts
        self.combo["values"] = display_opts

        # Preselect current if present
        try:
            if current and current in opts:
                self.combo.current(display_opts.index(current))
            else:
                self.combo.current(0)  # (none)
        except Exception:
            self.combo.current(0)

        self.combo.pack(side="left")

        # Save on change (except when "(none)" is chosen — use Clear for that)
        self.combo.bind("<<ComboboxSelected>>", self._on_select)

        # Clear button
        ttk.Button(self, text="Clear", command=self._on_clear).pack(side="left", padx=(6, 0))

        # Status
        self.msg = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.msg, foreground="#2e7d32").pack(side="left", padx=(8, 0))

    def _on_select(self, _evt=None):
        val = self.var.get().strip()
        if val == "(none)":
            # Don't write anything when picking "(none)"; user should click Clear to persist [].
            self.msg.set("Not saved (use Clear)")
            self.after(1200, lambda: self.msg.set(""))
            return
        ok = False
        try:
            ok = bool(self.set_value_callback(self.bill_id, "Review", "CeiExpert", [val]))
        except Exception:
            ok = False
        if ok:
            self.msg.set("Saved")
            self.after(1200, lambda: self.msg.set(""))

    def _on_clear(self):
        ok = False
        try:
            ok = bool(self.set_value_callback(self.bill_id, "Review", "CeiExpert", []))
        except Exception:
            ok = False
        if ok:
            # Reset UI to (none)
            try:
                self.combo.current(0)
            except Exception:
                pass
            self.msg.set("Cleared")
            self.after(1200, lambda: self.msg.set(""))
