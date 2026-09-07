"""Pricing rules & floor verification module.

Streamlined for v2.0 minimal flow:
- Price discounts / far-out markups are excluded from primary execution flow as requested.
- Preserves floor check and basic metadata for clean pipeline compatibility.
"""
from datetime import date as _date
from .floor import gross_floor

def ladder_multiplier(lead_days: int, di: float, informed: bool = True,
                      pickup_share: float = 0.0) -> float:
    """Neutral 1.00 multiplier (ladder discounting excluded from minimal flow)."""
    return 1.00

def apply_rules(nights: list, today=None) -> list:
    """Pass-through rule application: retains engine suggested price and checks economic cost floor."""
    today = today or _date.today()
    if isinstance(today, str):
        today = _date.fromisoformat(today)

    for o in nights:
        d = _date.fromisoformat(o["date"]) if isinstance(o["date"], str) else o["date"]
        o["lead_days"] = max(0, (d - today).days)
        o["ladder_mult"] = 1.00
        o["rival_state"] = o.get("rival", {}).get("state", "unknown")
        
        # Verify economic floor
        f = gross_floor(max(1, o.get("min_stay", 1)))
        o["floor_price"] = f
        if o.get("price", 0) < f:
            o["infeasible"] = True
            o["warning"] = f"کف اقتصادی ({f:,} تومان) بالاتر از قیمت پیشنهادی است"

    return nights

def fit_ladder_from_cdf(lead_cdf):
    """Stub helper for ladder fitting."""
    return [(0, 1.00), (999, 1.00)]
