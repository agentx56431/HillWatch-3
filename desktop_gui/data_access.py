# desktop_gui/data_access.py
# I/O helpers for the HillWatch JSON DB + safe setters for custom data.

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

# ---- Resolve DB path from config.py (fallback to data/bills_119.json) ----
try:
    # config.py lives at project root
    from config import DB_PATH as CONFIG_DB_PATH  # type: ignore
    DB_PATH: str = CONFIG_DB_PATH
except Exception:
    DB_PATH = str(Path(__file__).resolve().parents[1] / "data" / "bills_119.json")


# ---- Load / Save (with Windows-friendly atomic write + retries) ----

def load_db() -> Dict[str, Any]:
    """
    Load the JSON DB and return as a dict.
    If the file doesn't exist yet, returns empty dict.
    """
    p = Path(DB_PATH)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_db_atomic(db: Dict[str, Any], retries: int = 6, backoff: float = 0.15) -> None:
    """
    Atomically write the DB with retries to handle transient Windows locks
    (e.g., Access is denied / WinError 5). Writes to a temp file then os.replace().
    """
    db_path = Path(DB_PATH)
    tmp_path = db_path.with_suffix(".tmp")

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            # Write to a temp file
            with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            # Atomic replace
            os.replace(tmp_path, db_path)
            return
        except PermissionError as e:
            # File is locked (common on Windows). Back off and retry.
            last_err = e
            time.sleep(backoff * attempt)
        except OSError as e:
            # Other transient OS errors: also back off and retry a bit.
            last_err = e
            time.sleep(backoff * attempt)
        finally:
            # If replace failed, try to remove leftover temp
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    # Exhausted retries
    if last_err:
        raise last_err
    raise RuntimeError("Failed to save DB for unknown reason")


# ---- Minimal helpers used by the UI ----

def ensure_custom_paths(rec: Dict[str, Any]) -> None:
    """
    Ensure customData.Review exists (legacy helper for watchlist toggle).
    """
    if "customData" not in rec or not isinstance(rec["customData"], dict):
        rec["customData"] = {}
    cd = rec["customData"]
    if "Review" not in cd or not isinstance(cd["Review"], dict):
        cd["Review"] = {
            "WatchList": False,
            "CeiExpert": [],
            "StatementRequested": False,
            "StatementRequestedDate": None,
            "CEIExpertAcceptOrReject": False,
            "Review_Done": False,
            "CeiExpertOptions": []
        }


def set_watchlist_and_save(db: Dict[str, Any], bill_id: str, value: bool) -> None:
    """
    Set customData.Review.WatchList and save.
    """
    rec = db.get(bill_id)
    if not rec:
        raise KeyError(f"Bill not found: {bill_id}")
    ensure_custom_paths(rec)
    rec["customData"]["Review"]["WatchList"] = bool(value)
    save_db_atomic(db)


# ---- Full custom structure + generic setter used by the Custom editor ----

CUSTOM_DEFAULT: Dict[str, Dict[str, Any]] = {
    "Review": {
        "WatchList": False,
        "CeiExpert": [],                 # single-select stored as a 1-item list
        "StatementRequested": False,
        "StatementRequestedDate": None,  # YYYY-MM-DD or None
        "CEIExpertAcceptOrReject": False,
        "Review_Done": False,
        "CeiExpertOptions": [],          # populated elsewhere
    },
    "Outreach": {
        "Worked_Directly_with_Office": False,
        "Statement_Complete": False,
        "Statement_Complete_Date": None,
        "Statement_Emailed_Directly": False,
        "Statement_Emailed_Quorum": False,
        "InternalLed_Coalition_Letter": False,
        "ExternalLed_Coalition_Letter": False,
        "Support_Posted_Website": False,
        "Other_Support": "",
        "Outreach_Done": False,
    },
    "FinalTracking": {
        "Press_Release_Mention": False,
        "Press Release Mention_Source": "",
        "Any_Public_Mention": False,
        "Any_Public_Mention_Source": "",
        "Notes_or_Other": "",
        "Public_Mention_Date": None,
        "Final_Tracking_Done": False,
    },
}


def ensure_custom_full(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make sure customData exists and has all expected keys (non-destructive merge).
    Returns the customData dict.
    """
    if "customData" not in rec or not isinstance(rec["customData"], dict):
        rec["customData"] = {}
    cd = rec["customData"]

    for group, defaults in CUSTOM_DEFAULT.items():
        if group not in cd or not isinstance(cd[group], dict):
            cd[group] = {}
        for k, v in defaults.items():
            cd[group].setdefault(k, v)

    return cd


def set_custom_field_and_save(db: Dict[str, Any], bill_id: str, group: str, key: str, value: Any) -> None:
    """
    Generic setter used by the right-pane editor:
      set customData[group][key] = value
    then atomically save.
    """
    rec = db.get(bill_id)
    if not rec:
        raise KeyError(f"Bill not found: {bill_id}")

    cd = ensure_custom_full(rec)
    if group not in cd or not isinstance(cd[group], dict):
        cd[group] = {}

    cd[group][key] = value
    # DEBUG (optional): uncomment if you need to see writes in the terminal
    # print(f"[SAVE] {bill_id}: customData[{group}][{key}] = {value!r}")
    save_db_atomic(db)
