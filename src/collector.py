"""Daily collector: ingest live radar calendars into peak_forecast.db.

Independence note: jajiga-tracker keeps ITS own history DB untouched; we keep
our own clean store keyed by (room_id, night, seen_on). Re-running the same
day is idempotent (INSERT OR IGNORE).
"""
import json
import os
import sqlite3
from datetime import date
from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS nights (
    room_id INTEGER NOT NULL,
    night   TEXT    NOT NULL,
    seen_on TEXT    NOT NULL,
    price   INTEGER,
    booked  INTEGER NOT NULL DEFAULT 0,
    own     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (room_id, night, seen_on)
);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    con.commit()
    con.close()

def ingest_live_snapshot(db_path, calendars, today_iso):
    con = sqlite3.connect(db_path)
    rows = []
    for cal in calendars:
        rid = cal["room_id"]
        own = 1 if cal.get("meta", {}).get("own") else 0
        for nt in cal.get("nights", []):
            rows.append((rid, nt["date"], today_iso, nt.get("price"),
                         1 if nt.get("is_unavailable") else 0, own))
    con.executemany("INSERT OR IGNORE INTO nights VALUES (?,?,?,?,?,?)", rows)
    con.execute("INSERT OR REPLACE INTO meta VALUES ('last_collect', ?)",
                (today_iso,))
    con.commit()
    con.close()
    return len(rows)

def load_live_calendars(radar_dir):
    out = []
    for f in sorted(os.listdir(radar_dir)):
        if f[0].isdigit() and f.endswith(".json"):
            out.append(json.load(open(os.path.join(radar_dir, f),
                                      encoding="utf-8")))
    return out

def collect(db_path=None, today=None):
    db_path = db_path or config.DB_PATH
    today = today or date.today().isoformat()
    init_db(db_path)
    cals = load_live_calendars(config.RADAR_LIVE)
    return ingest_live_snapshot(db_path, cals, today)

if __name__ == "__main__":
    n = collect()
    print(f"ingested {n} night-rows into {config.DB_PATH}")
