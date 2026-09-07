"""Walk-forward backtest on radar_history.db + metrics (Brier, WAPE)."""
import sqlite3
from . import config

def brier(preds, outs):
    return sum((p - y) ** 2 for p, y in zip(preds, outs)) / len(preds)

def wape(pred_prices, actual_prices):
    num = sum(abs(a - b) for a, b in zip(pred_prices, actual_prices))
    den = sum(actual_prices) or 1
    return num / den

def _q(con, night_iso, upto=None):
    if upto:
        row = con.execute(
            "SELECT SUM(booked), COUNT(*) FROM days WHERE date=? AND last_seen<=? "
            "AND room_id!=?", (night_iso, upto, config.OWN_ROOM_ID)).fetchone()
    else:
        row = con.execute(
            "SELECT SUM(booked), COUNT(*) FROM days WHERE date=? AND room_id!=?",
            (night_iso, config.OWN_ROOM_ID)).fetchone()
    return (row[0] / row[1]) if row and row[1] else None

def historical_sellout_share(db_path, night_iso):
    con = sqlite3.connect(db_path)
    v = _q(con, night_iso)
    con.close()
    return v

def snapshot_state_at(db_path, snap_date, night_iso):
    """Rival booked-share for night_iso as known on snap_date.
    days.last_seen <= snap_date means the row existed by then (upsert semantics
    keep first status until changed; deleted/booked-again is captured by
    last_seen updates)."""
    con = sqlite3.connect(db_path)
    v = _q(con, night_iso, upto=snap_date)
    con.close()
    return v

def walk_forward(db_path, start_iso, end_iso, horizon=14):
    from datetime import date, timedelta
    d0, d1 = date.fromisoformat(start_iso), date.fromisoformat(end_iso)
    t = d0
    while t <= d1 - timedelta(days=horizon):
        for k in range(1, horizon + 1):
            night = (t + timedelta(days=k)).isoformat()
            pred = snapshot_state_at(db_path, t.isoformat(), night)
            act = historical_sellout_share(db_path, night)
            if pred is not None and act is not None:
                yield (t.isoformat(), night, pred, act)
        t += timedelta(days=7)
