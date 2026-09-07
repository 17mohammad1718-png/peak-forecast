import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.collector import init_db, ingest_live_snapshot

def test_ingest_idempotent():
    db = os.path.join(tempfile.mkdtemp(), "t.db")
    init_db(db)
    snap = [{"room_id": 111, "meta": {"own": True},
             "nights": [{"date": "2026-09-10", "price": 2400000,
                         "is_unavailable": True}]}]
    ingest_live_snapshot(db, snap, "2026-09-07")
    ingest_live_snapshot(db, snap, "2026-09-07")
    con = sqlite3.connect(db)
    n, d = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT room_id) FROM nights").fetchone()
    assert (n, d) == (1, 1)

def test_own_flag_persisted():
    db = os.path.join(tempfile.mkdtemp(), "t.db")
    init_db(db)
    snap = [{"room_id": 111, "meta": {"own": True},
             "nights": [{"date": "2026-09-10", "price": 2400000,
                         "is_unavailable": True}]}]
    ingest_live_snapshot(db, snap, "2026-09-07")
    con = sqlite3.connect(db)
    (own,) = con.execute("SELECT own FROM nights LIMIT 1").fetchone()
    assert own == 1
