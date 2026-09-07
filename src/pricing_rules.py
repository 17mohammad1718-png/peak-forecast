"""Lead-time ladder, orphan nights, min-stay. Peak-freeze enforced.

Ladder thresholds are literature defaults until we accumulate >= 60 days of
our own collector history; then fit_ladder_from_cdf() replaces them from the
empirical first_seen CDF (monthly refit, printed for user review).
"""
LADDER = [            # (max_lead_inclusive, multiplier)
    (0, 0.80), (1, 0.80), (2, 0.85), (3, 0.90), (5, 0.95),
    (13, 1.00), (44, 1.00), (999, 1.20)      # far-out premium L>45
]

def ladder_multiplier(lead_days: int, di: float) -> float:
    if di >= 75:                              # never discount a peak early
        return 1.00 if lead_days <= 44 else 1.20
    for cap, m in LADDER:
        if lead_days <= cap:
            return m
    return 1.0

def apply_rules(nights: list, today=None) -> list:
    """nights: engine rows with date/di/price/class_q + own_booked flags.
    Adds lead ladder multiplier, orphan handling, min-stay suggestion."""
    from datetime import date as _date
    n = len(nights)
    today = today or _date.today()
    for i, o in enumerate(nights):
        prev_b = nights[i - 1]["own_booked"] if i > 0 else True
        next_b = nights[i + 1]["own_booked"] if i < n - 1 else True
        o["is_orphan"] = (not o.get("own_booked")) and prev_b and next_b
        o.setdefault("min_stay", 1)
        if o.get("class_q") == "Super-Peak" or (
                o.get("is_holiday") and o.get("is_bridge")):
            o["min_stay"] = 3
        elif o.get("class_q") == "Peak" or (
                o.get("is_weekend") and o.get("is_holiday")):
            o["min_stay"] = 2
    for o in nights:
        lead = (_date.fromisoformat(o["date"]) - today).days
        o["lead_days"] = max(0, lead)
        lm = ladder_multiplier(o["lead_days"], o["di"])
        o["ladder_mult"] = lm
        o["price"] = int(round(o["price"] * lm, -3))
        if o["is_orphan"]:
            o["price"] = int(round(o["price"] * 0.75, -3))
            o["max_stay"] = 1
            o["note"] = "orphan-fill"
    return nights

def fit_ladder_from_cdf(lead_cdf):
    """lead_cdf: [(lead, cum_share)] -> replacement LADDER rows."""
    def lead_at(share):
        for lead, s in lead_cdf:
            if s >= share:
                return lead
        return 3
    t75 = lead_at(0.25)
    t50 = lead_at(0.50)
    t25 = lead_at(0.75)
    return [(max(0, t75 - 1), 0.80), (max(1, t50 - 1), 0.90),
            (max(2, t25 - 1), 0.95), (44, 1.00), (999, 1.20)]
