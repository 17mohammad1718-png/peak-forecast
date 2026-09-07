"""Aggregate rival market state, price ranges, and live demand signals (pickup/pace).

- Market coverage calculated against total tracked market rivals (config.TOTAL_TRACKED_RIVALS).
- 3-day & 7-day pickup/reopening computed on paired observations of the SAME rivals.
- Market Price Range (P25, P50, P75) calculated from fresh bookable prices of similar rivals.
"""
import sqlite3
from datetime import date, timedelta
from . import config

def calculate_paired_pickup(db_path, night_iso, today, days_back=3):
    """Calculate pickup rate over days_back on the EXACT SAME set of rivals observed at both times."""
    t_date = date.fromisoformat(today) if isinstance(today, str) else today
    past_date = (t_date - timedelta(days=days_back)).isoformat()
    today_iso = t_date.isoformat()

    con = sqlite3.connect(db_path)
    query = """
    WITH snap_today AS (
        SELECT room_id, status, booked
        FROM nights n1
        WHERE night=? AND own=0 AND seen_on<=?
          AND seen_on=(SELECT MAX(seen_on) FROM nights n2 WHERE n2.room_id=n1.room_id AND n2.night=n1.night AND n2.seen_on<=?)
    ),
    snap_past AS (
        SELECT room_id, status, booked
        FROM nights n1
        WHERE night=? AND own=0 AND seen_on<=?
          AND seen_on=(SELECT MAX(seen_on) FROM nights n2 WHERE n2.room_id=n1.room_id AND n2.night=n1.night AND n2.seen_on<=?)
    )
    SELECT 
        t.room_id,
        p.status AS past_status, p.booked AS past_booked,
        t.status AS today_status, t.booked AS today_booked
    FROM snap_today t
    INNER JOIN snap_past p ON t.room_id = p.room_id
    """
    rows = con.execute(query, (night_iso, today_iso, today_iso, night_iso, past_date, past_date)).fetchall()
    con.close()

    if not rows:
        return {"paired_count": 0, "pickup_rate": 0.0, "pickups": 0, "reopenings": 0, "valid": False}

    pickups = 0
    reopenings = 0
    total_paired = len(rows)

    for rid, p_stat, p_booked, t_status, t_booked in rows:
        was_free = (p_stat == "free") or (p_booked == 0)
        is_free = (t_status == "free") or (t_booked == 0)
        if was_free and not is_free:
            pickups += 1
        elif not was_free and is_free:
            reopenings += 1

    net_pickup = pickups - reopenings
    pickup_rate = net_pickup / total_paired if total_paired > 0 else 0.0

    return {
        "paired_count": total_paired,
        "pickups": pickups,
        "reopenings": reopenings,
        "net_pickup": net_pickup,
        "pickup_rate": round(pickup_rate, 4),
        "valid": total_paired >= 5,
    }

def rival_state_for_night(db_path, night_iso, today=None):
    """Aggregate rival market state for night_iso as known on reference date today."""
    t_date = date.fromisoformat(today) if isinstance(today, str) else (today or date.today())
    today_iso = t_date.isoformat()

    total_market_rivals = getattr(config, "TOTAL_TRACKED_RIVALS", 35)

    if not db_path or not config.os.path.exists(db_path):
        return {
            "n_rivals": 0,
            "total_market": total_market_rivals,
            "coverage": 0.0,
            "booked_share": 0.0,
            "p20": None, "p25": None, "p50": None, "p75": None, "p85": None,
            "market_range": None,
            "state": "unknown",
            "confidence_label": "برآورد تقویمی با اطمینان پایین",
            "reason": "دیتابیس در دسترس نیست",
            "pickup_3d": None, "pickup_7d": None,
        }

    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT room_id, price, booked, status, fetched_at FROM nights WHERE night=? AND own=0 "
        "AND seen_on=(SELECT MAX(seen_on) FROM nights WHERE night=? AND seen_on<=?)",
        (night_iso, night_iso, today_iso),
    ).fetchall()
    con.close()

    if not rows:
        return {
            "n_rivals": 0,
            "total_market": total_market_rivals,
            "coverage": 0.0,
            "booked_share": 0.0,
            "p20": None, "p25": None, "p50": None, "p75": None, "p85": None,
            "market_range": None,
            "state": "unknown",
            "confidence_label": "برآورد تقویمی با اطمینان پایین",
            "reason": "بدون تقویم رقیب",
            "pickup_3d": None, "pickup_7d": None,
        }

    valid_prices = sorted(p for _, p, _, _, _ in rows if p and p > 500_000)

    def pct(q):
        if not valid_prices:
            return None
        idx = max(0, min(len(valid_prices) - 1, round(q * (len(valid_prices) - 1))))
        return valid_prices[idx]

    p20 = pct(0.20)
    p25 = pct(0.25)
    p50 = pct(0.50)
    p75 = pct(0.75)
    p85 = pct(0.85)

    booked_count = sum(
        1 for _, p, b, st, _ in rows
        if (b or st in ("unavailable_unknown", "confirmed_booking", "confirmed_block"))
        and (p50 is None or not p or p > p50 * 0.5)
    )

    n_present = len(rows)
    n_with_price = len(valid_prices)
    
    coverage = round(n_with_price / max(1, total_market_rivals), 2)
    booked_share = round(booked_count / max(1, n_present), 3)

    y, m, d = map(int, night_iso.split("-"))
    lead = (date(y, m, d) - t_date).days

    pickup_3d = calculate_paired_pickup(db_path, night_iso, t_date, days_back=3)
    pickup_7d = calculate_paired_pickup(db_path, night_iso, t_date, days_back=7)

    if coverage < 0.30 or lead > 105 or not valid_prices:
        state = "unknown"
        confidence_label = "برآورد تقویمی با اطمینان پایین"
        reason = "پوشش کم بازار یا افق دور"
    elif not pickup_3d["valid"] or not pickup_7d["valid"]:
        state = "low_confidence"
        confidence_label = "برآورد تقویمی با اطمینان پایین"
        reason = "تاریخچهٔ کافی برای محاسبهٔ سرعت پرشدن وجود ندارد"
    else:
        state = "ok"
        confidence_label = "بالا" if coverage >= 0.60 else "متوسط"
        reason = "اطلاعات بازار و سرعت پرشدن معتبر"

    market_range = None
    if p25 and p75:
        market_range = {"p25": int(p25), "p50": int(p50 or p25), "p75": int(p75)}

    return {
        "n_rivals": n_present,
        "n_with_price": n_with_price,
        "total_market": total_market_rivals,
        "coverage": coverage,
        "booked_share": booked_share,
        "p20": p20,
        "p25": p25,
        "p50": p50,
        "p75": p75,
        "p85": p85,
        "market_range": market_range,
        "state": state,
        "confidence_label": confidence_label,
        "reason": reason,
        "lead": lead,
        "pickup_3d": pickup_3d,
        "pickup_7d": pickup_7d,
    }
