import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

DB_PATH = DATA / "jobs.db"
XLSX_PATH = ROOT / "job_search.xlsx"
CREDENTIALS = ROOT / "credentials.json"
TOKEN = ROOT / "token.json"
TIER_OVERRIDES = ROOT / "tier_overrides.json"


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


load_env()
BACKFILL_MONTHS = int(os.environ.get("BACKFILL_MONTHS", "24"))
CLASSIFY_MODEL = os.environ.get("CLASSIFY_MODEL", "claude-haiku-5-5")
TIER_MODEL = os.environ.get("TIER_MODEL", "claude-sonnet-5-5")
