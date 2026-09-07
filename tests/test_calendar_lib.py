import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.calendar_lib import day_type, load_holidays, bridge_info

H = load_holidays()

def test_nowruz_is_holiday():
    assert "1405-01-01" in H

def test_friday_is_weekend():
    jt = day_type(datetime.date(2026, 9, 11), H)   # Friday
    assert jt["is_weekend"] and jt["dow"] == "Fri"

def test_nowruz_day_real():
    assert day_type(datetime.date(2026, 3, 21), H)["is_holiday"]

def test_bridge_synthetic():
    # two single-day holidays with one normal day between -> bridge
    H2 = {"1405-07-10": ["a"], "1405-07-12": ["b"]}
    bi = bridge_info(datetime.date(2026, 10, 3), H2)   # 1405-07-11
    assert bi["is_bridge"] is True and bi["is_holiday"] is False

def test_holiday_day_is_not_bridge():
    bi = bridge_info(datetime.date(2026, 3, 22), H)    # 1405-01-02, itself holiday
    assert bi["is_bridge"] is False and bi["is_holiday"] is True
