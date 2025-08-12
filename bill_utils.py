import requests
import json
import hashlib
import os
import copy
from pathlib import Path
from config import (
    CONGRESS_API_KEY, API_BASE, SLUG_MAP, DB_PATH, CEI_EXPERT_OPTIONS
)


# =============================
# API CALL HELPERS
# =============================

def get_json(url, params=None):
    """Make a GET request to Congress.gov API and return JSON."""
    if not params:
        params = {}
    params["api_key"] = CONGRESS_API_KEY
    params["format"] = "json"

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# =============================
# URL HELPERS
# =============================

def build_congress_gov_url(congress, bill_type, bill_number):
    """Return a working Congress.gov URL for the bill."""
    slug = SLUG_MAP[bill_type.lower()]
    return f"https://www.congress.gov/bill/{congress}th-congress/{slug}/{bill_number}"

# =============================
# FILE HELPERS
# =============================

def load_db():
    """Load the JSON database or return an empty dict."""
    if DB_PATH.exists():
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    """Save the JSON database atomically."""
    temp_file = DB_PATH.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
    os.replace(temp_file, DB_PATH)

# =============================
# CUSTOM DATA SCHEMA
# =============================

# Your new three-section schema with defaults
DEFAULT_CUSTOMDATA = {
    "Review": {
        "WatchList": False,
        "CeiExpert": [],
        "CeiExpertOptions": CEI_EXPERT_OPTIONS,  # <-- added
        "StatementRequested": False,
        "StatementRequestedDate": None,
        "CEIExpertAcceptOrReject": False,
        "Review_Done": False
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
        "Outreach_Done": False
    },
    "FinalTracking": {
        "Press_Release_Mention": False,
        "Press Release Mention_Source": "",
        "Any_Public_Mention": False,
        "Any_Public_Mention_Source": "",
        "Notes_or_Other": "",
        "Public_Mention_Date": None,
        "Final_Tracking_Done": False
    }
}

LEGACY_TOPLEVEL_KEYS = ["watchlist", "ceiExpertNotes", "priorityLevel"]

def ensure_customdata_schema(custom_data: dict | None) -> dict:
    """
    Bring any existing customData up to the new three-section schema,
    and remove legacy top-level fields.
    """
    if not isinstance(custom_data, dict):
        custom_data = {}

    # Remove old top-level keys if present
    for k in LEGACY_TOPLEVEL_KEYS:
        if k in custom_data:
            del custom_data[k]

    # Merge defaults without overwriting existing values
    for section, defaults in DEFAULT_CUSTOMDATA.items():
        if section not in custom_data or not isinstance(custom_data[section], dict):
            custom_data[section] = {}
        sec = custom_data[section]
        for key, default_value in defaults.items():
            if key not in sec:
                sec[key] = default_value

    # keep the selectable options in sync with the master list
    custom_data["Review"]["CeiExpertOptions"] = CEI_EXPERT_OPTIONS

    return custom_data

# =============================
# MERGE & HASH HELPERS
# =============================

def compute_content_hash(data_fields):
    """Compute SHA-256 hash from key Congress.gov data fields."""
    payload = "|".join(str(data_fields.get(k, "")) for k in sorted(data_fields.keys()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def merge_bill_data(existing_bill, new_congress_data):
    normalized_custom = ensure_customdata_schema(existing_bill.get("customData"))
    return {
        "congressGovData": new_congress_data,
        "customData": normalized_custom
    }


def create_new_bill_entry(new_congress_data):
    return {
        "congressGovData": new_congress_data,
        "customData": copy.deepcopy(DEFAULT_CUSTOMDATA)  # three-section schema
    }

