"""S(jm): Jalali monthly demand factor (experimental initial baseline).

Jalali month mapping (1=Farvardin, ..., 12=Esfand).
Flagged as "experimental" ("آزمایشی") until validated against empirical deal volume.
"""
import json
import os
import datetime
import jdatetime
from collections import Counter, defaultdict
from . import config

FULL_YEARS = (2022, 2023, 2024, 2025)
LAG_DAYS = 4

# Initial experimental Jalali seasonality curve for Mazandaran / Babolkenar
EXPERIMENTAL_JALALI_SEASONALITY = {
    1: 1.35,   # Farvardin (Nowruz Peak)
    2: 0.95,   # Ordibehesht (Spring Mid)
    3: 1.10,   # Khordad (Late Spring High)
    4: 1.15,   # Tir (Summer High)
    5: 1.25,   # Mordad (Summer Peak)
    6: 1.30,   # Shahrivar (Late Summer Peak)
    7: 0.90,   # Mehr (Autumn Mid)
    8: 0.85,   # Aban (Autumn Low-Mid)
    9: 0.75,   # Azar (Early Winter Low)
    10: 0.65,  # Dey (Winter Low)
    11: 0.65,  # Bahman (Winter Low)
    12: 0.75,  # Esfand (Pre-Nowruz Low-Mid)
}

def build_curve():
    """Build Jalali monthly demand curve. Fall back to experimental curve if corpus missing."""
    corpus_path = config.REVIEWS_CORPUS
    if not os.path.exists(corpus_path):
        return dict(EXPERIMENTAL_JALALI_SEASONALITY)

    try:
        corpus = json.load(open(corpus_path, encoding="utf-8"))
        bb = [r for r in corpus if r.get("city") == "بابلکنار" and r.get("created_at")]
        if not bb:
            return dict(EXPERIMENTAL_JALALI_SEASONALITY)

        by_room = defaultdict(list)
        for r in bb:
            by_room[r["room_id"]].append(r)

        counts = Counter()
        for r in bb:
            g_date = datetime.date.fromisoformat(r["created_at"][:10])
            g_date -= datetime.timedelta(days=LAG_DAYS)
            j_date = jdatetime.date.fromgregorian(date=g_date)
            if g_date.year in FULL_YEARS:
                counts[j_date.month] += 1

        if not counts:
            return dict(EXPERIMENTAL_JALALI_SEASONALITY)

        # Rate relative to average
        total_revs = sum(counts.values()) or 1
        avg_revs = total_revs / 12.0
        
        raw = {}
        for m in range(1, 13):
            val = counts[m] / avg_revs if avg_revs else 1.0
            raw[m] = max(0.5, min(1.5, val))

        # 3-month centered moving average on Jalali months
        sm = {}
        for m in range(1, 13):
            prev_m = raw[m - 1] if m > 1 else raw[12]
            next_m = raw[m + 1] if m < 12 else raw[1]
            sm[m] = round((prev_m + raw[m] + next_m) / 3, 3)

        return sm
    except Exception:
        return dict(EXPERIMENTAL_JALALI_SEASONALITY)

def factor_for_month(curve, jmonth):
    """Lookup seasonality factor for Jalali month (1..12)."""
    m = int(jmonth)
    return curve.get(m, EXPERIMENTAL_JALALI_SEASONALITY.get(m, 1.0))

if __name__ == "__main__":
    curve = build_curve()
    out = os.path.join(config.DATA, "seasonality.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(curve, open(out, "w"), indent=1)
    print("wrote Jalali seasonality curve to", out)
    for m in sorted(curve):
        print(f"  Jalali Month {m:2d}: {curve[m]}")
