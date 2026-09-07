"""MDF engine v1: MDF(D) = S * W * H (R slot present, fixed 1.0 in v1).

Weights fitted from OUR market (2026-09-07 live medians):
Wed=135%, Thu=143% of week median; Fri ~= week median.
DI mapping: log-scale into [0,100] over MDF range [0.55, 2.05].
"""
import datetime
import math
from . import config
from .calendar_lib import day_type, bridge_info

WEEKDAY_W = {0: 0.90, 1: 0.88, 2: 1.05, 3: 1.30, 4: 1.12, 5: 0.90, 6: 0.90}
# Mon Tue Wed  Thu  Fri  Sat  Sun
# Fitted from REAL rival booking shares (radar_history, 2026-08-08..09-07):
# Thu 18% > Fri 15% > others ~14%; blended with rival price premium (Wed 135%).

ANCHORS = [(0, 0.85), (35, 1.00), (65, 1.35), (85, 1.80), (100, 2.50)]

def di_to_multiplier(di: float) -> float:
    for (x0, y0), (x1, y1) in zip(ANCHORS, ANCHORS[1:]):
        if x0 <= di <= x1:
            return y0 + (y1 - y0) * (di - x0) / (x1 - x0)
    return ANCHORS[-1][1]

def commission_price(rival_price: float) -> float:
    """Rival display price -> our gross price with equal net."""
    return round(rival_price * config.COMMISSION_FACTOR, -3)

def _di_from_mdf(mdf, mdf_min=0.55, mdf_max=2.05):
    x = math.log(max(0.05, mdf))
    lo, hi = math.log(mdf_min), math.log(mdf_max)
    return max(0.0, min(100.0, 100 * (x - lo) / (hi - lo)))

def forecast_night(d, holidays, season, rival, quantiles=None) -> dict:
    dt = day_type(d, holidays)
    bi = bridge_info(d, holidays)
    S = season.get(dt["jmonth"], 1.0)
    W = WEEKDAY_W[d.weekday()]
    H = 1.0
    if bi["is_bridge"]:
        H = 1.25
    if dt["is_holiday"]:
        H = 1.5 if dt["dow"] not in ("Thu", "Fri") else 1.8
    R = 1.0                                   # v1: pace layer arrives month 2
    mdf = S * W * H * R
    di = _di_from_mdf(mdf)
    # v1.1: ABSOLUTE classes (weak month may legitimately have zero peaks);
    # relative rank becomes a separate badge in horizon overlay; holiday
    # importance becomes a badge, NOT a class override.
    class_ = ("Normal" if di < 40 else "High" if di < 60
              else "Peak" if di < 75 else "Super-Peak")
    important_holiday = dt["is_holiday"] and dt["dow"] in ("Thu", "Fri")
    mult = di_to_multiplier(di)
    price = round(config.ANCHOR_PRICE * mult, -4)
    # v1.1: unknown rival horizon -> calendar-prior fallback; NO rival clamp,
    # NO unsupported far-out premium (missing info is not premium evidence).
    state = rival.get("state", "unknown")
    if state == "ok":
        floor_d = max(config.HARD_FLOOR, commission_price(rival["p20"] * 0.9))
        ceil_d = commission_price(rival["p85"])
        price = max(floor_d, min(ceil_d, price))
    else:
        # shrink toward anchor by coverage: log(P/A) = c * log(P_cal/A),
        # c = coverage-based confidence (0.6 -> 0.6x the calendar premium)
        c = max(0.0, min(1.0, rival.get("coverage", 0.0)))
        if price > config.ANCHOR_PRICE and c > 0:
            price = round(config.ANCHOR_PRICE *
                          (price / config.ANCHOR_PRICE) ** c, -3)
        # else: keep anchor-priced calendar value as-is
        # far-out premium only with informative calendars (handled by caller
        # via ladder; engine does not apply it on unknown nights)
    return {"date": d.isoformat(), "dow": dt["dow"], "jalali": dt["jalali"],
            "jmonth": dt["jmonth"], "is_holiday": dt["is_holiday"],
            "is_bridge": bi["is_bridge"], "is_weekend": dt["is_weekend"],
            "important_holiday": important_holiday,
            "S": round(S, 3), "W": W, "H": H, "R": R, "mdf": round(mdf, 3),
            "di": round(di, 1), "class_": class_, "multiplier": round(mult, 3),
            "price": price, "rival": rival}

def forecast_horizon(start, days, holidays, season, market_fn):
    out = []
    for i in range(days):
        d = start + datetime.timedelta(days=i)
        out.append(forecast_night(d, holidays, season, market_fn(d.isoformat())))
    dis = sorted(o["di"] for o in out)

    def q(p):
        i = max(0, min(len(dis) - 1, round(p * (len(dis) - 1))))
        return dis[i]

    p50, p80, p95 = q(0.50), q(0.80), q(0.95)
    for o in out:
        # class stays ABSOLUTE; percentile rank shown as badge (topX%)
        if o["di"] >= p95:
            o["rank_badge"] = "top 5%"
        elif o["di"] >= p80:
            o["rank_badge"] = "top 20%"
        elif o["di"] >= p50:
            o["rank_badge"] = "top 50%"
        else:
            o["rank_badge"] = None
        o["qcut"] = {"p50": p50, "p80": p80, "p95": p95}
    return out
