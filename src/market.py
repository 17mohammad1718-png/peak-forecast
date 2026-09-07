"""Aggregate rival market state for future nights (own cabin excluded).

v1.1: adds observation state — a night whose rival calendars are not yet
opened/uninformative is UNKNOWN evidence, not observed zero demand.
"""
import sqlite3
from . import config

def rival_state_for_night(db_path, night_iso, today=None):
    """Latest-seen snapshot state for one night, own rows excluded.
    state: 'ok' (informative) | 'unknown' (no/poor coverage)."""
    from datetime import date
    today = today or date.today()
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT room_id, price, booked FROM nights WHERE night=? AND own=0 "
        "AND seen_on=(SELECT MAX(seen_on) FROM nights WHERE night=?)",
        (night_iso, night_iso)).fetchall()
    con.close()
    if not rows:
        return {"n_rivals": 0, "booked_share": 0.0, "p20": None, "p50": None,
                "p85": None, "state": "unknown", "reason": "no-calendars"}
    prices = sorted(p for _, p, _ in rows if p)

    def pct(q):
        if not prices:
            return None
        i = max(0, min(len(prices) - 1, round(q * (len(prices) - 1))))
        return prices[i]

    # v1.1: a 'booked' row priced <=50% of the night's rival median is almost
    # always a host block / closed calendar (verified: room 3181918 blocks all
    # Dec at 700-950K since Aug). Exclude from demand share; keep its price.
    med = pct(0.50)
    booked = sum(1 for _, p, b in rows if b and (med is None or
                                                 not p or p > med * 0.5))

    # Coverage heuristic: informative when (a) at least 60% of rivals have
    # any price for this night AND (b) lead <= 105 days (calendar horizon).
    n_with_price = len(prices)
    y, m, d = map(int, night_iso.split("-"))
    lead = (date(y, m, d) - today).days
    coverage = n_with_price / len(rows)
    if coverage < 0.6 or lead > 105:
        return {"n_rivals": len(rows), "booked_share": booked / len(rows),
                "p20": pct(0.20), "p50": pct(0.50), "p85": pct(0.85),
                "state": "unknown",
                "reason": ("low-coverage" if coverage < 0.6
                           else "beyond-horizon"),
                "coverage": round(coverage, 2), "lead": lead}
    if lead > 75 and booked / len(rows) < 0.02:
        # calendars open but zero pickup = thin evidence, not zero demand
        return {"n_rivals": len(rows), "booked_share": booked / len(rows),
                "p20": pct(0.20), "p50": pct(0.50), "p85": pct(0.85),
                "state": "unknown", "reason": "no-pickup-thin",
                "coverage": round(coverage, 2), "lead": lead}
    return {"n_rivals": len(rows), "booked_share": booked / len(rows),
            "p20": pct(0.20), "p50": pct(0.50), "p85": pct(0.85),
            "state": "ok", "coverage": round(coverage, 2), "lead": lead}
