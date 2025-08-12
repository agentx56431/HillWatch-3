# desktop_gui/data_access.py
# Minimal helpers to load/save the local JSON DB safely.

import json
import os
from pathlib import Path

# Try to read DB_PATH from config.py; fall back to data/bills_119.json
try:
    from config import DB_PATH  # expected to point to data/bills_119.json
except Exception:
    DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bills_119.json"

DB_PATH = Path(DB_PATH)

def load_db() -> dict:
    """
    Load the JSON database from DB_PATH.
    Returns a dict keyed by billId.
    Raises FileNotFoundError if missing.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at: {DB_PATH}")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db_atomic(db: dict) -> None:
    """
    Atomically write the database to DB_PATH:
    write to a temp file, then replace.
    """
    tmp = DB_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
    os.replace(tmp, DB_PATH)

def ensure_custom_paths(rec: dict) -> None:
    """Ensure customData.Review exists with expected keys."""
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

def set_watchlist_and_save(db: dict, bill_id: str, value: bool) -> None:
    """Set customData.Review.WatchList and atomically save."""
    rec = db.get(bill_id)
    if not rec:
        raise KeyError(f"Bill not found: {bill_id}")
    ensure_custom_paths(rec)
    rec["customData"]["Review"]["WatchList"] = bool(value)
    save_db_atomic(db)
