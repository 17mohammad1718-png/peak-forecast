import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.collector import init_db, ingest_live_snapshot
from src.market import rival_state_for_night

def _mk(db, snap):
    init_db(db)
    ingest_live_snapshot(db, snap, "2026-09-07")

def test_booked_share_excludes_own():
    db = os.path.join(tempfile.mkdtemp(), "t.db")
    _mk(db, [
        {"room_id": 1, "meta": {"own": False}, "nights": [
            {"date": "2026-09-10", "price": 3000000, "is_unavailable": True}]},
        {"room_id": 2, "meta": {"own": False}, "nights": [
            {"date": "2026-09-10", "price": 2500000, "is_unavailable": False}]},
        {"room_id": 9, "meta": {"own": True}, "nights": [
            {"date": "2026-09-10", "price": 2400000, "is_unavailable": True}]},
    ])
    st = rival_state_for_night(db, "2026-09-10")
    assert st["n_rivals"] == 2
    assert abs(st["booked_share"] - 0.5) < 1e-9
    # 2 rival prices [2.5M, 3.0M]: quantile index = round(q*(n-1)) -> p50 = 2.5M
    assert st["p50"] == 2500000 and st["p85"] == 3000000

def test_empty_night():
    db = os.path.join(tempfile.mkdtemp(), "t.db")
    init_db(db)
    st = rival_state_for_night(db, "2099-01-01")
    assert st["n_rivals"] == 0 and st["booked_share"] == 0.0
