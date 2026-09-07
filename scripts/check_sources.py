#!/usr/bin/env python3
"""Exit 0 iff every external source is readable. One line per source."""
import sqlite3, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config

def main():
    ok = True
    n = sum(1 for f in os.listdir(config.RADAR_LIVE)
            if f[0].isdigit() and f.endswith(".json"))
    print(f"radar live calendars: {n} files"); ok &= n >= 30
    con = sqlite3.connect(config.RADAR_HISTORY_DB)
    (days,) = con.execute("SELECT COUNT(*) FROM days").fetchone()
    print(f"radar history db: {days} day-rows"); ok &= days > 4000
    corpus = json.load(open(config.REVIEWS_CORPUS, encoding="utf-8"))
    bb = sum(1 for r in corpus if r.get("city") == "بابلکنار")
    print(f"reviews corpus: {len(corpus)} total, {bb} babolkenar"); ok &= bb > 7000
    con = sqlite3.connect(config.HOLIDAYS_DB)
    (h,) = con.execute("SELECT COUNT(DISTINCT date) FROM events WHERE year=1405 AND is_holiday=1").fetchone()
    print(f"holidays 1405: {h} unique dates"); ok &= h >= 30
    print("RESULT:", "OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
