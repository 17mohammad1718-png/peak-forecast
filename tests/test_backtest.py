import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.backtest import brier, wape

def test_brier_perfect_and_worst():
    assert brier([1.0], [1]) == 0.0
    assert abs(brier([0.0], [1]) - 1.0) < 1e-9

def test_wape_zero_and_full():
    assert wape([100, 200], [100, 200]) == 0.0
    assert abs(wape([100, 200], [200, 400]) - 0.5) < 1e-9
