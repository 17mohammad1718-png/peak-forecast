"""Own booking & decision ledger (v1.1).

Two tables in peak_forecast.db:
  reservations(id, start, end, nights, payout, status, note)
    status: confirmed | cancelled | refunded
  decisions(ts, target, suggested, applied, action, reason)
    action: done | hold | reject
Sources: manual JSON import (own_bookings.json) + Telegram responses.
"""
import json
import os
import sqlite3
from datetime import date
from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start TEXT NOT NULL, end TEXT NOT NULL, nights INTEGER NOT NULL,
    payout INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'confirmed',
    note TEXT DEFAULT '',
    UNIQUE(start, end, payout)
);
CREATE TABLE IF NOT EXISTS decisions (
    ts TEXT NOT NULL, target TEXT NOT NULL,
    suggested INTEGER, applied INTEGER,
    action TEXT NOT NULL, reason TEXT DEFAULT ''
);
"""

def _con():
    con = sqlite3.connect(config.DB_PATH)
    con.executescript(SCHEMA)
    return con

def import_bookings(json_path=None):
    """Import own bookings from exported JSON (chalet dashboard export).
    Accepts: [{start, nights, payout?, ...}] or dashboard-shaped records."""
    path = json_path or os.path.join(config.DATA, "own_bookings.json")
    if not os.path.exists(path):
        return {"imported": 0, "reason": "file not found: " + path}
    raw = json.load(open(path, encoding="utf-8"))
    rows = []
    for b in raw if isinstance(raw, list) else raw.get("bookings", []):
        st = str(b.get("start") or b.get("entry") or "")[:10]
        n = int(b.get("nights") or b.get("n") or 1)
        pay = int(b.get("payout") or b.get("net") or 0)
        stat = str(b.get("status") or "confirmed")
        if not st or len(st) != 10:
            continue
        from datetime import datetime, timedelta
        end = (datetime.strptime(st, "%Y-%m-%d") +
               timedelta(days=n)).date().isoformat()
        rows.append((st, end, n, pay, stat))
    con = _con()
    before = con.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    con.executemany(
        "INSERT OR IGNORE INTO reservations(start,end,nights,payout,status) "
        "VALUES (?,?,?,?,?)", rows)
    after = con.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    con.commit(); con.close()
    return {"imported": after - before, "total": after}

def record_decision(target, suggested, applied, action, reason=""):
    con = _con()
    con.execute("INSERT INTO decisions VALUES (datetime('now'),?,?,?,?,?)",
                (target, suggested, applied, action, reason))
    con.commit(); con.close()

def summary():
    con = _con()
    res = con.execute(
        "SELECT COUNT(*), SUM(nights), SUM(payout) FROM reservations "
        "WHERE status='confirmed'").fetchone()
    dec = con.execute(
        "SELECT action, COUNT(*) FROM decisions GROUP BY action").fetchall()
    con.close()
    confirmed_n, nights, payout = res
    adr = (payout / nights) if (nights and payout) else None
    return {"reservations": confirmed_n, "nights": nights,
            "payout": payout, "adr_net": adr, "decisions": dict(dec)}

if __name__ == "__main__":
    print(json.dumps(summary(), ensure_ascii=False, indent=1, default=str))
