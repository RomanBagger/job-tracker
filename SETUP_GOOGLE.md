# Connect Gmail through Google Cloud (one time, ~10 minutes)

The app reads mail through the Gmail API with **read-only** access (`gmail.readonly`): it cannot send, delete or modify anything.
You need two files in the project folder: `credentials.json` (Gmail access) and `.env` (Anthropic key).

## 1. Project and Gmail API
1. Open <https://console.cloud.google.com> and sign in with the Google account whose mail you want to read.
2. Click the project picker at the top → **New project** → name it `job-tracker` → **Create**. Make sure it is selected.
3. Menu **APIs & Services → Library** → find **Gmail API** → **Enable**.

## 2. OAuth consent screen
1. **APIs & Services → OAuth consent screen** (in the new UI: **Google Auth Platform**).
2. User type **External**, app name `job-tracker`, your email as "User support" and "Developer contact" → Save.
3. **Audience → Test users → Add users** → enter **your own Gmail** → **Save**.
   Without this, sign-in fails with `403 access_denied` ("app has not completed Google verification").
4. Click **Publish app** (status *In production*). Google verification is not needed for personal use.
   While the status is *Testing*, the token lasts only 7 days and you will have to sign in again every week.

## 3. OAuth client
1. **APIs & Services → Credentials → Create credentials → OAuth client ID**.
2. Application type **Desktop app**, any name → **Create**.
3. Click **Download JSON** and save it as **`credentials.json`** in the project root (next to `run.sh`).

## 4. Anthropic key
1. <https://console.anthropic.com> → **Billing**: add credit ($5–10 lasts a long time).
2. **Settings → API Keys → Create Key**, copy the key (`sk-ant-...`, shown only once).
3. Copy `.env.example` to `.env` and paste the key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   BACKFILL_MONTHS=3
   ```
   `BACKFILL_MONTHS` is how many months of mail to read on the first run (3 for a test, 24 for full history).

## 5. First sign-in
Open the **Job Tracker** app and click **Update table** («Обновить таблицу (почта)»). A browser window from Google opens:
1. Choose your account.
2. If you see "Google hasn't verified this app", click **Advanced → Go to job-tracker (unsafe)**. It is your own app, so the warning is expected.
3. Allow read access to your mail.

This creates `token.json`, and you will not need to sign in again.

## Troubleshooting
| Symptom | What to do |
|---|---|
| `403 access_denied` at sign-in | Your email is not under **Test users** (step 2.3), or the app is not published. |
| Asks you to sign in again after a week | The app is in *Testing*: click **Publish app** and delete `token.json`. |
| `credentials.json` not found | The file is not in the project root or has another name (it downloads as `client_secret_…json`). |
| `invalid_grant` / token will not refresh | Delete `token.json` and sign in again. |
| Anthropic 401 / credit error | Check the key in `.env` and your balance in the Anthropic console. |
