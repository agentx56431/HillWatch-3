# HillWatch v3

A local toolkit for storing, monitoring, and categorizing U.S. legislation from Congress.gov, with a desktop GUI to browse, search, filter, and manage a custom workflow (WatchList → Rejected → Complete).

> **Local-first**: The JSON database (`data/bills_119.json`) stays on your machine and is ignored by Git by default.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage (Terminal Commands)](#usage-terminal-commands)
- [GUI Overview](#gui-overview)
- [JSON Database Structure](#json-database-structure)
- [Data Dictionary](#data-dictionary)
- [Updater Phases](#updater-phases)
- [Troubleshooting](#troubleshooting)

---

## Project Structure

```

HillWatch 3/
├─ .venv/                     # Python virtual environment (ignored)
├─ data/
│  ├─ bills\_119.json          # Local JSON database (ignored by Git)
│  └─ debug/                  # Optional raw API probe dumps (ignored)
├─ desktop\_gui/
│  ├─ **init**.py
│  ├─ app.py                  # Main GUI application (left tabs + right details)
│  ├─ table\_view\.py           # Table widget (Title + Latest Action Date)
│  ├─ detail\_panel.py         # Right pane (Congress.gov data + Custom editor)
│  ├─ filter\_dialog.py        # Filters dialog (types, committees, sponsors, dates, sort)
│  ├─ data\_access.py          # JSON load/save helpers (safe, atomic writes)
│  ├─ collapsible.py          # Expand/collapse sections
│  └─ editor\_fields.py        # Reusable form controls (checkbox, text, date, CEI picker)
├─ bill\_utils.py              # Helpers shared by CLI tools
├─ config.py                  # Constants (paths, types, threading defaults)
├─ updater.py                 # CLI updater (phased API fetch + enrichment)
├─ raw\_api\_probe.py           # Prints raw API JSON for debugging mappings
├─ stats.py                   # Quick stats for the local JSON
├─ requirements.txt
├─ .gitignore
└─ README.md

````

**Git ignores** the venv, `.env`, logs, tmp files, `.vscode/`, and `data/bills_119.json`.

---

## Setup

```bash
# from the project root folder
python -m venv .venv
# Windows + Git Bash:
source .venv/Scripts/activate

# install dependencies
pip install -r requirements.txt

# (Optional) put your Congress.gov API key in .env as:
# CONGRESS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
````

> If you don’t use a `.env`, make sure `config.py` picks up your API key another way.

---

## Usage (Terminal Commands)

### Run the desktop app

```bash
python -m desktop_gui.app
```

### Show quick database stats

```bash
python stats.py
```

Outputs totals by phase and by bill type, plus last modified time.

### Probe raw API responses for one bill (debug)

```bash
python raw_api_probe.py
```

Dumps “list”, “detail”, and “committees” JSON for a sample bill into `data/debug/` and prints to terminal.

---

## GUI Overview

**Left side**: Tabs with searchable/sortable tables

* **Bills Feed** — all bills (always 100% of `bills_119.json`)
* **WatchList** — watchlisted bills *not* Rejected/Complete
* **Rejected** — `Review.WatchList = true`, `CEIExpertAcceptOrReject = false`, and `Review_Done = true`
* **Complete** — `Review.WatchList = true`, `CEIExpertAcceptOrReject = true`, and `Final_Tracking_Done = true`

Features:

* **Search** (as you type) across title, sponsor, committee, latest action text, etc.
* **Filters**: bill type, origin chamber, committees, sponsors, date range (Introduced or Latest Action), sort order.
* **Load More**: renders +200 in the current tab without reloading.

**Right side**: Details for selected row

* **View Legislation in Browser** (opens `congressGovUrl`)
* ⭐ **WatchList** toggle
* **Congress.gov Data** (read-only; open by default)
* **Custom** (collapsed by default) → Review, Outreach, FinalTracking (editable)

  * CEI Expert single-select with **Clear**
  * All edits **autosave** instantly and **re-route** the row across WatchList/Rejected/Complete as needed.

---

## JSON Database Structure

Top-level is a mapping of `billId` → bill record. Example (single bill abbreviated):

```json
{
  "S_2682": {
    "congressGovData": {
      "billId": "S_2682",
      "congress": 119,
      "billType": "S",
      "billNumber": "2682",
      "title": "Captain Paul W. 'Bud' Bucha VA Medical Center Act of 2025",
      "originChamber": "Senate",
      "introducedDate": "2025-08-02",
      "sponsorFullName": "Sen. Blumenthal, Richard [D-CT]",
      "sponsorParty": "D",
      "sponsorState": "CT",
      "sponsorDistrict": null,
      "currentCommitteeName": null,
      "currentSubcommitteeName": null,
      "latestActionText": "Message on Senate action sent to the House.",
      "latestActionDate": "2025-08-08",
      "updateDate": "2025-08-09",
      "updateDateIncludingText": "2025-08-09",
      "sourceUrl": "https://api.congress.gov/v3/bill/119/s/2682?format=json",
      "congressGovUrl": "https://www.congress.gov/bill/119th-congress/senate-bill/2682",
      "contentHash": "…",
      "committeeLastActionSeen": "2025-08-08"
    },
    "customData": {
      "Review": {
        "WatchList": false,
        "CeiExpert": [],
        "CeiExpertOptions": [
          "Iain Murray", "John Berlau", "Richard Morrison", "Ryan Young",
          "Sean Higgins", "Stone Washington", "Clyde Wayne Crews", "Alex Reinauer",
          "Jessica Melugin", "Jeremy Nighossian", "Ondray Harris", "Devin Watkins",
          "David McFadden", "Ben Lieberman", "Daren Bakst", "Jacob Tomasulo",
          "Marlo Lewis", "Paige Lambermont"
        ],
        "StatementRequested": false,
        "StatementRequestedDate": null,
        "CEIExpertAcceptOrReject": false,
        "Review_Done": false
      },
      "Outreach": {
        "Worked_Directly_with_Office": false,
        "Statement_Complete": false,
        "Statement_Complete_Date": null,
        "Statement_Emailed_Directly": false,
        "Statement_Emailed_Quorum": false,
        "InternalLed_Coalition_Letter": false,
        "ExternalLed_Coalition_Letter": false,
        "Support_Posted_Website": false,
        "Other_Support": "",
        "Outreach_Done": false
      },
      "FinalTracking": {
        "Press_Release_Mention": false,
        "Press Release Mention_Source": "",
        "Any_Public_Mention": false,
        "Any_Public_Mention_Source": "",
        "Notes_or_Other": "",
        "Public_Mention_Date": null,
        "Final_Tracking_Done": false
      }
    }
  }
}
```

---

## Data Dictionary

| Field                   | JSON Path                                 |               Type | Source                         | Notes                                                                      |
| ----------------------- | ----------------------------------------- | -----------------: | ------------------------------ | -------------------------------------------------------------------------- |
| billId                  | `congressGovData.billId`                  |             string | Auto (computed)                | `"{billType}_{billNumber}"`                                                |
| congress                | `congressGovData.congress`                |             number | Congress.gov API (list/detail) | 119                                                                        |
| billType                | `congressGovData.billType`                |             string | Congress.gov API (list/detail) | HR, S, HJRES, SJRES, HCONRES, SCONRES                                      |
| billNumber              | `congressGovData.billNumber`              |             string | Congress.gov API (list/detail) | e.g., `"2682"`                                                             |
| title                   | `congressGovData.title`                   |             string | Congress.gov API (list/detail) |                                                                            |
| originChamber           | `congressGovData.originChamber`           |             string | Congress.gov API (list/detail) | “House” or “Senate”                                                        |
| introducedDate          | `congressGovData.introducedDate`          | string(YYYY‑MM‑DD) | Congress.gov API (detail)      |                                                                            |
| sponsorFullName         | `congressGovData.sponsorFullName`         |             string | Congress.gov API (detail)      |                                                                            |
| sponsorParty            | `congressGovData.sponsorParty`            |             string | Congress.gov API (detail)      | D/R/I                                                                      |
| sponsorState            | `congressGovData.sponsorState`            |             string | Congress.gov API (detail)      |                                                                            |
| sponsorDistrict         | `congressGovData.sponsorDistrict`         |       string\|null | Congress.gov API (detail)      | null for Senators                                                          |
| currentCommitteeName    | `congressGovData.currentCommitteeName`    |       string\|null | Congress.gov API (committees)  | The single “current” committee (heuristic)                                 |
| currentSubcommitteeName | `congressGovData.currentSubcommitteeName` |       string\|null | Congress.gov API (committees)  |                                                                            |
| latestActionText        | `congressGovData.latestActionText`        |             string | Congress.gov API (list/detail) |                                                                            |
| latestActionDate        | `congressGovData.latestActionDate`        | string(YYYY‑MM‑DD) | Congress.gov API (list/detail) |                                                                            |
| updateDate              | `congressGovData.updateDate`              |             string | Congress.gov API               |                                                                            |
| updateDateIncludingText | `congressGovData.updateDateIncludingText` |             string | Congress.gov API               |                                                                            |
| sourceUrl               | `congressGovData.sourceUrl`               |             string | Auto (from API anchor)         | Canonical API URL for the bill                                             |
| congressGovUrl          | `congressGovData.congressGovUrl`          |             string | Auto (computed)                | `https://www.congress.gov/bill/{congress}th-congress/{type-name}/{number}` |
| contentHash             | `congressGovData.contentHash`             |             string | Auto (computed)                | Hash for change detection                                                  |
| committeeLastActionSeen | `congressGovData.committeeLastActionSeen` | string(YYYY‑MM‑DD) | Auto (computed)                | Used by updater to avoid reprocessing                                      |

**Custom — Review**

| Field                   | JSON Path                                   |                     Type | Source       | Notes                                               |
| ----------------------- | ------------------------------------------- | -----------------------: | ------------ | --------------------------------------------------- |
| WatchList               | `customData.Review.WatchList`               |                  boolean | Manual (GUI) | Drives inclusion in WatchList/Rejected/Complete     |
| CeiExpert               | `customData.Review.CeiExpert`               |           array\<string> | Manual (GUI) | Single-select via GUI; stored as list; can be empty |
| CeiExpertOptions        | `customData.Review.CeiExpertOptions`        |           array\<string> | Static list  | CEI expert names shown in picker                    |
| StatementRequested      | `customData.Review.StatementRequested`      |                  boolean | Manual       |                                                     |
| StatementRequestedDate  | `customData.Review.StatementRequestedDate`  | string(YYYY‑MM‑DD)\|null | Manual       |                                                     |
| CEIExpertAcceptOrReject | `customData.Review.CEIExpertAcceptOrReject` |                  boolean | Manual       | `True=Accept, False=Reject`                         |
| Review\_Done            | `customData.Review.Review_Done`             |                  boolean | Manual       | Marks review phase complete                         |

**Custom — Outreach**

| Field                          | JSON Path                                          |                     Type | Source | Notes     |
| ------------------------------ | -------------------------------------------------- | -----------------------: | ------ | --------- |
| Worked\_Directly\_with\_Office | `customData.Outreach.Worked_Directly_with_Office`  |                  boolean | Manual |           |
| Statement\_Complete            | `customData.Outreach.Statement_Complete`           |                  boolean | Manual |           |
| Statement\_Complete\_Date      | `customData.Outreach.Statement_Complete_Date`      | string(YYYY‑MM‑DD)\|null | Manual |           |
| Statement\_Emailed\_Directly   | `customData.Outreach.Statement_Emailed_Directly`   |                  boolean | Manual |           |
| Statement\_Emailed\_Quorum     | `customData.Outreach.Statement_Emailed_Quorum`     |                  boolean | Manual |           |
| InternalLed\_Coalition\_Letter | `customData.Outreach.InternalLed_Coalition_Letter` |                  boolean | Manual |           |
| ExternalLed\_Coalition\_Letter | `customData.Outreach.ExternalLed_Coalition_Letter` |                  boolean | Manual |           |
| Support\_Posted\_Website       | `customData.Outreach.Support_Posted_Website`       |                  boolean | Manual |           |
| Other\_Support                 | `customData.Outreach.Other_Support`                |                   string | Manual | Free text |
| Outreach\_Done                 | `customData.Outreach.Outreach_Done`                |                  boolean | Manual |           |

**Custom — FinalTracking**

| Field                         | JSON Path                                               |                     Type | Source | Notes                                                   |
| ----------------------------- | ------------------------------------------------------- | -----------------------: | ------ | ------------------------------------------------------- |
| Press\_Release\_Mention       | `customData.FinalTracking.Press_Release_Mention`        |                  boolean | Manual |                                                         |
| Press Release Mention\_Source | `customData.FinalTracking.Press Release Mention_Source` |                   string | Manual |                                                         |
| Any\_Public\_Mention          | `customData.FinalTracking.Any_Public_Mention`           |                  boolean | Manual |                                                         |
| Any\_Public\_Mention\_Source  | `customData.FinalTracking.Any_Public_Mention_Source`    |                   string | Manual |                                                         |
| Notes\_or\_Other              | `customData.FinalTracking.Notes_or_Other`               |                   string | Manual |                                                         |
| Public\_Mention\_Date         | `customData.FinalTracking.Public_Mention_Date`          | string(YYYY‑MM‑DD)\|null | Manual |                                                         |
| Final\_Tracking\_Done         | `customData.FinalTracking.Final_Tracking_Done`          |                  boolean | Manual | Triggers move to **Complete** when combined with Accept |

---

## Updater Phases

> You already separated API calls by phase for speed and control.

* **Phase: list** — hit `/bill/:congress/:billType` (6 types) to build the generic bill list.
* **Phase: detail** — per bill, hit `/bill/:congress/:billType/:number` to get `introducedDate`, sponsor fields, etc.
* **Phase: committees** — per bill, hit `/bill/:congress/:billType/:number/committees` and select the *current* committee/subcommittee.

Examples:

```bash
# fetch list (first pass)
python updater.py --phase list --workers 6 --qps 1.5

# enrich with detail (introduced date, sponsor, etc.)
python updater.py --phase detail --workers 6 --qps 1.2

# committees pass
python updater.py --phase committees --workers 6 --qps 1.0

# show what would be updated without writing
python updater.py --dry-run
```

* **Workers** = concurrent requests
* **QPS** = requests per second (respect API limits)

The updater **only updates changed bills** using content hashes + timestamps, so you don’t have to reprocess all 7,800+ bills each run.

---

## Troubleshooting

* **GUI shows nothing / import error** → Ensure you run in the venv and installed requirements:
  `source .venv/Scripts/activate && pip install -r requirements.txt`

* **JSON won’t save (Windows)** → If you see `PermissionError: [WinError 5]`:

  * Close any programs holding the file (Explorer preview, editors).
  * We write atomically (temp file + replace). If antivirus blocks, add an exception for the project folder.

* **Git “NUL” file** → If that ghost file appears:

  ```bash
  git rm --cached -f NUL 2> NUL
  git commit -m "Remove ghost NUL"
  git push
  ```

  And add `NUL` to `.gitignore`.

* **Count label after “Load More”** → It updates in the active tab and shows “Showing X of Y”; if it doesn’t, reload the app and report the tab where you saw it.

---

## License

Private internal project (no license published).

```

---

Want me to push these changes to your README wording (e.g., add screenshots later), or tweak any sections (like adding a “Build from scratch” checklist)?
::contentReference[oaicite:0]{index=0}
```
