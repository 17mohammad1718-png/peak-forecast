import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.seasonality import build_curve, factor_for_month

def test_curve_shape():
    curve = build_curve()
    assert set(curve) == set(range(1, 13))
    assert all(0.6 <= v <= 1.4 for v in curve.values())
    peak = max(curve, key=curve.get)
    assert peak in (8, 9), f"peak month {peak}"
    assert curve[2] < 0.85, f"Feb too high: {curve[2]}"

def test_factor_lookup():
    curve = build_curve()
    assert isinstance(factor_for_month(curve, 9), float)
