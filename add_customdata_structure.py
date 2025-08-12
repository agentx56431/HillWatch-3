# file: add_customdata_structure.py
import json
from pathlib import Path
from datetime import date

DATA_FILE = Path("data/bills_119.json")

# Default structure for new customData fields
DEFAULT_CUSTOMDATA = {
    "Review": {
        "WatchList": False,
        "CeiExpert": [],
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

def merge_customdata(existing):
    """Merge existing customData with the new default schema."""
    if not isinstance(existing, dict):
        existing = {}
    for section, defaults in DEFAULT_CUSTOMDATA.items():
        if section not in existing or not isinstance(existing[section], dict):
            existing[section] = {}
        for key, default_value in defaults.items():
            if key not in existing[section]:
                existing[section][key] = default_value
    return existing

def main():
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found.")
        return
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        bills = json.load(f)

    updated_count = 0
    for bill_id, bill_data in bills.items():
        bill_data["customData"] = merge_customdata(bill_data.get("customData", {}))
        updated_count += 1

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(bills, f, indent=2)

    print(f"Updated {updated_count} bills with new customData structure.")

if __name__ == "__main__":
    main()
