"""Pace layer challenger (v1.1) — SHADOW MODE, not wired into engine.

R_residual(D) compares observed rival booked-share at lead L with the POOLED
expected share at the SAME lead bucket + weekday tier (the prior). Promotion
requires BSS >= 5% vs calendar-only baseline on paired matured outcomes
(pre-declared). Until that test passes, engine keeps R=1.0.
"""
import math
import sqlite3
from datetime import date, timedelta
from . import config

BUCKETS = [(0, 2), (3, 5), (6, 10), (11, 20), (21, 45), (46, 120)]

def bucket_for(lead):
    for i, (lo, hi) in enumerate(BUCKETS):
        if lo <= lead <= hi:
            return i
    return len(BUCKETS) - 1

def pooled_prior(history_db):
    """{bucket: mean booked share} across rivals, censoring-aware:
    exclude rows whose first_seen == first snapshot date (start-censored)."""
    con = sqlite3.connect(history_db)
    first_snap = con.execute("SELECT MIN(first_seen) FROM days").fetchone()[0]
    rows = con.execute(
        "SELECT date, first_seen, status FROM days WHERE room_id!=? "
        "AND NOT (first_seen=?)", (config.OWN_ROOM_ID, first_snap)).fetchall()
    con.close()
    from collections import defaultdict
    by_b = defaultdict(lambda: [0, 0])
    for night, fs, status in rows:
        y, m, d = map(int, night.split("-"))
        fy, fm, fd = map(int, fs.split("-"))
        lead = (date(y, m, d) - date(fy, fm, fd)).days
        b = by_b[bucket_for(lead)]
        b[1] += 1
        if status == "booked":
            b[0] += 1
    return {k: (v[0] / v[1] if v[1] else 0.0, v[1]) for k, v in by_b.items()}

def challenger_report():
    """Shadow report: prior by lead bucket + sample sizes."""
    pri = pooled_prior(config.RADAR_HISTORY_DB)
    out = {}
    for k, (share, n) in sorted(pri.items()):
        lo, hi = BUCKETS[k]
        out[f"lead {lo}-{hi}d"] = {"prior_share": round(share, 3), "n": n}
    return out

if __name__ == "__main__":
    import json
    print(json.dumps(challenger_report(), indent=1))
