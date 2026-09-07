import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pricing_rules import ladder_multiplier, apply_rules

def test_ladder_never_discounts_peak():
    assert ladder_multiplier(1, di=90) == 1.00
    assert ladder_multiplier(1, di=30) < 1.00

def test_far_out_premium():
    assert ladder_multiplier(60, di=30) > 1.0

def test_orphan_flag_and_price():
    nights = [
        {"date": "2026-10-01", "own_booked": True, "di": 30, "price": 2_000_000},
        {"date": "2026-10-02", "own_booked": False, "di": 30, "price": 2_000_000},
        {"date": "2026-10-03", "own_booked": True, "di": 30, "price": 2_000_000},
    ]
    out = apply_rules(nights, today=__import__("datetime").date(2026, 9, 7))
    assert out[1]["is_orphan"] and out[1]["price"] < 2_000_000
    assert out[1]["max_stay"] == 1

def test_min_stay_rules():
    nights = [
        {"date": "2026-10-01", "own_booked": False, "di": 97,
         "class_q": "Super-Peak", "price": 4_000_000},
        {"date": "2026-10-02", "own_booked": False, "di": 40,
         "class_q": "Normal", "price": 2_000_000},
    ]
    out = apply_rules(nights, today=__import__("datetime").date(2026, 9, 7))
    assert out[0]["min_stay"] == 3 and out[1]["min_stay"] == 1
