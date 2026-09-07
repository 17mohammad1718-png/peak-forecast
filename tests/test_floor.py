import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.floor import gross_floor, floor_check

def test_floor_decreases_with_stay_length():
    f1 = gross_floor(1)
    f3 = gross_floor(3)
    assert f3 < f1, "longer stays amortize turnover -> lower floor"

def test_floor_check():
    f1 = gross_floor(1)
    r = floor_check(f1 + 10_000, stay_nights=1)
    assert r["clears"] is True
    r2 = floor_check(f1 - 10_000, stay_nights=1)
    assert r2["clears"] is False and r2["shortfall"] > 0
