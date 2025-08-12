HillWatch 3
HillWatch 3 is a lightweight Python-based tool for fetching, processing, and storing U.S. congressional legislation data from the Congress.gov API.
It maintains a local JSON database of all bills in the 119th Congress, supports custom data fields, and is designed for easy future integration with GUIs or data dashboards.

📂 Project Structure
plaintext
Copy
Edit
HillWatch-3/
│
├── .gitignore                # Files/folders ignored by Git
├── README.md                 # Project documentation (you are here)
├── requirements.txt          # Python dependencies
│
├── data/                      # Local data storage
│   ├── bills_119.json         # Main JSON database of all 119th Congress bills
│   ├── bills_119.backup.json  # Backup copy of the database
│   └── debug/                 # Temporary debug JSON dumps (ignored in Git)
│
├── add_customdata_structure.py # Script to add CEI-specific tracking fields to the bill database
├── bill_utils.py               # Helper functions for bill data processing
├── config.py                   # Configuration (API keys, constants, etc.)
├── raw_api_probe.py            # Simple probe script to test Congress.gov API connections
├── stats.py                    # Summarizes stored bills and custom tracking stats
└── updater.py                  # Main script for pulling new/updated bill data from Congress.gov API
📊 Data Dictionary
The main database (data/bills_119.json) is a list of bill objects.
Below is the definition of each key:

Field Name	Type	Description
billId	string	Unique internal ID for the bill (e.g., S_2682)
congress	integer	Congress number (e.g., 119)
billType	string	Bill type abbreviation (e.g., S, HR, HJRES)
billNumber	integer	Official bill number
title	string	Official title of the bill
originChamber	string	Chamber where the bill originated (Senate or House)
introducedDate	string	Date bill was introduced (YYYY-MM-DD)
sponsorFullName	string	Full name of the bill's sponsor
sponsorParty	string	Party affiliation of sponsor
sponsorState	string	State abbreviation of sponsor
sponsorDistrict	string/null	Sponsor's district (House only)
currentCommitteeName	string/null	Current assigned committee
currentSubcommitteeName	string/null	Current assigned subcommittee
latestActionText	string	Summary of the latest action
latestActionDate	string	Date of latest action
updateDate	string	Last time this bill was updated in the local database
updateDateIncludingText	string	Same as updateDate, but also tracks text changes
sourceUrl	string	Source URL of API data
congressGovUrl	string	Direct Congress.gov bill page
contentHash	string	Hash of the content to detect changes
Custom Tracking Fields		Added via add_customdata_structure.py for CEI purposes
Review	boolean	Mark for review
WatchList	boolean	Flag for watch list
CeiExpert	string	Assigned CEI expert
StatementRequested	boolean	Whether a statement was requested
StatementRequestedDate	string	Date statement was requested
CEIExpertAcceptOrReject	string	Expert’s decision
Review_Done	boolean	Whether review was completed
CeiExpertOptions	list	Suggested CEI experts
Outreach	boolean	Whether outreach has been done
... (more tracking fields as needed)		

⚙️ Installation
Clone the repository

bash
Copy
Edit
git clone https://github.com/agentx56431/HillWatch-3.git
cd HillWatch-3
Create & activate virtual environment

bash
Copy
Edit
python -m venv .venv
source .venv/Scripts/activate  # Git Bash (Windows)
# or
.venv\Scripts\activate         # CMD/PowerShell (Windows)
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Set up .env file

ini
Copy
Edit
CONGRESS_API_KEY=your_api_key_here
🚀 Core Commands
Update database with latest Congress.gov data
bash
Copy
Edit
python updater.py
Fetches new bills and updates existing bills.

Maintains data/bills_119.json with incremental changes.

Add custom CEI tracking fields
bash
Copy
Edit
python add_customdata_structure.py
Adds internal tracking fields to all bills (if missing).

Ensures database schema consistency.

View database statistics
bash
Copy
Edit
python stats.py
Outputs:

Total bills stored

Number of bills per chamber

Breakdown by latest action

CEI tracking progress

Quick API probe
bash
Copy
Edit
python raw_api_probe.py
Tests Congress.gov API key and returns a sample bill record.

🛡 .gitignore Rules
These files/folders are ignored from Git tracking:

bash
Copy
Edit
__pycache__/
*.pyc
.venv/
.env
data/debug/
*.log
*.tmp
.vscode/
Thumbs.db
.DS_Store
📌 Notes
This version of HillWatch is core logic only (no GUI).

All future UI/Dashboard integrations should pull from data/bills_119.json.

The database is append/update safe—you can run updater.py multiple times without data duplication.