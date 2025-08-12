# Raw API probe for Congress.gov — prints and saves raw JSON
# Requires: requests, python-dotenv, .env with CONGRESS_API_KEY
from pathlib import Path
import os, json, requests
from dotenv import load_dotenv

# === EDIT THESE TO TARGET A SPECIFIC BILL ===
CONGRESS = 119
BILL_TYPE = "s"       # e.g., "s", "hr", "hjres", "sjres", "hconres", "sconres"
BILL_NUMBER = "2682"  # e.g., "2682"

API_BASE = "https://api.congress.gov/v3"

def get_json(url, params=None):
    if params is None:
        params = {}
    params["format"] = "json"
    params["api_key"] = API_KEY
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        print("Response was not valid JSON. Raw text follows:")
        print(r.text)
        raise

def dump_json(obj, label, outdir):
    print(f"\n=== {label} ===")
    print(json.dumps(obj, indent=2))
    out = outdir / f"{label.lower().replace(' ', '_')}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def main():
    # Setup paths & API key
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data" / "debug"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Load API key from .env
    load_dotenv()
    global API_KEY
    API_KEY = os.getenv("CONGRESS_API_KEY")
    if not API_KEY:
        raise SystemExit("Missing CONGRESS_API_KEY in .env")

    # 1) Sample LIST endpoint for the selected bill type (first few only)
    list_url = f"{API_BASE}/bill/{CONGRESS}/{BILL_TYPE}"
    list_json = get_json(list_url, {"limit": 5, "offset": 0})
    dump_json(list_json, f"LIST_{CONGRESS}_{BILL_TYPE}_PAGE0", data_dir)

    # 2) DETAIL endpoint for the specific bill
    detail_url = f"{API_BASE}/bill/{CONGRESS}/{BILL_TYPE}/{BILL_NUMBER}"
    detail_json = get_json(detail_url)
    dump_json(detail_json, f"DETAIL_{CONGRESS}_{BILL_TYPE}_{BILL_NUMBER}", data_dir)

    # 3) COMMITTEES subresource for that bill
    comm_url = f"{API_BASE}/bill/{CONGRESS}/{BILL_TYPE}/{BILL_NUMBER}/committees"
    committees_json = get_json(comm_url)
    dump_json(committees_json, f"COMMITTEES_{CONGRESS}_{BILL_TYPE}_{BILL_NUMBER}", data_dir)

    print(f"\nSaved raw JSON to: {data_dir}")

if __name__ == "__main__":
    main()
