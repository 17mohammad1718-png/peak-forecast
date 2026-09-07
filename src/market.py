"""Aggregate rival market state for future nights (own cabin excluded)."""
import sqlite3
from . import config

def rival_state_for_night(db_path, night_iso):
    """Latest-seen snapshot state for one night, own rows excluded."""
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT room_id, price, booked FROM nights WHERE night=? AND own=0 "
        "AND seen_on=(SELECT MAX(seen_on) FROM nights WHERE night=?)",
        (night_iso, night_iso)).fetchall()
    con.close()
    if not rows:
        return {"n_rivals": 0, "booked_share": 0.0,
                "p20": None, "p50": None, "p85": None}
    prices = sorted(p for _, p, _ in rows if p)
    booked = sum(b for _, _, b in rows)

    def pct(q):
        if not prices:
            return None
        i = max(0, min(len(prices) - 1, round(q * (len(prices) - 1))))
        return prices[i]

    return {"n_rivals": len(rows), "booked_share": booked / len(rows),
            "p20": pct(0.20), "p50": pct(0.50), "p85": pct(0.85)}
