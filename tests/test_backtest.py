import sys
import os
import tempfile
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.backtest import (
    record_forecast_audit,
    evaluate_historical_occupancy_accuracy,
    brier_score,
)

def test_brier_score():
    assert brier_score([1.0], [1]) == 0.0
    assert abs(brier_score([0.0], [1]) - 1.0) < 1e-9

def test_no_future_data_leakage_in_backtest():
    db = os.path.join(tempfile.mkdtemp(), "bt.db")
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE nights (room_id INT, night TEXT, seen_on TEXT, price INT, booked INT, own INT, status TEXT, fetched_at TEXT)")
    con.execute("INSERT INTO nights VALUES (1, '2026-09-01', '2026-09-01', 2000000, 1, 0, 'confirmed_booking', '2026-09-01')")
    con.execute("INSERT INTO nights VALUES (1, '2026-09-20', '2026-09-07', 2000000, 0, 0, 'free', '2026-09-07')")
    con.commit()
    con.close()

    # Record forecast issued on 2026-08-31 for night 2026-09-01
    record_forecast_audit(db, [{"date": "2026-09-01", "di": 80.0, "demand_level": "ابرپیک", "suggested_price": 2500000, "confidence": "بالا"}], issued_at="2026-08-31")
    # Record forecast issued on 2026-09-07 for future night 2026-09-20
    record_forecast_audit(db, [{"date": "2026-09-20", "di": 40.0, "demand_level": "عادی", "suggested_price": 2000000, "confidence": "متوسط"}], issued_at="2026-09-07")

    # Evaluate on today = 2026-09-07
    res = evaluate_historical_occupancy_accuracy(db, today="2026-09-07")
    # Only 2026-09-01 has night <= today (2026-09-07)
    assert res["pairs"] == 1
