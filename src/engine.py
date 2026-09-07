"""Peak Demand Engine and Pricing Engine (v2.0-jalali-market).

1. Peak Demand Engine:
   - Base demand built from Jalali month, day of week, holidays, holiday eves, and bridges.
   - Market pickup signal (3d/7d paired) adjusts peak intensity.
   - Outputs: DI (Demand Intensity 0..100), demand_level (عادی, پرتقاضا, پیک, ابرپیک),
     confidence (بالا, متوسط, برآورد تقویمی با اطمینان پایین), and explainable Persian reason.

2. Price Engine:
   - Starts from median price of similar fresh rivals (market_p50).
   - DOES NOT re-multiply holiday factors on rival prices (since rivals already price for holidays).
   - Applies limited, explainable adjustment for chalet quality & demand intensity.
   - Calculates own net payout after commission (config.COMMISSION_OWN).
   - Enforces economic cost floor (gross_floor); warns if floor > market price.
"""
import datetime
import math
from . import config
from .calendar_lib import day_type, bridge_info
from .seasonality import factor_for_month
from .floor import gross_floor

# Day-of-week demand multipliers (Mon=0 ... Sun=6)
WEEKDAY_W = {0: 0.90, 1: 0.88, 2: 1.05, 3: 1.30, 4: 1.12, 5: 0.90, 6: 0.90}

# Anchor multiplier mapping for fallback anchor pricing
ANCHORS = [(0, 0.85), (35, 1.00), (65, 1.35), (85, 1.80), (100, 2.50)]

def di_to_multiplier(di: float) -> float:
    """Map DI [0,100] to fallback anchor price multiplier [0.85, 2.50]."""
    for (x0, y0), (x1, y1) in zip(ANCHORS, ANCHORS[1:]):
        if x0 <= di <= x1:
            return y0 + (y1 - y0) * (di - x0) / (x1 - x0)
    return ANCHORS[-1][1]

def _di_from_mdf(mdf: float, mdf_min: float = 0.55, mdf_max: float = 2.05) -> float:
    """Log-scale mapping of Market Demand Factor (MDF) to DI [0..100]."""
    x = math.log(max(0.05, mdf))
    lo, hi = math.log(mdf_min), math.log(mdf_max)
    return max(0.0, min(100.0, 100.0 * (x - lo) / (hi - lo)))

def compute_peak_demand(d, holidays, season, market_info) -> dict:
    """Peak Demand Engine: compute demand intensity, level, reason, confidence."""
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d)

    dt = day_type(d, holidays)
    bi = bridge_info(d, holidays)

    # 1. Jalali monthly seasonality S (1..12)
    jmonth = dt["jmonth"]
    S = factor_for_month(season, jmonth)

    # 2. Day of week factor W
    W = WEEKDAY_W[d.weekday()]

    # 3. Holiday, Eve of holiday, and Bridge factor H
    H = 1.0
    reasons = []

    # Reason component: Month
    reasons.append(f"ماه شمسی {jmonth} (آزمایشی)")

    if dt["is_holiday"]:
        H *= 1.6 if dt["dow"] in ("Thu", "Fri") else 1.45
        reasons.append("تعطیلی رسمی")
    elif dt["is_eve"]:
        H *= 1.18
        reasons.append("شب قبل از تعطیلی")

    if bi["is_bridge"]:
        H *= 1.22
        reasons.append("بین دو تعطیلی (پسران/پل)")

    if bi.get("is_consecutive"):
        H *= 1.12
        reasons.append("تعطیلات پیوسته")

    if dt["is_weekend"] and not dt["is_holiday"]:
        reasons.append("آخر هفته")

    # 4. Live market demand velocity signal R (3d/7d pickup)
    R = 1.0
    pickup_3d = market_info.get("pickup_3d") or {}
    if pickup_3d.get("valid"):
        rate = pickup_3d.get("pickup_rate", 0.0)
        if rate > 0.05:
            R += min(0.20, rate * 0.8)
            reasons.append(f"افزایش رزرو رقبا (+{int(rate*100)}%)")
        elif rate < -0.05:
            R -= min(0.15, abs(rate) * 0.5)
            reasons.append("کاهش تقاضای زنده")

    mdf = S * W * H * R
    di = _di_from_mdf(mdf)

    # Demand level classification
    if di < 40:
        class_en = "Normal"
        demand_level = "عادی"
    elif di < 60:
        class_en = "High"
        demand_level = "پرتقاضا"
    elif di < 75:
        class_en = "Peak"
        demand_level = "پیک"
    else:
        class_en = "Super-Peak"
        demand_level = "ابرپیک"

    confidence = market_info.get("confidence_label", "برآورد تقویمی با اطمینان پایین")
    reason_str = " + ".join(reasons)

    return {
        "date": d.isoformat(),
        "dow": dt["dow"],
        "dow_fa": dt["dow_fa"],
        "jalali": dt["jalali"],
        "jmonth": jmonth,
        "is_holiday": dt["is_holiday"],
        "is_eve": dt["is_eve"],
        "is_bridge": bi["is_bridge"],
        "is_weekend": dt["is_weekend"],
        "S": round(S, 3),
        "W": round(W, 3),
        "H": round(H, 3),
        "R": round(R, 3),
        "mdf": round(mdf, 3),
        "di": round(di, 1),
        "class_": class_en,
        "demand_level": demand_level,
        "reason": reason_str,
        "confidence": confidence,
    }

