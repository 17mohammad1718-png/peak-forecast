"""S(m): monthly demand factor from Babolkenar review velocity, normalized.

Normalization: reviews per month (2022-2025) divided by active-listing proxy
(rooms whose first review predates that month), shifted -4 days for review
lag, mapped to [0.6, 1.4], smoothed with a 3-month centered window.
"""
import json
import os
import datetime
from collections import Counter, defaultdict
from . import config

FULL_YEARS = (2022, 2023, 2024, 2025)
LAG_DAYS = 4

def build_curve():
    corpus = json.load(open(config.REVIEWS_CORPUS, encoding="utf-8"))
    bb = [r for r in corpus if r.get("city") == "بابلکنار" and r.get("created_at")]
    by_room = defaultdict(list)
    for r in bb:
        by_room[r["room_id"]].append(r)
    month_first = {rid: min(x["created_at"][:7] for x in revs)
                   for rid, revs in by_room.items()}
    counts = Counter()
    for r in bb:
        d = datetime.date.fromisoformat(r["created_at"][:10])
        d -= datetime.timedelta(days=LAG_DAYS)
        if d.year in FULL_YEARS:
            counts[d.month] += 1
    # supply proxy per month: use 2023 as reference year
    supply = {m: sum(1 for first in month_first.values() if first <= f"2023-{m:02d}")
              for m in range(1, 13)}
    rate = {m: counts[m] / max(1, supply[m]) for m in range(1, 13)}
    lo, hi = min(rate.values()), max(rate.values())
    raw = {m: 0.6 + 0.8 * (rate[m] - lo) / (hi - lo) for m in rate}
    sm = {}
    for m in range(1, 13):
        prev_m = raw[m - 1] if m > 1 else raw[12]
        next_m = raw[m + 1] if m < 12 else raw[1]
        sm[m] = round((prev_m + raw[m] + next_m) / 3, 3)
    return sm

def factor_for_month(curve, month):
    return curve[int(month)]

if __name__ == "__main__":
    curve = build_curve()
    out = os.path.join(config.DATA, "seasonality.json")
    json.dump(curve, open(out, "w"), indent=1)
    print("wrote", out)
    for m in sorted(curve):
        print(f"  month {m:2d}: {curve[m]}")
