#!/usr/bin/env python3
"""Daily pipeline: collect -> engine -> rules -> data/forecast/latest.json"""
import json
import os
import sys
import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config, collector, market, seasonality
from src.calendar_lib import load_holidays
from src.engine import forecast_horizon
from src.pricing_rules import apply_rules

def load_own_bookings():
    own_file = os.path.join(config.DATA, "own_bookings.json")
    own_nights = set()
    if os.path.exists(own_file):
        for b in json.load(open(own_file, encoding="utf-8")):
            d0 = datetime.date.fromisoformat(b["start"])
            for k in range(int(b.get("nights", 1))):
                own_nights.add((d0 + datetime.timedelta(days=k)).isoformat())
    return own_nights

def main():
    collector.collect()
    today = datetime.date.today()
    holidays = load_holidays()
    season = seasonality.build_curve()

    def market_fn(night_iso):
        return market.rival_state_for_night(config.DB_PATH, night_iso)

    rows = forecast_horizon(today, config.HORIZON_DAYS, holidays, season,
                            market_fn)
    own_nights = load_own_bookings()
    for o in rows:
        o["own_booked"] = o["date"] in own_nights
        o["lead_days"] = (datetime.date.fromisoformat(o["date"]) - today).days
    rows = apply_rules(rows, today=today)
    out = {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "anchor": config.ANCHOR_PRICE,
           "commission_factor": round(config.COMMISSION_FACTOR, 4),
           "horizon_days": config.HORIZON_DAYS, "nights": rows}
    dest = os.path.join(config.DATA, "forecast")
    os.makedirs(dest, exist_ok=True)
    json.dump(out, open(os.path.join(dest, "latest.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    peaks = [o for o in rows if o["class_"] == "Super-Peak"][:6]
    print(f"forecast written: {len(rows)} nights")
    for p in peaks:
        print(f"  peak {p['date']} ({p['dow']}) DI={p['di']} "
              f"price={p['price']:,} min_stay={p['min_stay']}")

if __name__ == "__main__":
    main()
