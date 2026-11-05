import json
import re

import anthropic

from .config import CLASSIFY_MODEL

EVENTS = ["applied", "hr_invite", "tech_invite", "final_invite", "test_task",
          "rejected", "offer", "recruiter_outreach", "other"]

SYSTEM = """Ты разбираешь письма из почты соискателя на вакансии DevOps / Platform / SRE (Польша).
Для каждого письма верни объект:
- id: как во входе
- is_job: true, если письмо относится к конкретному процессу найма (отклик, приглашение, отказ, оффер, тестовое, письмо рекрутера по вакансии). Рассылки job-бордов, дайджесты, реклама, не про найм -> false
- company: название нанимающей компании (не job-борд, не рекрутинговое агентство-посредник, если видна конечная компания; если только агентство - его название). Нормализуй: без Sp. z o.o., Inc, Ltd
- role: название позиции или null
- event: одно из applied | hr_invite (созвон с HR/рекрутером, скрининг) | tech_invite (техническое интервью) | final_invite (финальный раунд, интервью с менеджером/командой) | test_task | rejected | offer | recruiter_outreach (рекрутер написал первым, ответа кандидата ещё нет) | other
- stage_hint: только для rejected - на каком этапе отказ, если это ясно из текста: auto (автоответ/без интервью) | hr | tech | final; иначе null
- confidence: 0..1
Отвечай ТОЛЬКО JSON-массивом, без пояснений."""


def _client():
    return anthropic.Anthropic()


def _parse(text):
    m = re.search(r"\[.*\]", text, re.S)
    return json.loads(m.group(0)) if m else []


def classify_batch(emails):
    payload = [
        {"id": e["id"], "date": e["date"][:10], "from": e["sender"], "subject": e["subject"],
         "text": e["body"][:1500] or e["snippet"]}
        for e in emails
    ]
    resp = _client().messages.create(
        model=CLASSIFY_MODEL,
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    out = {r["id"]: r for r in _parse("".join(b.text for b in resp.content if b.type == "text")) if "id" in r}
    results = []
    for e in emails:
        r = out.get(e["id"], {})
        event = r.get("event") if r.get("event") in EVENTS else "other"
        results.append({
            "is_job": 1 if r.get("is_job") else 0,
            "company": (r.get("company") or None),
            "role": r.get("role"),
            "event": event,
            "stage_hint": r.get("stage_hint"),
            "confidence": float(r.get("confidence") or 0),
        })
    return results


SUFFIXES = (r"sp\.? ?z ?o\.?o\.?|inc|ltd|llc|gmbh|s\.a\.|group|polska|poland|technologies|technology|"
            r"systems|consulting|software|international|limited|corporation|corp|co")


def company_key(name):
    """Ключ для склейки дублей: 'Akamai Technologies' == 'Akamai', 'Skydance (Paramount)' == 'Paramount'."""
    if not name:
        return None
    paren = re.search(r"\(([^)]+)\)", name)
    if paren:
        name = paren.group(1)
    s = re.sub(rf"\b({SUFFIXES})\b\.?", "", name.lower())
    return re.sub(r"[^a-z0-9а-я]+", "", s) or None
