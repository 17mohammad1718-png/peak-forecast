"""Stay-length contribution floor (v1.1).

gross_floor(n) = (C_turn/n + C_night + contribution) / (1 - commission)
C_turn: cleaning/laundry/labor/travel per reservation
C_night: utilities/consumables per occupied night
contribution: minimum per-night contribution to fixed costs (host target)

Defaults are PLACEHOLDERS until the host worksheet confirms them (docs task).
"""
from . import config

DEFAULTS = {
    "C_turn": 300_000,       # toman per reservation (placeholder)
    "C_night": 150_000,      # toman per occupied night (placeholder)
    "contribution": 800_000, # min per-night contribution to fixed (placeholder)
}

def gross_floor(stay_nights: int = 1, C_turn=None, C_night=None,
                contribution=None) -> int:
    n = max(1, int(stay_nights))
    ct = DEFAULTS["C_turn"] if C_turn is None else C_turn
    cn = DEFAULTS["C_night"] if C_night is None else C_night
    cb = DEFAULTS["contribution"] if contribution is None else contribution
    need_net = ct / n + cn + cb
    return int(round(need_net / (1 - config.COMMISSION_OWN), -3))

def floor_check(price: int, stay_nights: int = 1) -> dict:
    f = gross_floor(stay_nights)
    return {"floor": f, "price": price, "clears": price >= f,
            "shortfall": max(0, f - price)}
