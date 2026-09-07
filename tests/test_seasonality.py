import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.seasonality import build_curve, factor_for_month

def test_jalali_seasonality_mapping():
    curve = build_curve()
    assert set(curve.keys()) == set(range(1, 13))
    # Jalali Month 1 (Farvardin) is Nowruz Peak
    farvardin = factor_for_month(curve, 1)
    # Jalali Month 10 (Dey) is Winter Low
    dey = factor_for_month(curve, 10)
    assert farvardin > 1.20, f"Farvardin should be peak: {farvardin}"
    assert dey < 0.80, f"Dey should be low winter: {dey}"
    assert farvardin > dey

def test_fallback_when_corpus_missing():
    # Calling build_curve when corpus is missing should return experimental factors without throwing FileNotFoundError
    curve = build_curve()
    assert isinstance(curve, dict)
    assert 1 in curve
    assert curve[1] >= 1.2
