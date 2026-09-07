import sys
import os
import tempfile
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.collector import (
    init_db,
    ingest_live_snapshot,
    resolve_status,
    is_data_fresh,
    STATUS_FREE,
    STATUS_UNAVAILABLE_UNKNOWN,
    STATUS_CONFIRMED_BLOCK,
    STATUS_CONFIRMED_BOOKING,
)

def test_ingest_idempotent():
    db = os.path.join(tempfile.mkdtemp(), "t.db")
    init_db(db)
    snap = [{
        "room_id": 111,
        "meta": {"own": True},
        "nights": [{"date": "2026-09-10", "price": 2400000, "is_unavailable": True}]
    }]
    ingest_live_snapshot(db, snap, "2026-09-07")
    ingest_live_snapshot(db, snap, "2026-09-07")
    con = sqlite3.connect(db)
    n, d = con.execute("SELECT COUNT(*), COUNT(DISTINCT room_id) FROM nights").fetchone()
    assert (n, d) == (1, 1)

def test_status_separation():
    # Free
    assert resolve_status({"is_unavailable": False}, own=False) == STATUS_FREE
    # Rival unavailable (default: unknown)
    assert resolve_status({"is_unavailable": True}, own=False) == STATUS_UNAVAILABLE_UNKNOWN
    # Rival with explicit block
    assert resolve_status({"is_unavailable": True, "status": "blocked"}, own=False) == STATUS_CONFIRMED_BLOCK
    # Own unavailable (default: confirmed booking)
    assert resolve_status({"is_unavailable": True}, own=True) == STATUS_CONFIRMED_BOOKING
    # Own with explicit block
    assert resolve_status({"is_unavailable": True, "status": "closed"}, own=True) == STATUS_CONFIRMED_BLOCK

def test_stale_data_detection():
    # Fresh
    assert is_data_fresh("2026-09-07", "2026-09-07", max_age_days=2) is True
    # Stale (source fetched 10 days ago)
    assert is_data_fresh("2026-08-28", "2026-09-07", max_age_days=2) is False
