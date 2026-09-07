import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.tg_digest import diff_msgs

def _mk(price, cls, orphan=False):
    return {"price": price, "class_": cls, "is_orphan": orphan, "di": 50,
            "date": "2026-10-01"}

def test_price_delta_and_new_peak():
    new = {"nights": [{"date": "2026-10-01", "price": 3_000_000,
                       "class_": "Super-Peak", "is_orphan": False, "di": 90}]}
    old = {"nights": [{"date": "2026-10-01", "price": 2_400_000,
                       "class_": "High", "is_orphan": False, "di": 60}]}
    msgs = diff_msgs(new, old)
    assert any("3,000,000" in m for m in msgs)
    assert any("پیک جدید" in m for m in msgs)

def test_small_change_ignored():
    new = {"nights": [dict(_mk(2_420_000, "Normal"), date="2026-10-01")]}
    old = {"nights": [dict(_mk(2_400_000, "Normal"), date="2026-10-01")]}
    assert diff_msgs(new, old) == []
