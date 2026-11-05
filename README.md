# Job Tracker

A Mac app that reads your Gmail, finds job-search emails (DevOps / Platform / SRE or any other role), and works out the
company and the stage (applied → HR → Tech → Final → rejected / offer). It rates every company on an S–D scale and shows
everything in a desktop window and in a `job_search.xlsx` spreadsheet.

Everything stays on your computer. Your mailbox is **read-only** (`gmail.readonly` scope).

---

## For humans: install in about 15 minutes

### What you need
| What | Why | Cost |
|---|---|---|
| A Mac | the app is built for macOS | n/a |
| Python 3.10+ | to run the code (check in Terminal: `python3 --version`; if missing, install from python.org) | free |
| A Gmail account | the mailbox to read | free |
| Google Cloud | one-time permission to read your mail | free |
| An Anthropic (Claude) API key | parses emails and rates companies | paid, $5–10 is plenty |

### Steps
**1. Download and build**
```
git clone https://github.com/RomanBagger/job-tracker.git
cd job-tracker
./build_app.sh
```
This creates **Job Tracker.app**.

**2. Anthropic API key**
1. Go to <https://console.anthropic.com> → Billing → add $5–10.
2. Settings → API Keys → Create Key → copy the key (`sk-ant-...`).
3. In the project folder run `cp .env.example .env` and paste the key into `.env`.

**3. Gmail access (Google Cloud)**: full walkthrough in **[SETUP_GOOGLE.md](SETUP_GOOGLE.md)**. In short:
1. <https://console.cloud.google.com> → create a project → enable **Gmail API**.
2. OAuth consent screen: type External, add **your own Gmail under Test users**, then click **Publish app**.
3. Credentials → Create credentials → OAuth client ID → **Desktop app** → download the JSON.
4. Save it in the project folder as **`credentials.json`**.

**4. Run it**
Open **Job Tracker.app** (drag it to the Dock if you like) and click **Update table** (the button is labelled
«Обновить таблицу (почта)»). A browser window opens for Google sign-in. If you see "Google hasn't verified this app",
choose **Advanced → Go to job-tracker (unsafe)** and allow access. The first pass over your mailbox takes a few minutes.

### Buttons
- **Update table** («Обновить таблицу (почта)»): reads new emails and refreshes the table.
- **Update company ratings** («Обновить рейтинг компаний»): re-rates every company. Slow and costs API credits.
- **Open Excel** («Открыть Excel»): opens `job_search.xlsx`.

> The app interface and the status names in the table are currently in Russian.

### Troubleshooting
| Symptom | Fix |
|---|---|
| `403 access_denied` when signing in to Google | Your email is not under **Test users**, or the app is not published (step 3.2) |
| Asks you to sign in again every week | You did not click **Publish app**. After publishing, delete `token.json` and sign in again |
| `credentials.json` not found | The file is not in the project root, or is still named `client_secret_….json`: rename it |
| Anthropic error 401 / credit balance | Check the key in `.env` and your balance |

Scheduling and manual company ratings are described at the bottom under "Advanced".

---

## For agents (Claude Code)

A person has downloaded this repository and wants help installing the app. Tell them to paste this into Claude Code:

> Clone https://github.com/RomanBagger/job-tracker, read CLAUDE.md and help me install the app step by step.

The agent runbook is in **[CLAUDE.md](CLAUDE.md)**: what to check, what the agent can do itself, and what only the user
can do in a browser.

---

## Advanced

**Scheduling (cron)**, via `crontab -e`:
```
0 8 * * 1  /path/to/job-tracker/run.sh            # emails: every Monday
0 9 1 * *  /path/to/job-tracker/run.sh --rerate   # ratings older than 30 days: 1st of the month
```
Log: `data/sync.log`. The Mac must be awake at that time.

**Manual company ratings** go in `tier_overrides.json`:
`{"Google": {"tier": "S", "category": "product", "rationale": "..."}}`. Such companies are never re-rated automatically.

**Settings** in `.env`: `BACKFILL_MONTHS` is how many months of mail to read on the first run (default 24; use 3 for a test).

**How it works:** `jobtracker/gmail.py` (reads Gmail) → `classify.py` (Claude Haiku parses emails) → `tiers.py`
(Claude Sonnet + web search rates companies) → SQLite `data/jobs.db` → `report.py` (xlsx) · `app.py` + `ui.html` (window).

**Never published (in `.gitignore`):** `.env`, `credentials.json`, `token.json`, `data/`, `job_search.xlsx`.
