import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pricing_rules import ladder_multiplier, apply_rules

def test_ladder_multiplier_neutral():
    # Streamlined flow keeps ladder multiplier neutral
    assert ladder_multiplier(1, di=90) == 1.00
    assert ladder_multiplier(1, di=30) == 1.00

def test_apply_rules_economic_floor():
    nights = [
        {"date": "2026-10-01", "price": 1_000_000, "di": 30},
        {"date": "2026-10-02", "price": 3_500_000, "di": 70},
    ]
    out = apply_rules(nights, today=__import__("datetime").date(2026, 9, 7))
    assert out[0].get("infeasible") is True
    assert "کف اقتصادی" in out[0].get("warning", "")
    assert out[1].get("infeasible") is not True
