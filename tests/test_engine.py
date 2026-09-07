import sys
import os
import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.engine import (
    compute_peak_demand,
    compute_suggested_price,
    forecast_night,
    group_consecutive_peaks,
)

FLAT_SEASON = {m: 1.0 for m in range(1, 13)}
EMPTY_RIVAL = {
    "n_rivals": 0, "n_with_price": 0, "coverage": 0.0, "p50": None,
    "confidence_label": "برآورد تقویمی با اطمینان پایین", "state": "unknown"
}

def test_peak_demand_classification():
    H = {}
    # Farvardin 1 holiday night
    d = datetime.date(2026, 3, 21) # 1405-01-01
    H["1405-01-01"] = ["Nowruz"]
    peak = compute_peak_demand(d, H, {1: 1.35}, EMPTY_RIVAL)
    assert peak["jmonth"] == 1
    assert peak["is_holiday"] is True
    assert peak["demand_level"] in ("پیک", "ابرپیک")
    assert "تعطیلی رسمی" in peak["reason"]

def test_holiday_factor_not_remultiplied_on_competitor_price():
    rival_market = {
        "n_rivals": 10, "n_with_price": 10, "coverage": 0.8,
        "p25": 2_500_000, "p50": 3_000_000, "p75": 3_500_000,
        "confidence_label": "بالا", "state": "ok"
    }
    peak_info = {"di": 85.0, "demand_level": "ابرپیک"}
    price_info = compute_suggested_price(peak_info, rival_market)
    
    # Suggested price should be based on rival P50 (3M) with limited quality adjustment (~3.3M),
    # NOT 3M * 1.8 holiday multiplier (5.4M)!
    assert price_info["suggested_price"] < 4_000_000
    assert abs(price_info["suggested_price"] - 3_300_000) <= 200_000

def test_consecutive_peaks_grouping():
    nights = [
        {"date": "2026-09-10", "jalali": "1405-06-19", "demand_level": "ابرپیک"},
        {"date": "2026-09-11", "jalali": "1405-06-20", "demand_level": "پیک"},
        {"date": "2026-09-12", "jalali": "1405-06-21", "demand_level": "عادی"},
        {"date": "2026-09-13", "jalali": "1405-06-22", "demand_level": "ابرپیک"},
    ]
    ranges = group_consecutive_peaks(nights)
    assert len(ranges) == 2
    assert ranges[0]["start"] == "1405-06-19"
    assert ranges[0]["end"] == "1405-06-20"
    assert ranges[0]["nights_count"] == 2
