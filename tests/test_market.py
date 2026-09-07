import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.collector import init_db, ingest_live_snapshot
from src.market import rival_state_for_night, calculate_paired_pickup

def test_coverage_relative_to_total_market():
    db = os.path.join(tempfile.mkdtemp(), "t.db")
    init_db(db)
    # Ingest 1 rival
    snap = [{
        "room_id": 1,
        "meta": {"own": False},
        "nights": [{"date": "2026-09-10", "price": 2500000, "is_unavailable": False}]
    }]
    ingest_live_snapshot(db, snap, "2026-09-07")
    
    st = rival_state_for_night(db, "2026-09-10", today="2026-09-07")
    # Coverage should be 1 / 35 (~0.03), NOT 1.00 (100%)
    assert st["coverage"] < 0.10
    assert st["confidence_label"] == "برآورد تقویمی با اطمینان پایین"

def test_paired_pickup_calculation():
    db = os.path.join(tempfile.mkdtemp(), "t.db")
    init_db(db)
    
    # Day 1 snapshot (2026-09-04): 5 rivals free
    snap_past = [
        {"room_id": i, "meta": {"own": False}, "nights": [{"date": "2026-09-10", "price": 2000000, "is_unavailable": False}]}
        for i in range(1, 6)
    ]
    ingest_live_snapshot(db, snap_past, "2026-09-04")

    # Day 2 snapshot (2026-09-07): 2 of those 5 rivals flipped to unavailable
    snap_today = [
        {"room_id": i, "meta": {"own": False}, "nights": [{"date": "2026-09-10", "price": 2000000, "is_unavailable": (i <= 2)}]}
        for i in range(1, 6)
    ]
    ingest_live_snapshot(db, snap_today, "2026-09-07")

    p = calculate_paired_pickup(db, "2026-09-10", today="2026-09-07", days_back=3)
    assert p["valid"] is True
    assert p["paired_count"] == 5
    assert p["pickups"] == 2
    assert abs(p["pickup_rate"] - 0.40) < 1e-3
