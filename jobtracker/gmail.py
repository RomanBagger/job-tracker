import base64
import re
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import CREDENTIALS, TOKEN

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Грубый префильтр на стороне Gmail, чтобы не гонять через LLM всю почту.
KEYWORDS = [
    "application", "applied", "apply", "interview", "candidate", "candidacy", "recruiter",
    "position", "vacancy", "role", "hiring", "offer", "unfortunately", "regret", "assessment",
    "take-home", "screening", "your profile", "opportunity", "career", "talent",
    "вакансия", "вакансии", "отклик", "собеседование", "интервью", "кандидат", "рекрутер",
    "к сожалению", "оффер", "тестовое", "позиция", "резюме", "приглашаем", "отказ",
]
SEARCH_Q = "({}) -category:promotions -category:social -in:spam -in:trash".format(
    " OR ".join(f'"{k}"' if " " in k else k for k in KEYWORDS)
)


def service():
    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_ids(svc, after: datetime):
    q = f"{SEARCH_Q} after:{after.strftime('%Y/%m/%d')}"
    ids, token = [], None
    while True:
        r = svc.users().messages().list(userId="me", q=q, pageToken=token, maxResults=500).execute()
        ids += [m["id"] for m in r.get("messages", [])]
        token = r.get("nextPageToken")
        if not token:
            return ids


def _body_text(payload):
    def walk(p):
        mime = p.get("mimeType", "")
        data = p.get("body", {}).get("data")
        if mime == "text/plain" and data:
            yield "plain", base64.urlsafe_b64decode(data).decode("utf-8", "replace")
        elif mime == "text/html" and data:
            yield "html", base64.urlsafe_b64decode(data).decode("utf-8", "replace")
        for sub in p.get("parts", []) or []:
            yield from walk(sub)

    parts = list(walk(payload))
    plain = [t for k, t in parts if k == "plain"]
    if plain:
        return "\n".join(plain)
    html = "\n".join(t for k, t in parts if k == "html")
    html = re.sub(r"(?s)<(script|style).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def fetch(svc, mid):
    m = svc.users().messages().get(userId="me", id=mid, format="full").execute()
    h = {x["name"].lower(): x["value"] for x in m["payload"].get("headers", [])}
    date = datetime.fromtimestamp(int(m["internalDate"]) / 1000, tz=timezone.utc)
    return {
        "id": mid,
        "thread_id": m["threadId"],
        "date": date.isoformat(),
        "sender": h.get("from", ""),
        "subject": h.get("subject", ""),
        "snippet": m.get("snippet", ""),
        "body": re.sub(r"\s+", " ", _body_text(m["payload"])).strip()[:3500],
    }
