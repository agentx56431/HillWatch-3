HillWatch 3
HillWatch 3 is a lightweight Python tool for fetching, processing, and storing U.S. congressional legislation from the official Congress.gov API.
It maintains a local JSON database for the 119th Congress, supports CEI‑specific tracking fields, and is ready for future GUI or dashboard layers.

Project structure
graphql
Copy
Edit
HillWatch-3/
├── README.md
├── requirements.txt                 # requests, python-dotenv
├── .gitignore
│
├── data/
│   ├── bills_119.json               # MAIN database (keep!)
│   ├── bills_119.backup.json        # Optional manual backup
│   └── debug/                       # Scratch outputs (ignored)
│
├── config.py                        # Paths, constants (e.g., DB_PATH)
├── bill_utils.py                    # Helpers (hashing, URL build, merges, etc.)
├── updater.py                       # Main updater (list → detail → committees)
├── add_customdata_structure.py      # Ensures customData schema on all bills
├── stats.py                         # Quick DB stats
└── raw_api_probe.py                 # Prints raw API JSON for a sample bill
Setup
bash
Copy
Edit
python -m venv .venv
source .venv/Scripts/activate     # (Git Bash on Windows)
pip install -r requirements.txt
Create .env:

ini
Copy
Edit
CONGRESS_API_KEY=your_api_key_here
Usage
Update/refresh the local database:

bash
Copy
Edit
python updater.py
Initialize/repair custom fields:

bash
Copy
Edit
python add_customdata_structure.py
See quick stats:

bash
Copy
Edit
python stats.py
Probe the API (lists + detail + committees for a sample):

bash
Copy
Edit
python raw_api_probe.py
JSON database structure (shape)
data/bills_119.json is a JSON object keyed by billId (e.g., "S_2682").
Each value has two top‑level sections: congressGovData (API‑driven) and customData (your fields).

json
Copy
Edit
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
      "currentCommitteeName": "Veterans' Affairs Committee",
      "currentSubcommitteeName": null,
      "latestActionText": "Message on Senate action sent to the House.",
      "latestActionDate": "2025-08-08",
      "updateDate": "2025-08-09",
      "updateDateIncludingText": "2025-08-09",
      "sourceUrl": "https://api.congress.gov/v3/bill/119/s/2682?format=json",
      "congressGovUrl": "https://www.congress.gov/bill/119th-congress/senate-bill/2682",
      "contentHash": "2ae1e5...d665c90",
      "committeeLastActionSeen": "2025-08-08"
    },
    "customData": {
      "Review": {
        "WatchList": false,
        "CeiExpert": [],
        "StatementRequested": false,
        "StatementRequestedDate": null,
        "CEIExpertAcceptOrReject": false,
        "Review_Done": false,
        "CeiExpertOptions": [
          "Iain Murray", "John Berlau", "Richard Morrison", "Ryan Young",
          "Sean Higgins", "Stone Washington", "Clyde Wayne Crews", "Alex Reinauer",
          "Jessica Melugin", "Jeremy Nighossian", "Ondray Harris", "Devin Watkins",
          "David McFadden", "Ben Lieberman", "Daren Bakst", "Jacob Tomasulo",
          "Marlo Lewis", "Paige Lambermont"
        ]
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
Data dictionary
Endpoints used

List: /v3/bill/{congress}/{billType}?offset=&limit=&format=json → “API(list)”

Detail: /v3/bill/{congress}/{billType}/{number}?format=json → “API(detail)”

Committees: /v3/bill/{congress}/{billType}/{number}/committees?format=json → “API(committees)”

Sources legend

API(list): basic bill rows from the list endpoint

API(detail): fuller, single‑bill endpoint (sponsors, introducedDate, etc.)

API(committees): bill committees/subcommittees list

Auto: derived/calculated locally

Manual: user‑maintained custom fields

A) congressGovData fields
Key	Type	Source	Notes
billId	string	Auto	Internal ID ${billType}_${billNumber} (e.g., S_2682).
congress	integer	API(list) / API(detail)	Congress number (e.g., 119).
billType	string	API(list) / API(detail)	One of HR, S, HJRES, SJRES, HCONRES, SCONRES.
billNumber	string	API(list) / API(detail)	Numeric string (“2682”).
title	string	API(list) / API(detail)	Chosen default title from API (typically “title” in list).
originChamber	string	API(list) / API(detail)	“House” or “Senate”.
introducedDate	string(YYYY‑MM‑DD) or null	API(detail)	bill.introducedDate.
sponsorFullName	string or null	API(detail)	bill.sponsors[0].fullName if present.
sponsorParty	string or null	API(detail)	bill.sponsors[0].party.
sponsorState	string or null	API(detail)	bill.sponsors[0].state.
sponsorDistrict	string or null	API(detail)	bill.sponsors[0].district if present (House).
currentCommitteeName	string or null	API(committees)	First active/most recent committee (we pick one).
currentSubcommitteeName	string or null	API(committees)	First active subcommittee (if any).
latestActionText	string	API(list) / API(detail)	latestAction.text.
latestActionDate	string(YYYY‑MM‑DD)	API(list) / API(detail)	latestAction.actionDate.
updateDate	string(YYYY‑MM‑DD)	API(list)	When API row last updated (not our local write).
updateDateIncludingText	string(YYYY‑MM‑DD)	API(list)	API’s “including text” update marker.
sourceUrl	string	Auto	Stored canonical detail URL we hit for this bill.
congressGovUrl	string	Auto	Pretty URL: https://www.congress.gov/bill/{congress}th-congress/{type-name}/{number} (e.g., senate-bill for S).
contentHash	string	Auto	Hash of selected fields; used to detect content changes and avoid rewriting unchanged bills.
committeeLastActionSeen	string(YYYY‑MM‑DD) or null	Auto	Timestamp we last observed a committee/subcommittee assignment (for incremental updates).

B) customData → Manual (user‑maintained, with sensible defaults)
Review (manual; defaults set by add_customdata_structure.py)
Key	Type	Source	Notes
WatchList	boolean	Manual	Star/flag for internal watchlist.
CeiExpert	array<string>	Manual	Selected experts from options.
StatementRequested	boolean	Manual	Whether we requested a statement.
StatementRequestedDate	date or null	Manual	YYYY‑MM‑DD.
CEIExpertAcceptOrReject	boolean	Manual	True=Accept, False=Reject.
Review_Done	boolean	Manual	Marks review completion.
CeiExpertOptions	array<string>	Manual (pre‑seeded)	Shared list of allowable experts.

