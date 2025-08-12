# HillWatch 2 — Local Legislation Store

HillWatch 2 is a local Python toolchain for storing, monitoring, and categorizing U.S. legislation data from Congress.gov. It keeps a JSON database you can update **incrementally** and enrich in **phases**. Your own fields (watchlists, notes, etc.) live in a separate section and are **never overwritten** by API refreshes.

---

## Folder contents (what each file does)

* `config.py` — Central settings (paths, bill types, API base). Loads `CONGRESS_API_KEY` from `.env`.
* `bill_utils.py` — Helpers for:

  * Loading/saving the JSON DB *atomically*
  * Building Congress.gov URLs
  * Preserving your `customData` on updates
  * Computing a content hash for change detection
* `updater.py` — **Main engine**, runs in **three phases**:

  1. **list** → general bill info (title, latest action, etc.)
  2. **detail** → *introduced date* + *sponsor*
  3. **committees** → current committee/subcommittee (if any)
* `stats.py` — Prints progress stats (totals & by bill type) and last-updated info.
* `raw_api_probe.py` — Quick debugging probe to print/save raw JSON from Congress.gov for a specific bill.
* `data/` — Local database & debug outputs:

  * `data/bills_119.json` — the main JSON database (created on first run)
  * `data/debug/` — optional raw responses if you use the probe script
* `.env` — your API key (example):

  ```
  CONGRESS_API_KEY=YOUR_KEY_HERE
  ```
* `.venv/` — your Python virtual environment (local, no admin rights needed)
* `__pycache__/` — Python bytecode cache (auto-generated; safe to delete)

---

## Prerequisites

* Python 3.10+ recommended
* No admin rights needed

Activate the venv (Git Bash on Windows):

```bash
cd "C:/Users/francisco.ferrisi/Desktop/FF - GA Local Files/Coding/HillWatch 2"
source .venv/Scripts/activate
```

---

## Quickstart

1. **Add your API key** to `.env`:

```
CONGRESS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxx
```

2. **Phase 1 — build the index (fast):**

```bash
python updater.py --phase list --qps 1.2
```

3. **Phase 2 — enrich sponsor + introduced date:**

* Small test:

```bash
python updater.py --phase detail --types s --limit 200 --workers 6 --qps 1.2
```

* Full pass:

```bash
python updater.py --phase detail --workers 6 --qps 1.2
```

4. **Phase 3 — enrich committees:**

* Small test:

```bash
python updater.py --phase committees --types s --limit 200 --workers 6 --qps 1.2
```

* Full pass:

```bash
python updater.py --phase committees --workers 6 --qps 1.2
```

5. **Check status:**

```bash
python stats.py
```

---

## How the JSON is structured

Each bill is keyed like `S_2682` and has two sections:

```json
{
  "S_2682": {
    "congressGovData": {
      "billId": "S_2682",
      "congress": 119,
      "billType": "S",
      "billNumber": "2682",
      "title": "...",
      "originChamber": "Senate",
      "introducedDate": "2025-08-02",
      "sponsorFullName": "Sen. Example [D-XY]",
      "sponsorParty": "D",
      "sponsorState": "XY",
      "sponsorDistrict": null,
      "currentCommitteeName": "Judiciary Committee",
      "currentSubcommitteeName": null,
      "latestActionText": "...",
      "latestActionDate": "2025-08-08",
      "updateDate": "2025-08-09",
      "updateDateIncludingText": "2025-08-09",
      "sourceUrl": "https://api.congress.gov/v3/bill/119/s/2682?format=json",
      "congressGovUrl": "https://www.congress.gov/bill/119th-congress/senate-bill/2682",
      "contentHash": "…",
      "committeeLastActionSeen": "2025-08-08"   // set after committees phase
    },
    "customData": {
      "watchlist": false,
      "ceiExpertNotes": "",
      "priorityLevel": null
    }
  }
}
```

* **`congressGovData`** is updated by scripts (don’t edit by hand).
* **`customData`** is yours—edit freely; updates won’t overwrite it.

---

## Phases (what they do)

### Phase: list

* Pulls general info for all tracked bill types (HR, S, HJRES, SJRES, HCONRES, SCONRES).
* Initializes new bills and refreshes index fields (title, latest action, etc.).
* Keeps previously enriched fields as-is.

### Phase: detail

* For bills missing **introducedDate** or **sponsor**, fetches the bill detail endpoint.
* Runs **in parallel** with `--workers`; respects global rate limit `--qps`.

### Phase: committees

* For bills missing committee or where `latestActionDate` changed since last check, fetches committees and selects the **current** committee/subcommittee (when available).
* Runs **in parallel** with `--workers` and `--qps`.

**CLI reference:**

```bash
python updater.py --phase {list|detail|committees} \
                  [--types s,hr,hjres,sjres,hconres,sconres] \
                  [--limit N] \
                  [--workers 6] \
                  [--qps 1.2]
```

---

## Stats & debugging

**Stats**

```bash
python stats.py
```

Prints:

* Total bills
* Past Phase 1 (listed)
* Past Phase 2 (detail filled)
* Past Phase 3 (committees processed or verified)
* Breakdown by bill type
* File last-saved time and the latest API update timestamp in the DB

**Raw API probe (if something looks off)**

```bash
python raw_api_probe.py
```

Edit the top to choose a bill:

```python
CONGRESS = 119
BILL_TYPE = "s"
BILL_NUMBER = "2682"
```

Saves JSON under `data/debug/` and prints it.

---

## Performance tips

* **`--qps`** is a global ceiling across threads. Start conservative (e.g., `1.0–1.4`). If you hit HTTP 429 or 5xx spikes, lower it.
* **`--workers`** overlaps network latency. 6–8 is a good starting point.
* You can safely **stop** any phase (Ctrl+C) and re-run later—everything is incremental.

---

## Editing your custom fields

Edit only the `customData` block, e.g.:

```json
"customData": {
  "watchlist": true,
  "ceiExpertNotes": "Flag for weekly review",
  "priorityLevel": "A"
}
```

Re-running phases will not change `customData`.

---

## Housekeeping & cleanup

Safe to delete any time:

* `__pycache__/` folders
* `*.pyc` files
* `data/debug/` (raw probe outputs)

Keep:

* `.venv/` (your local Python environment)
* `.env` (your API key)
* `data/bills_119.json` (the database)

Optional `.gitignore` (if you use git):

```
# Python
__pycache__/
*.pyc

# Local env & secrets
.venv/
.env

# Generated data
data/debug/
```

---

## Common issues

* **`pip: command not found` in Git Bash** → use `python -m pip install ...`
* **Venv not activating** → in Git Bash: `source .venv/Scripts/activate`
* **Null committees** → some bills have no current referral; that’s normal.
* **Early runs saved nulls** → phases now “re-enrich” missing fields; re-run `detail`/`committees`.

---

## Next steps (optional)

* Add a `--since` window to Phase 1 (only list updates since a timestamp).
* Add tagging & filtering in `customData`.
* Export CSV/Excel reports from `stats.py`.

---

*(Copy this into a file named `README.md` in your HillWatch 2 folder.)*

test
test2