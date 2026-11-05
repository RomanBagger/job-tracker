# Agent runbook: installing Job Tracker

You are helping a person install this app on their Mac. Go one step at a time and verify each result with commands.
Use plain language and reply in the language the user writes in. Never ask the user to paste keys or tokens into the chat.

## What you do vs. what only the user can do
- **You:** checks (`python3 --version`), `./build_app.sh`, creating `.env` from `.env.example`, moving `credentials.json` out of
  Downloads, checking that files exist, running the app and diagnosing from logs.
- **Only the user** (in a browser): create the Google Cloud project, click the consent buttons, sign in to Google, add credit
  and create the Anthropic key. For these, give the link and 2–3 clear actions, then wait for "done".

## Order
1. **Environment.** macOS (`uname`), `python3 --version` (3.10+ needed). If Python is missing, suggest `brew install python` or python.org.
2. **Build.** In the repo root run `./build_app.sh`. `Job Tracker.app` should appear. On failure, read the output and fix it.
3. **Anthropic key.** Ask the user to create a key at <https://console.anthropic.com> (needs $5–10 credit). Create `.env` from
   `.env.example`; the user pastes the key into the file themselves (open it with `open -e .env`). Do not print the key.
   Check without showing the value: `awk -F= '/^ANTHROPIC_API_KEY/{print "key length:", length($2)}' .env` (expect > 50).
4. **Google Cloud.** Walk through `SETUP_GOOGLE.md`. Where people most often go wrong:
   - Enable **Gmail API** specifically.
   - **Add their own email under Test users** (otherwise `403 access_denied`).
   - Click **Publish app** (otherwise the token dies after 7 days).
   - The OAuth client type must be **Desktop app**.
   - Put the downloaded `client_secret_….json` in the repo root as `credentials.json`:
     `mv ~/Downloads/client_secret_*.json ./credentials.json` (make sure there is exactly one file and it has an `installed` key).
5. **First run.** Prefer a test: set `BACKFILL_MONTHS=3` in `.env`. Open `Job Tracker.app` and click "Update table"
   («Обновить таблицу (почта)»); the user signs in in the browser (the "not verified" warning → Advanced → Go to job-tracker).
   Or from the terminal: `.venv/bin/python -m jobtracker.sync` (can take tens of minutes; run it in the background and watch the output).
6. **Verify.** `token.json`, `data/jobs.db` and `job_search.xlsx` should exist. Look at the status distribution
   (`sqlite3 data/jobs.db "select event,count(*) from emails where is_job=1 group by 1"`) and show it to the user.
   If a company name is wrong or an email is not about hiring, fix the prompt in `jobtracker/classify.py`.
7. **Schedule (optional).** Offer the cron lines from the README. Ask permission before editing `crontab` and keep a backup of the old one.

## Common errors
| Error | Cause | Action |
|---|---|---|
| `403 access_denied` | email not in Test users / app not published | Add under Audience → Test users, Publish app |
| `invalid_grant: Token has been expired or revoked` | Testing-mode token (7 days) | Publish app; `mv token.json data/`; sign in again |
| `credentials.json` not found | not in repo root / wrong name | Find it in Downloads and rename |
| `AuthenticationError` / Anthropic 401 | empty or wrong key | Check `.env` without printing the key |
| `credit balance is too low` | no credit | Add credit at console.anthropic.com → Billing |
| `database is locked` | concurrent runs | Wait for the run to finish, restart the app |

## Rules
- Never commit or publish: `.env`, `credentials.json`, `token.json`, `data/`, `job_search.xlsx`, résumés. They are in `.gitignore`.
- The "Update company ratings" button («Обновить рейтинг компаний», `--rerate --force`) re-rates every company with web search:
  slow and paid. Warn the user before running it.
- Mail is read-only; never add code that sends, deletes or labels emails.
- The UI and status names are in Russian; translate for the user if they do not read Russian.
