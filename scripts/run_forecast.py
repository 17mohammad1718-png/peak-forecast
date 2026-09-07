#!/usr/bin/env python3
"""Daily pipeline: collect -> engine -> audit audit -> data/forecast/latest.json"""
import json
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config, collector, market, seasonality
from src.calendar_lib import load_holidays
from src.engine import forecast_horizon, group_consecutive_peaks
from src.pricing_rules import apply_rules
from src.backtest import record_forecast_audit

def load_own_bookings():
    own_file = os.path.join(config.DATA, "own_bookings.json")
    own_nights = set()
    if os.path.exists(own_file):
        try:
            for b in json.load(open(own_file, encoding="utf-8")):
                d0 = datetime.date.fromisoformat(b["start"])
                for k in range(int(b.get("nights", 1))):
                    own_nights.add((d0 + datetime.timedelta(days=k)).isoformat())
        except Exception:
            pass
    return own_nights

def main():
    today = datetime.date.today()
    today_iso = today.isoformat()

    # 1. Collect live data
    try:
        collector.collect(today=today_iso)
    except Exception as e:
        print(f"Warning: collect step skipped/failed: {e}")

    # 2. Load context
    holidays = load_holidays()
    season = seasonality.build_curve()

    def market_fn(night_iso):
        return market.rival_state_for_night(config.DB_PATH, night_iso, today=today_iso)

    # 3. Engine forecast
    rows = forecast_horizon(today, config.HORIZON_DAYS, holidays, season, market_fn)
    own_nights = load_own_bookings()
    
    for o in rows:
        o["own_booked"] = o["date"] in own_nights
        o["lead_days"] = (datetime.date.fromisoformat(o["date"]) - today).days

    # 4. Streamlined rules check
    rows = apply_rules(rows, today=today)

    # 5. Audit record in DB
    try:
        record_forecast_audit(config.DB_PATH, rows, issued_at=today_iso)
    except Exception as e:
        print(f"Warning: forecast audit record failed: {e}")

    # 6. Group consecutive peak ranges
    peak_ranges = group_consecutive_peaks(rows)

    out = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "model_version": getattr(config, "MODEL_VERSION", "v2.0-jalali-market"),
        "horizon_days": config.HORIZON_DAYS,
        "consecutive_peak_ranges": peak_ranges,
        "nights": rows,
    }

    dest = os.path.join(config.DATA, "forecast")
    os.makedirs(dest, exist_ok=True)
    out_path = os.path.join(dest, "latest.json")
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"forecast written: {len(rows)} nights to {out_path}")
    if peak_ranges:
        print(f"found {len(peak_ranges)} consecutive peak range(s):")
        for r in peak_ranges:
            print(f"  🔥 {r['start']} تا {r['end']} ({r['nights_count']} شب {r['level']})")

if __name__ == "__main__":
    main()