Outreach (manual)
Key	Type	Source	Notes
Worked_Directly_with_Office	boolean	Manual	Outreach status.
Statement_Complete	boolean	Manual	Whether statement text is finalized.
Statement_Complete_Date	date or null	Manual	YYYY‑MM‑DD.
Statement_Emailed_Directly	boolean	Manual	Sent directly to offices.
Statement_Emailed_Quorum	boolean	Manual	Sent via Quorum.
InternalLed_Coalition_Letter	boolean	Manual	Internal coalition letters.
ExternalLed_Coalition_Letter	boolean	Manual	External coalition letters.
Support_Posted_Website	boolean	Manual	Posted on CEI site.
Other_Support	string	Manual	Free‑text notes.
Outreach_Done	boolean	Manual	Outreach complete.

FinalTracking (manual)
Key	Type	Source	Notes
Press_Release_Mention	boolean	Manual	Was bill mentioned in a release?
Press Release Mention_Source	string	Manual	Source/URL/notes.
Any_Public_Mention	boolean	Manual	Any public mention online/press.
Any_Public_Mention_Source	string	Manual	Source/URL/notes.
Notes_or_Other	string	Manual	Free‑text notes.
Public_Mention_Date	date or null	Manual	YYYY‑MM‑DD.
Final_Tracking_Done	boolean	Manual	Final tracking complete.

Tab logic (for future GUI):

WatchList tab: Review.WatchList == True and Review.Review_Done == False

Rejected tab: Review.Review_Done == True and Review.CEIExpertAcceptOrReject == False

Complete tab: FinalTracking.Final_Tracking_Done == True

Update strategy (fast & incremental)
Phase 1: List calls per billType, paginated (pulls basic fields & latestAction + API updateDates).

Phase 2: Detail calls for bills that are new/changed since last contentHash.

Phase 3: Committees calls only when missing or updateDate moved forward.

Writes are idempotent: unchanged bills are skipped (via contentHash).

Tips & safety
Keep .env out of Git (already in .gitignore).

Keep data/bills_119.json under Git if you want history; otherwise add it to .gitignore and keep only a small sample_bills.json for sharing.

Make a manual backup occasionally:

bash
Copy
Edit
cp data/bills_119.json data/bills_119.backup.json