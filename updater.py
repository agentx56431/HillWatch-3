import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from config import (
    BILL_TYPES,
    API_BASE,
    CONGRESS_NUMBER,
    CONGRESS_API_KEY,
)
from bill_utils import (
    build_congress_gov_url,
    load_db,
    save_db,
    compute_content_hash,
    merge_bill_data,
    create_new_bill_entry,
)

# =========================
# Rate Limiter + HTTP
# =========================

class RateLimiter:
    def __init__(self, qps: float):
        self.qps = max(qps, 0.1)
        self.lock = threading.Lock()
        self.next_time = 0.0
    def wait(self):
        with self.lock:
            now = time.perf_counter()
            if now < self.next_time:
                time.sleep(self.next_time - now)
                now = time.perf_counter()
            self.next_time = now + 1.0 / self.qps

session = requests.Session()

def session_get_json(url: str, params: dict | None, limiter: RateLimiter, retries: int = 4, timeout: int = 30):
    if params is None:
        params = {}
    params = dict(params)
    params["format"] = "json"
    params["api_key"] = CONGRESS_API_KEY

    backoff = 1.0
    for attempt in range(1, retries + 1):
        try:
            limiter.wait()
            resp = session.get(url, params=params, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"Transient HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            if attempt == retries:
                raise
            time.sleep(backoff)
            backoff = min(backoff * 2.0, 16.0)
    raise RuntimeError("Exhausted retries")

# =========================
# Parsers (robust to shape)
# =========================

def parse_list_items(payload: dict) -> list[dict]:
    if isinstance(payload, dict):
        bc = payload.get("bills")
        if isinstance(bc, list):
            return bc
        if isinstance(bc, dict):
            return bc.get("bill", []) or []
        return payload.get("bill", []) or []
    if isinstance(payload, list):
        return payload
    return []

def parse_detail(detail_json: dict) -> tuple[str | None, dict]:
    node = detail_json.get("bill", detail_json) if isinstance(detail_json, dict) else {}
    introduced = node.get("introducedDate")

    sponsors = node.get("sponsors")
    if isinstance(sponsors, dict):
        slist = sponsors.get("item", []) or []
    elif isinstance(sponsors, list):
        slist = sponsors
    else:
        slist = []

    sponsor = slist[0] if slist else {}
    return introduced, {
        "sponsorFullName": sponsor.get("fullName"),
        "sponsorParty": sponsor.get("party"),
        "sponsorState": sponsor.get("state"),
        "sponsorDistrict": sponsor.get("district"),
    }

def parse_committees(committees_json: dict, latest_action_text: str | None) -> dict:
    committees = []
    if isinstance(committees_json, dict):
        cnode = committees_json.get("committees", committees_json)
        if isinstance(cnode, dict) and "committee" in cnode:
            committees = cnode.get("committee") or []
        elif isinstance(cnode, list):
            committees = cnode
        else:
            committees = committees_json.get("committee", []) or []
    elif isinstance(committees_json, list):
        committees = committees_json

    current = None
    for c in committees:
        if c.get("currentReferrals") is True:
            current = c
            break
    if not current and committees:
        current = committees[0]

    name = current.get("name") if current else None

    sub_name = None
    if current:
        subnode = current.get("subcommittee")
        if isinstance(subnode, list) and subnode:
            sub_name = subnode[0].get("name")
        elif isinstance(subnode, dict):
            sub_name = subnode.get("name")

    if not sub_name and latest_action_text:
        import re
        m = re.search(r"Subcommittee on ([^.;\n]+)", latest_action_text)
        if m:
            sub_name = f"Subcommittee on {m.group(1).strip()}"

    return {"currentCommitteeName": name, "currentSubcommitteeName": sub_name}

# =========================
# Builders
# =========================

def build_from_list_item(list_item: dict, existing: dict | None) -> dict:
    bill_type = list_item["type"].upper()
    number = list_item["number"]
    latest = list_item.get("latestAction") or {}

    prev = (existing or {}).get("congressGovData", {})
    introduced_prev = prev.get("introducedDate")
    sponsor_prev = {
        "sponsorFullName": prev.get("sponsorFullName"),
        "sponsorParty": prev.get("sponsorParty"),
        "sponsorState": prev.get("sponsorState"),
        "sponsorDistrict": prev.get("sponsorDistrict"),
    }
    committee_prev = {
        "currentCommitteeName": prev.get("currentCommitteeName"),
        "currentSubcommitteeName": prev.get("currentSubcommitteeName"),
    }

    cg = {
        "billId": f"{bill_type}_{number}",
        "congress": CONGRESS_NUMBER,
        "billType": bill_type,
        "billNumber": number,
        "title": list_item.get("title"),
        "originChamber": list_item.get("originChamber"),
        "introducedDate": introduced_prev,
        **sponsor_prev,
        **committee_prev,
        "latestActionText": latest.get("text"),
        "latestActionDate": latest.get("actionDate"),
        "updateDate": list_item.get("updateDate"),
        "updateDateIncludingText": list_item.get("updateDateIncludingText"),
        "sourceUrl": list_item.get("url") or f"{API_BASE}/bill/{CONGRESS_NUMBER}/{bill_type.lower()}/{number}",
        "congressGovUrl": build_congress_gov_url(CONGRESS_NUMBER, bill_type.lower(), number),
    }
    cg["contentHash"] = compute_content_hash(cg)
    return cg

def apply_detail(existing: dict, introduced_date: str | None, sponsor_info: dict) -> dict:
    cg = dict(existing["congressGovData"])
    cg["introducedDate"] = introduced_date
    cg.update(sponsor_info)
    cg["contentHash"] = compute_content_hash(cg)
    return cg

def apply_committees(existing: dict, committee_data: dict) -> dict:
    cg = dict(existing["congressGovData"])
    cg.update(committee_data)
    cg["contentHash"] = compute_content_hash(cg)
    cg["committeeLastActionSeen"] = cg.get("latestActionDate")
    return cg

# =========================
# Utils for progress
# =========================

def _fmt_hhmmss(seconds: float) -> str:
    if seconds == float("inf"):
        return "--:--:--"
    seconds = int(max(0, seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# =========================
# Phase 1 — LIST
# =========================

def run_phase_list(db: dict, types: list[str], qps: float):
    limiter = RateLimiter(qps)
    total_new, total_updated, checked = 0, 0, 0

    for bt in types:
        print(f"\n[List] {bt.upper()} …")
        offset = 0
        per_page = 250
        while True:
            url = f"{API_BASE}/bill/{CONGRESS_NUMBER}/{bt}"
            payload = session_get_json(url, {"limit": per_page, "offset": offset}, limiter)
            items = parse_list_items(payload)
            if not items:
                break

            for item in items:
                checked += 1
                bill_id = f"{item['type'].upper()}_{item['number']}"
                cg = build_from_list_item(item, db.get(bill_id))

                if bill_id in db:
                    db[bill_id] = merge_bill_data(db[bill_id], cg)
                    total_updated += 1
                else:
                    db[bill_id] = create_new_bill_entry(cg)
                    total_new += 1

            offset += per_page
            time.sleep(0.2)

    save_db(db)
    print(f"\n[List] Done. Checked: {checked} | New: {total_new} | Updated: {total_updated} | Total in DB: {len(db)}")

# =========================
# Phase 2 — DETAIL (sponsor + introduced)
# =========================

def _needs_detail(entry: dict) -> bool:
    cg = entry["congressGovData"]
    return cg.get("introducedDate") is None or cg.get("sponsorFullName") is None

def run_phase_detail(db: dict, types: list[str], limit: int | None, workers: int, qps: float):
    limiter = RateLimiter(qps)
    to_process = []
    for bill_id, entry in db.items():
        tprefix = bill_id.split("_", 1)[0].lower()
        if tprefix in types and _needs_detail(entry):
            to_process.append(bill_id)
    if limit:
        to_process = to_process[:limit]

    total = len(to_process)
    print(f"\n[Detail] Bills to enrich: {total} (workers={workers}, qps={qps})")
    if not to_process:
        print("[Detail] Nothing to do.")
        return

    start = time.time()
    done = 0

    def task(bill_id: str):
        tprefix, number = bill_id.split("_", 1)
        url = f"{API_BASE}/bill/{CONGRESS_NUMBER}/{tprefix.lower()}/{number}"
        detail_json = session_get_json(url, None, limiter)
        introduced, sponsor = parse_detail(detail_json)
        cg = apply_detail(db[bill_id], introduced, sponsor)
        db[bill_id] = merge_bill_data(db[bill_id], cg)
        return bill_id

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(task, bid) for bid in to_process]
        for fut in as_completed(futures):
            _ = fut.result()
            done += 1
            if done % 25 == 0 or done == total:
                elapsed = max(time.time() - start, 1e-6)
                rate = done / elapsed
                remaining = total - done
                eta = remaining / rate if rate > 0 else float("inf")
                print(f"[Detail] {done}/{total} | {rate:.2f} bills/s | elapsed {_fmt_hhmmss(elapsed)} | ETA {_fmt_hhmmss(eta)}")

    save_db(db)
    print(f"[Detail] Completed {done} updates.")

# =========================
# Phase 3 — COMMITTEES
# =========================

def _needs_committees(entry: dict) -> bool:
    cg = entry["congressGovData"]
    las = cg.get("latestActionDate")
    seen = cg.get("committeeLastActionSeen")
    return cg.get("currentCommitteeName") is None or (las and las != seen)

def run_phase_committees(db: dict, types: list[str], limit: int | None, workers: int, qps: float):
    limiter = RateLimiter(qps)
    to_process = []
    for bill_id, entry in db.items():
        tprefix = bill_id.split("_", 1)[0].lower()
        if tprefix in types and _needs_committees(entry):
            to_process.append(bill_id)
    if limit:
        to_process = to_process[:limit]

    total = len(to_process)
    print(f"\n[Committees] Bills to enrich: {total} (workers={workers}, qps={qps})")
    if not to_process:
        print("[Committees] Nothing to do.")
        return

    start = time.time()
    done = 0

    def task(bill_id: str):
        tprefix, number = bill_id.split("_", 1)
        latest_text = db[bill_id]["congressGovData"].get("latestActionText")
        url = f"{API_BASE}/bill/{CONGRESS_NUMBER}/{tprefix.lower()}/{number}/committees"
        committees_json = session_get_json(url, None, limiter)
        committee_data = parse_committees(committees_json, latest_text)
        cg = apply_committees(db[bill_id], committee_data)
        db[bill_id] = merge_bill_data(db[bill_id], cg)
        return bill_id

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(task, bid) for bid in to_process]
        for fut in as_completed(futures):
            _ = fut.result()
            done += 1
            if done % 25 == 0 or done == total:
                elapsed = max(time.time() - start, 1e-6)
                rate = done / elapsed
                remaining = total - done
                eta = remaining / rate if rate > 0 else float("inf")
                print(f"[Committees] {done}/{total} | {rate:.2f} bills/s | elapsed {_fmt_hhmmss(elapsed)} | ETA {_fmt_hhmmss(eta)}")

    save_db(db)
    print(f"[Committees] Completed {done} updates.")

# =========================
# CLI
# =========================

def main():
    parser = argparse.ArgumentParser(description="HillWatch 2 — phased Congress.gov updater")
    parser.add_argument("--phase", choices=["list", "detail", "committees"], required=True,
                        help="Which phase to run: list | detail | committees")
    parser.add_argument("--types", default=None,
                        help="Comma-separated bill types (default: all 6). e.g. 's,hr,hjres'")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of bills to process (detail/committees). Ignored for list.")
    parser.add_argument("--workers", type=int, default=6,
                        help="Parallel workers for detail/committees (default 6)")
    parser.add_argument("--qps", type=float, default=2.0,
                        help="Max requests per second across all threads (default 2.0)")
    args = parser.parse_args()

    types = [t.strip().lower() for t in (args.types.split(",") if args.types else BILL_TYPES)]

    db = load_db()

    if args.phase == "list":
        print("=== HillWatch 2 — Phase: LIST ===")
        run_phase_list(db, types, qps=args.qps)
        print("Phase LIST complete.\nNext: run --phase detail, then --phase committees.")
        return

    if not db:
        print("Database is empty. Run: python updater.py --phase list")
        return

    if args.phase == "detail":
        print("=== HillWatch 2 — Phase: DETAIL (sponsor + introducedDate) ===")
        run_phase_detail(db, types, limit=args.limit, workers=args.workers, qps=args.qps)
        print("Phase DETAIL complete.")
        return

    if args.phase == "committees":
        print("=== HillWatch 2 — Phase: COMMITTEES ===")
        run_phase_committees(db, types, limit=args.limit, workers=args.workers, qps=args.qps)
        print("Phase COMMITTEES complete.")
        return

if __name__ == "__main__":
    main()
