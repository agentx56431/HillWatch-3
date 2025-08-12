from pathlib import Path
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")

# Base folder paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "bills_119.json"

# Congress session to track
CONGRESS_NUMBER = 119

# Bill types to track
BILL_TYPES = ["hr", "s", "hjres", "sjres", "hconres", "sconres"]

# API base
API_BASE = "https://api.congress.gov/v3"

# Congress.gov slug mapping for URLs
SLUG_MAP = {
    "hr": "house-bill",
    "s": "senate-bill",
    "hjres": "house-joint-resolution",
    "sjres": "senate-joint-resolution",
    "hconres": "house-concurrent-resolution",
    "sconres": "senate-concurrent-resolution"
}

# CEI expert options (master list)
CEI_EXPERT_OPTIONS = [
    "Iain Murray",
    "John Berlau",
    "Richard Morrison",
    "Ryan Young",
    "Sean Higgins",
    "Stone Washington",
    "Clyde Wayne Crews",
    "Alex Reinauer",
    "Jessica Melugin",
    "Jeremy Nighossian",
    "Ondray Harris",
    "Devin Watkins",
    "David McFadden",
    "Ben Lieberman",
    "Daren Bakst",
    "Jacob Tomasulo",
    "Marlo Lewis",
    "Paige Lambermont"
]
