"""Year heatmap data builder (v2) - NO review-count curve.

Three layers per Gregorian day:
  1. holiday tier (official holidays from persian_holiday.db + bridges)
  2. real rival booking share for dates we have data (radar_history.db)
  3. month tier (Mazandaran consensus from Jajiga mag + local knowledge):
     Farvardin peak(Nowruz), Ordibehesht mid, Khordad high (end-of-spring
     trips), Tir-Mordad-Shahrivar high (Caspian summer), Mehr-Aban mid-high
     (fall-leaf), Azar mid, Dey-Bahman low (winter), Esfand low-mid.
Output: data/yearmap-<year>.json -> [{date, dow, tier 0..100, flags}]
"""
import json
import os
import datetime
import jdatetime
import sqlite3
from . import config
from .calendar_lib import load_holidays, day_type, bridge_info

# month base tier 0..100 (Mazandaran Caspian consensus, Jajiga mag aligned)
MONTH_TIER = {1: 85, 2: 45, 3: 60, 4: 70, 5: 80, 6: 90,
              7: 80, 8: 75, 9: 45, 10: 25, 11: 18, 12: 25}
DOW_TIER = {0: 40, 1: 38, 2: 55, 3: 78, 4: 70, 5: 45, 6: 42}
# Mon Tue Wed Thu Fri Sat Sun (from REAL rival bookings + price premium)

def month_tier(jm):
    return MONTH_TIER.get(int(jm), 40)

def day_tier(d, holidays, rival_share=None):
    dt = day_type(d, holidays)
    bi = bridge_info(d, holidays)
    t = max(month_tier(dt["jmonth"]) * 0.62, DOW_TIER[d.weekday()] * 0.62)
    # blend: month macro + weekly rhythm
    t = 0.55 * month_tier(dt["jmonth"]) + 0.45 * DOW_TIER[d.weekday()]
    if bi["is_bridge"]:
        t += 18
    if dt["is_holiday"]:
        t += 25
        if dt["dow"] in ("Thu", "Fri"):
            t += 12
    if rival_share is not None:
        t = 0.5 * t + 0.5 * (rival_share * 100)
    return min(100.0, t), dt, bi

def _rival_shares():
    """{night_iso: booked_share} from radar_history (real bookings, rivals only)."""
    try:
        con = sqlite3.connect(config.RADAR_HISTORY_DB)
        rows = con.execute(
            "SELECT date, SUM(CASE WHEN status='booked' THEN 1 ELSE 0 END), "
            "COUNT(*) FROM days WHERE room_id!=? GROUP BY date",
            (config.OWN_ROOM_ID,)).fetchall()
        con.close()
        return {d: b / n for d, b, n in rows if n}
    except Exception:
        return {}

def build_year(jy):
    """All days of Jalali year jy as list of dicts."""
    holidays = load_holidays()
    rival = _rival_shares()
    out = []
    j = jdatetime.date(jy, 1, 1)
    while j.year == jy:
        d = j.togregorian()
        rs = rival.get(d.isoformat())
        t, dt, bi = day_tier(d, holidays, rs)
        out.append({
            "date": d.isoformat(), "jalali": dt["jalali"],
            "jyear": jy, "dow": dt["dow"], "jmonth": dt["jmonth"],
            "tier": round(t), "is_holiday": dt["is_holiday"],
            "is_bridge": bi["is_bridge"], "is_weekend": dt["is_weekend"],
            "rival_share": round(rs * 100) if rs is not None else None,
            "has_rival_data": rs is not None,
        })
        j = j + jdatetime.timedelta(days=1)
    return out

def main():
    os.makedirs(config.DATA, exist_ok=True)
    for jy in (1405, 1406):
        rows = build_year(jy)
        p = os.path.join(config.DATA, f"yearmap-{jy}.json")
        json.dump(rows, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        hi = [r for r in rows if r["tier"] >= 80]
        print(f"yearmap-{jy}: {len(rows)} days, {len(hi)} hot days "
              f"(>=80), wrote {p}")

if __name__ == "__main__":
    main()