def compute_suggested_price(peak_info: dict, market_info: dict, stay_nights: int = 1) -> dict:
    """Price Engine: compute market range, chalet suggested price, net payout, and cost floor check."""
    di = peak_info["di"]
    market_range = market_info.get("market_range")
    p50 = market_info.get("p50")

    # Starting point: Median price of similar rivals
    if p50 and market_info.get("state") != "unknown":
        base_market_price = float(p50)
        # Apply ONLY limited quality/demand-intensity adjustment to competitor price
        # (do NOT multiply holiday factor onto rival price because rival price already reflects holiday rate)
        quality_adj = 1.00
        if di >= 75:
            quality_adj = 1.10
        elif di >= 60:
            quality_adj = 1.05
        elif di < 35:
            quality_adj = 0.95
        suggested_price = int(round(base_market_price * quality_adj, -4))
    else:
        # Fallback to anchor pricing when no fresh market prices exist
        anchor = config.ANCHOR_PRICE
        mult = di_to_multiplier(di)
        suggested_price = int(round(anchor * mult, -4))

    # Calculate net payout for own chalet
    net_payout = int(round(suggested_price * (1.0 - config.COMMISSION_OWN), -3))

    # Economic cost floor check
    floor_price = gross_floor(stay_nights)
    infeasible = suggested_price < floor_price
    warning = ""
    if infeasible:
        warning = f"کف اقتصادی ({floor_price:,} تومان) بالاتر از قیمت پیشنهادی بازار است"

    return {
        "market_range": market_range,
        "p25": market_info.get("p25"),
        "p50": market_info.get("p50"),
        "p75": market_info.get("p75"),
        "valid_rival_count": market_info.get("n_with_price", 0),
        "suggested_price": suggested_price,
        "price": suggested_price,  # backwards compatibility
        "net_payout": net_payout,
        "floor_price": floor_price,
        "infeasible": infeasible,
        "warning": warning,
    }

def forecast_night(d, holidays, season, market_info) -> dict:
    """Combined single night forecast combining Peak Engine and Price Engine."""
    peak = compute_peak_demand(d, holidays, season, market_info)
    price_info = compute_suggested_price(peak, market_info)
    
    out = dict(peak)
    out.update(price_info)
    out["rival"] = market_info
    out["model_version"] = getattr(config, "MODEL_VERSION", "v2.0-jalali-market")
    return out

def forecast_horizon(start, days, holidays, season, market_fn):
    """Forecast consecutive nights over the given horizon."""
    if isinstance(start, str):
        start = datetime.date.fromisoformat(start)

    out = []
    for i in range(days):
        d = start + datetime.timedelta(days=i)
        m_info = market_fn(d.isoformat())
        out.append(forecast_night(d, holidays, season, m_info))

    return out

def group_consecutive_peaks(nights: list) -> list:
    """Group consecutive Peak / Super-Peak nights into display ranges.
    
    Returns list of dicts:
      [{"start": "1405-01-01", "end": "1405-01-04", "nights_count": 4, "level": "ابرپیک", "dates": [...]}]
    """
    peaks = []
    current_group = []

    for n in nights:
        is_peak = n.get("class_") in ("Peak", "Super-Peak") or n.get("demand_level") in ("پیک", "ابرپیک")
        if is_peak:
            current_group.append(n)
        else:
            if current_group:
                peaks.append(current_group)
                current_group = []
    if current_group:
        peaks.append(current_group)

    ranges = []
    for g in peaks:
        start_j = g[0].get("jalali") or g[0].get("date")
        end_j = g[-1].get("jalali") or g[-1].get("date")
        highest_level = "ابرپیک" if any(x.get("demand_level") == "ابرپیک" for x in g) else "پیک"
        ranges.append({
            "start": start_j,
            "end": end_j,
            "start_iso": g[0]["date"],
            "end_iso": g[-1]["date"],
            "nights_count": len(g),
            "level": highest_level,
            "dates": [x["date"] for x in g],
        })

    return ranges
