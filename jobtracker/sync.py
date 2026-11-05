import sys
from datetime import datetime, timedelta, timezone

from . import gmail, tiers
from .classify import classify_batch, company_key
from .config import BACKFILL_MONTHS
from .db import connect, get_meta, set_meta
from .report import write_xlsx

BATCH = 10
RERATE_DAYS = 30


def sync_emails(conn):
    last = get_meta(conn, "last_sync")
    now = datetime.now(timezone.utc)
    after = (datetime.fromisoformat(last) - timedelta(days=2)) if last else now - timedelta(days=30 * BACKFILL_MONTHS)
    svc = gmail.service()
    known = {r["id"] for r in conn.execute("SELECT id FROM emails")}
    ids = [i for i in gmail.list_ids(svc, after) if i not in known]
    print(f"новых писем: {len(ids)}", flush=True)
    for n in range(0, len(ids), BATCH):
        batch = [gmail.fetch(svc, i) for i in ids[n:n + BATCH]]
        for e, c in zip(batch, classify_batch(batch)):
            conn.execute(
                "INSERT OR REPLACE INTO emails VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (e["id"], e["thread_id"], e["date"], e["sender"], e["subject"], e["snippet"],
                 c["is_job"], c["company"], company_key(c["company"]), c["role"], c["event"],
                 c["stage_hint"], c["confidence"]))
        conn.commit()
        print(f"  {min(n + BATCH, len(ids))}/{len(ids)}", flush=True)
    set_meta(conn, "last_sync", now.isoformat())


def rekey(conn):
    """Пересчитать ключи по текущим правилам и склеить дубли компаний (оценки не теряются)."""
    for r in conn.execute("SELECT DISTINCT company FROM emails WHERE company IS NOT NULL").fetchall():
        conn.execute("UPDATE emails SET company_key=? WHERE company=?", (company_key(r["company"]), r["company"]))
    for c in conn.execute("SELECT * FROM companies ORDER BY rated_at DESC").fetchall():
        new = company_key(c["name"])
        if new == c["company_key"]:
            continue
        if new and not conn.execute("SELECT 1 FROM companies WHERE company_key=?", (new,)).fetchone():
            conn.execute("UPDATE companies SET company_key=? WHERE company_key=?", (new, c["company_key"]))
        else:
            conn.execute("DELETE FROM companies WHERE company_key=?", (c["company_key"],))
    conn.commit()


def _overridden(ov, name, key):
    d = ov.get(name) or ov.get(key)
    return {"category": "", "rationale": "ручная оценка", **d} if d else None


def rate_companies(conn, rerate=False, force=False):
    ov = tiers.overrides()
    now = datetime.now(timezone.utc).isoformat()
    new = conn.execute(
        """SELECT e.company_key, MAX(e.company) AS name FROM emails e
           LEFT JOIN companies c USING(company_key)
           WHERE e.is_job=1 AND e.company_key IS NOT NULL AND c.company_key IS NULL
           GROUP BY e.company_key""").fetchall()
    for r in new:
        d = _overridden(ov, r["name"], r["company_key"])
        manual = 1 if d else 0
        d = d or tiers.rate(r["name"])
        conn.execute("INSERT INTO companies (company_key,name,tier,category,rationale,manual,rated_at) VALUES (?,?,?,?,?,?,?)",
                     (r["company_key"], r["name"], d["tier"], d.get("category", ""), d.get("rationale", ""), manual, now))
        conn.commit()
        print(f"  новая {r['name']}: {d['tier']}", flush=True)
    if not rerate:
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(days=0 if force else RERATE_DAYS)).isoformat()
    for c in conn.execute("SELECT * FROM companies WHERE manual=0 AND rated_at < ?", (cutoff,)).fetchall():
        d = _overridden(ov, c["name"], c["company_key"]) or tiers.rate(c["name"])
        if d["tier"] != c["tier"]:
            conn.execute("UPDATE companies SET prev_tier=?, tier_changed_at=? WHERE company_key=?",
                         (c["tier"], now, c["company_key"]))
            print(f"  {c['name']}: {c['tier']} -> {d['tier']}", flush=True)
        conn.execute("UPDATE companies SET tier=?, category=?, rationale=?, rated_at=? WHERE company_key=?",
                     (d["tier"], d.get("category", c["category"]), d.get("rationale", ""), now, c["company_key"]))
        conn.commit()


def main():
    conn = connect()
    rekey(conn)
    if "--report-only" not in sys.argv:
        if "--rerate" not in sys.argv:
            sync_emails(conn)
        rate_companies(conn, rerate="--rerate" in sys.argv, force="--force" in sys.argv)
    print(f"компаний в таблице: {write_xlsx()}", flush=True)


if __name__ == "__main__":
    main()
