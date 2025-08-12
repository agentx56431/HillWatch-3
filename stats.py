# Stats for HillWatch 2 JSON
# Save as: stats.py (run from the HillWatch 2 folder)
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict

DB_PATH = Path("data/bills_119.json")

ORDER = ["S", "HR", "SJRES", "HJRES", "HCONRES", "SCONRES"]

def parse_api_time(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # Handles full ISO (e.g., 2025-08-09T11:03:18Z or without Z)
        if s.endswith("Z"):
            s = s[:-1]
        return datetime.fromisoformat(s)
    except Exception:
        # Try date-only (e.g., 2025-08-09)
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            return None

def is_phase2(cg: dict) -> bool:
    return bool(cg.get("introducedDate")) and bool(cg.get("sponsorFullName"))

def is_phase3(cg: dict) -> bool:
    """
    Consider Phase 3 'done' if:
      - we have a currentCommitteeName (some bills have none, and that's okay), OR
      - committeeLastActionSeen == latestActionDate (means we checked committees for the latest action)
    """
    name = cg.get("currentCommitteeName")
    las = cg.get("latestActionDate")
    seen = cg.get("committeeLastActionSeen")
    return (name is not None) or (las is not None and las == seen)

def safe_get_type(cg: dict) -> str:
    bt = (cg.get("billType") or "").upper()
    # Normalize common variants just in case
    if bt in {"S", "HR", "SJRES", "HJRES", "HCONRES", "SCONRES"}:
        return bt
    return bt or "UNKNOWN"

def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH.resolve()}")
        print("Run: python updater.py --phase list")
        return

    data = json.loads(DB_PATH.read_text(encoding="utf-8"))
    total = len(data)

    phase1_total = 0
    phase2_total = 0
    phase3_total = 0

    by_type_total = defaultdict(int)
    by_type_p1 = defaultdict(int)
    by_type_p2 = defaultdict(int)
    by_type_p3 = defaultdict(int)

    latest_api_dt = None

    for bill_id, entry in data.items():
        cg = entry.get("congressGovData", {})
        if cg:
            phase1_total += 1  # present in DB from list phase
        if is_phase2(cg):
            phase2_total += 1
        if is_phase3(cg):
            phase3_total += 1

        bt = safe_get_type(cg)
        by_type_total[bt] += 1
        if cg:
            by_type_p1[bt] += 1
        if is_phase2(cg):
            by_type_p2[bt] += 1
        if is_phase3(cg):
            by_type_p3[bt] += 1

        upd = parse_api_time(cg.get("updateDateIncludingText"))
        if upd and (latest_api_dt is None or upd > latest_api_dt):
            latest_api_dt = upd

    # File last modified time (local)
    mtime = datetime.fromtimestamp(DB_PATH.stat().st_mtime)
    latest_api_str = latest_api_dt.isoformat(sep=" ", timespec="seconds") if latest_api_dt else "N/A"

    # Header
    print("\n=== HillWatch 2 — Database Stats ===")
    print(f"File: {DB_PATH.resolve()}")
    print(f"Last file save (local): {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Latest API update in DB: {latest_api_str}")

    # Totals
    def pct(x, denom): 
        return f"{(100*x/denom):5.1f}%" if denom else "  0.0%"

    print("\n--- Overall ---")
    print(f"Total bills:          {total}")
    print(f"Past Phase 1 (list):  {phase1_total}   ({pct(phase1_total, total)})")
    print(f"Past Phase 2 (detail):{phase2_total}   ({pct(phase2_total, total)})")
    print(f"Past Phase 3 (comm.): {phase3_total}   ({pct(phase3_total, total)})")

    # Breakdown
    print("\n--- By Bill Type ---")
    header = f"{'Type':8} {'Total':>7}  {'P1':>7}  {'P2':>7}  {'P3':>7}   {'P2%':>6} {'P3%':>6}"
    print(header)
    print("-"*len(header))
    for bt in ORDER + sorted(k for k in by_type_total.keys() if k not in ORDER):
        t = by_type_total.get(bt, 0)
        p1 = by_type_p1.get(bt, 0)
        p2 = by_type_p2.get(bt, 0)
        p3 = by_type_p3.get(bt, 0)
        p2pct = pct(p2, t) if t else "  0.0%"
        p3pct = pct(p3, t) if t else "  0.0%"
        print(f"{bt:8} {t:7}  {p1:7}  {p2:7}  {p3:7}   {p2pct:>6} {p3pct:>6}")

    print("\nDone.\n")

if __name__ == "__main__":
    main()
