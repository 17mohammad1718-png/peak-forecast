"""Daily collector: ingest live radar calendars into peak_forecast.db.

Captures actual fetch timestamp (fetched_at) alongside ingestion date (seen_on).
Distinguishes statuses:
  - free (آزاد)
  - unavailable_unknown (ناموجود با علت نامشخص)
  - confirmed_block (بلاک تأییدشده)
  - confirmed_booking (رزرو تأییدشده)
"""
import json
import os
import sqlite3
from datetime import date, datetime
from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS nights (
    room_id    INTEGER NOT NULL,
    night      TEXT    NOT NULL,
    seen_on    TEXT    NOT NULL,
    price      INTEGER,
    booked     INTEGER NOT NULL DEFAULT 0,
    own        INTEGER NOT NULL DEFAULT 0,
    status     TEXT    NOT NULL DEFAULT 'free',
    fetched_at TEXT,
    PRIMARY KEY (room_id, night, seen_on)
);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""

# Status definitions (FA & EN)
STATUS_FREE = "free"
STATUS_UNAVAILABLE_UNKNOWN = "unavailable_unknown"
STATUS_CONFIRMED_BLOCK = "confirmed_block"
STATUS_CONFIRMED_BOOKING = "confirmed_booking"

STATUS_FA = {
    STATUS_FREE: "آزاد",
    STATUS_UNAVAILABLE_UNKNOWN: "ناموجود با علت نامشخص",
    STATUS_CONFIRMED_BLOCK: "بلاک تأییدشده",
    STATUS_CONFIRMED_BOOKING: "رزرو تأییدشده",
}

def init_db(db_path):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    
    # Migrations for existing databases
    for col, col_type in [("status", "TEXT DEFAULT 'free'"), ("fetched_at", "TEXT")]:
        try:
            con.execute(f"ALTER TABLE nights ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass  # column already exists
            
    con.commit()
    con.close()

def resolve_status(nt, own):
    """Determine status based on availability and host ownership."""
    is_unavail = bool(nt.get("is_unavailable"))
    if not is_unavail:
        return STATUS_FREE

    raw_status = str(nt.get("status") or "").lower()
    if own:
        if raw_status in ("block", "blocked", "closed", "confirmed_block", "بلاک"):
            return STATUS_CONFIRMED_BLOCK
        if raw_status in ("booked", "reserved", "confirmed_booking", "رزرو"):
            return STATUS_CONFIRMED_BOOKING
        # Default own unavailable is confirmed booking unless marked block
        return STATUS_CONFIRMED_BOOKING
    else:
        if raw_status in ("block", "blocked", "confirmed_block"):
            return STATUS_CONFIRMED_BLOCK
        if raw_status in ("booked", "confirmed_booking"):
            return STATUS_CONFIRMED_BOOKING
        # Rivals: typically we only observe unavailable without internal cause
        return STATUS_UNAVAILABLE_UNKNOWN

def ingest_live_snapshot(db_path, calendars, today_iso, fetch_ts_default=None):
    init_db(db_path)
    con = sqlite3.connect(db_path)
    rows = []
    
    for cal in calendars:
        rid = cal["room_id"]
        own = 1 if cal.get("meta", {}).get("own") or rid == config.OWN_ROOM_ID else 0
        fetched_at = cal.get("fetched_at") or fetch_ts_default or today_iso
        
        for nt in cal.get("nights", []):
            st = resolve_status(nt, own)
            is_booked = 0 if st == STATUS_FREE else 1
            rows.append((
                rid,
                nt["date"],
                today_iso,
                nt.get("price"),
                is_booked,
                own,
                st,
                fetched_at,
            ))
            
    con.executemany(
        "INSERT OR IGNORE INTO nights(room_id, night, seen_on, price, booked, own, status, fetched_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    con.execute("INSERT OR REPLACE INTO meta VALUES ('last_collect', ?)", (today_iso,))
    con.commit()
    con.close()
    return len(rows)

def load_live_calendars(radar_dir):
    out = []
    if not os.path.exists(radar_dir):
        return out
    for f in sorted(os.listdir(radar_dir)):
        if f[0].isdigit() and f.endswith(".json"):
            f_path = os.path.join(radar_dir, f)
            try:
                data = json.load(open(f_path, encoding="utf-8"))
                mtime_dt = datetime.fromtimestamp(os.path.getmtime(f_path))
                data["fetched_at"] = data.get("fetched_at") or mtime_dt.isoformat(timespec="seconds")
                out.append(data)
            except Exception:
                continue
    return out

def is_data_fresh(fetched_at_str, today_iso, max_age_days=2):
    """Verify source timestamp is fresh relative to execution date."""
    if not fetched_at_str:
        return False
    try:
        f_date = date.fromisoformat(fetched_at_str[:10])
        t_date = date.fromisoformat(today_iso[:10])
        return (t_date - f_date).days <= max_age_days
    except Exception:
        return False

def collect(db_path=None, today=None):
    db_path = db_path or config.DB_PATH
    today = today or date.today().isoformat()
    init_db(db_path)
    cals = load_live_calendars(config.RADAR_LIVE)
    return ingest_live_snapshot(db_path, cals, today)

if __name__ == "__main__":
    n = collect()
    print(f"ingested {n} night-rows into {config.DB_PATH}")
