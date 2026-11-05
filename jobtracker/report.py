from collections import Counter, defaultdict
from datetime import datetime, timezone

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from .config import XLSX_PATH
from .db import connect

STAGE_ORDER = {"applied": 1, "hr": 2, "tech": 3, "final": 4, "offer": 5}
STAGE_LABEL = {0: "—", 1: "CV / отклик", 2: "HR", 3: "Tech", 4: "Final", 5: "Offer"}
EVENT_STAGE = {"applied": 1, "recruiter_outreach": 0, "hr_invite": 2, "test_task": 3,
               "tech_invite": 3, "final_invite": 4, "offer": 5}
STALE_DAYS = 30
TIER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
TIER_FILL = {"S": "FFD700", "A": "A8E6A3", "B": "CFE8FF", "C": "EEEEEE", "D": "F4B6B6"}


def company_rows(conn):
    emails = conn.execute(
        "SELECT * FROM emails WHERE is_job=1 AND company_key IS NOT NULL ORDER BY date").fetchall()
    meta = {r["company_key"]: r for r in conn.execute("SELECT * FROM companies")}
    by = defaultdict(list)
    for e in emails:
        by[e["company_key"]].append(e)
    rows = []
    for key, es in by.items():
        reached, rejected_hint, rejected_at = 0, None, None
        for e in es:
            reached = max(reached, EVENT_STAGE.get(e["event"], 0))
            if e["event"] == "rejected":
                rejected_at, rejected_hint = e["date"], e["stage_hint"]
        rejected = rejected_at is not None
        if rejected:
            hint = {"auto": 1, "hr": 2, "tech": 3, "final": 4}.get(rejected_hint, 0)
            reached = max(reached, hint, 1)
        last_date = es[-1]["date"][:10]
        stale = (datetime.now(timezone.utc) - datetime.fromisoformat(es[-1]["date"])).days > STALE_DAYS
        if reached >= 5:
            status = "Offer"
        elif rejected:
            status = f"Отказ: {STAGE_LABEL[reached]}"
        elif reached == 0:
            status = "Рекрутер написал" if not stale else "Рекрутер написал (без ответа)"
        else:
            status = "Нет ответа" if stale else "В процессе"
        m = meta.get(key)
        roles = [e["role"] for e in es if e["role"]]
        rows.append({
            "company": m["name"] if m and m["name"] else es[-1]["company"],
            "tier": m["tier"] if m else "?",
            "category": m["category"] if m else "",
            "rationale": m["rationale"] if m else "",
            "change": f"{m['prev_tier']} → {m['tier']}" if m and m["prev_tier"] else "",
            "role": Counter(roles).most_common(1)[0][0] if roles else "",
            "stage": STAGE_LABEL[reached] if reached else STAGE_LABEL[1],
            "reached": reached,
            "status": status,
            "first": es[0]["date"][:10],
            "last": es[-1]["date"][:10],
            "n": len(es),
        })
    rows.sort(key=lambda r: (TIER_ORDER.get(r["tier"], 9), r["company"].lower()))
    return rows


def write_xlsx():
    conn = connect()
    rows = company_rows(conn)
    wb = Workbook()

    ws = wb.active
    ws.title = "Компании"
    head = ["Компания", "Тир", "Тип", "Роль", "Дошёл до", "Статус", "Первое письмо", "Последнее", "Писем", "Смена тира", "Почему такой тир"]
    ws.append(head)
    def closed(r):
        return r["status"].startswith("Отказ") or r["status"] == "Offer"

    ACTIVE_ORDER = {"В процессе": 0, "Рекрутер написал": 1, "Нет ответа": 2, "Рекрутер написал (без ответа)": 3}
    active = sorted((r for r in rows if not closed(r)),
                    key=lambda r: (ACTIVE_ORDER.get(r["status"], 9), TIER_ORDER.get(r["tier"], 9), r["company"].lower()))
    done = sorted((r for r in rows if closed(r)),
                  key=lambda r: (r["status"] != "Offer", TIER_ORDER.get(r["tier"], 9), r["company"].lower()))

    def section(title, fill):
        ws.append([title])
        for c in ws[ws.max_row]:
            c.font = Font(bold=True, size=12)
            c.fill = PatternFill("solid", fgColor=fill)

    def add(r, grey=False):
        ws.append([r["company"], r["tier"], r["category"], r["role"], r["stage"], r["status"],
                   r["first"], r["last"], r["n"], r["change"], r["rationale"]])
        row = ws[ws.max_row]
        row[1].fill = PatternFill("solid", fgColor=TIER_FILL.get(r["tier"], "FFFFFF"))
        if grey:
            for i, c in enumerate(row):
                if i != 1:
                    c.font = Font(color="777777")

    section(f"В процессе ({len(active)})", "D9EAD3")
    for r in active:
        add(r)
    ws.append([])
    section(f"Закрытые: отказы и офферы ({len(done)})", "E0E0E0")
    for r in done:
        add(r, grey=True)

    st = wb.create_sheet("Статистика")
    total = len(rows)
    reached = Counter(r["stage"] for r in rows)
    st.append(["Воронка", "Компаний", "% от всех"])
    cum = 0
    order = ["CV / отклик", "HR", "Tech", "Final", "Offer"]
    for i, s in enumerate(order):
        cnt = sum(reached[x] for x in order[i:])
        st.append([f"Дошли до: {s}", cnt, round(cnt / total, 3) if total else 0])
    st.append([])
    st.append(["Где отказали", "Компаний"])
    for k, v in sorted(Counter(r["status"] for r in rows).items(), key=lambda x: -x[1]):
        st.append([k, v])
    st.append([])
    st.append(["Тир", "Компаний", "Дошли до tech+", "Офферы"])
    for t in "SABCD?":
        sub = [r for r in rows if r["tier"] == t]
        if sub:
            st.append([t, len(sub), sum(r["stage"] in ("Tech", "Final", "Offer") for r in sub),
                       sum(r["status"] == "Offer" for r in sub)])
    st.append([])
    st.append(["Месяц", "Писем по найму"])
    months = Counter(e["date"][:7] for e in conn.execute("SELECT date FROM emails WHERE is_job=1"))
    for k in sorted(months):
        st.append([k, months[k]])

    for sheet in (ws, st):
        for c in sheet[1]:
            c.font = Font(bold=True)
        for i in range(1, sheet.max_column + 1):
            sheet.column_dimensions[get_column_letter(i)].width = 60 if sheet is ws and i == 11 else 20
        sheet.freeze_panes = "A2"
    wb.save(XLSX_PATH)
    return len(rows)
