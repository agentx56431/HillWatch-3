# desktop_gui/filters.py
# Search/filter helpers for HillWatch v3

from typing import Dict, Tuple, List

def _cg_text(rec: dict) -> str:
    """
    Build a searchable text blob from congressGovData fields.
    Only congressGovData is searched (not customData).
    """
    cg = rec.get("congressGovData", {}) or {}
    parts = [
        str(cg.get("billType", "")),
        str(cg.get("billNumber", "")),
        str(cg.get("title", "")),
        str(cg.get("originChamber", "")),
        str(cg.get("latestActionText", "")),
        str(cg.get("sponsorFullName", "")),
        str(cg.get("sponsorParty", "")),
        str(cg.get("sponsorState", "")),
        str(cg.get("currentCommitteeName", "")),
        str(cg.get("currentSubcommitteeName", "")),
        str(cg.get("introducedDate", "")),
        str(cg.get("latestActionDate", "")),
    ]
    # Lowercase + single string for fast substring checks
    return " ".join(parts).lower()

def _matches(query: str, blob: str) -> bool:
    """
    AND match on tokens: every token in the query must be present in the blob.
    """
    q = (query or "").strip().lower()
    if not q:
        return True
    tokens = [t for t in q.split() if t]
    return all(t in blob for t in tokens)

def search_items(db: Dict[str, dict], query: str) -> List[Tuple[str, dict]]:
    """
    Return a list of (bill_id, record) that match the query across congressGovData.
    """
    if not query or not query.strip():
        return list(db.items())
    out = []
    for bid, rec in db.items():
        blob = _cg_text(rec)
        if _matches(query, blob):
            out.append((bid, rec))
    return out
