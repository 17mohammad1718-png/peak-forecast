#!/usr/bin/env python3
"""Walk-forward backtest -> data/backtest/metrics.json"""
import json
import os
import sys
import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config
from src.backtest import walk_forward, brier, wape
from src.engine import di_to_multiplier
from src.calendar_lib import load_holidays, day_type
from src.seasonality import build_curve

def main():
    today = datetime.date.today().isoformat()
    holidays = load_holidays()
    season = build_curve()
    pairs = list(walk_forward(config.RADAR_HISTORY_DB, "2026-08-15", today))
    preds, outs = [], []
    for _, _, p, a in pairs:
        preds.append(p)
        outs.append(a)
    b = brier(preds, [1 if o >= 0.7 else 0 for o in outs])
    # price error: suggested (engine on the night, rival state ignored for v1)
    pred_prices, actual_prices = [], []
    for _, night, p, a in pairs:
        if a <= 0.05:
            continue                            # no sellout signal that night
        d = datetime.date.fromisoformat(night)
        r = season.get(day_type(d, holidays)["jmonth"], 1.0)
        import src.engine as eng
        di = eng._di_from_mdf(r * eng.WEEKDAY_W[d.weekday()])
        pred_prices.append(2_400_000 * di_to_multiplier(di))
        con_actual = None                        # filled below from history
        actual_prices.append(2_400_000 * di_to_multiplier(min(100, 100 * a)))
    w = wape(pred_prices, actual_prices) if pred_prices else None
    dest = os.path.join(config.DATA, "backtest")
    os.makedirs(dest, exist_ok=True)
    out = {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "pairs": len(pairs),
           "brier_sellout_0.7": round(b, 4),
           "wape_price": round(w, 4) if w is not None else None,
           "mean_pred_share": round(sum(preds) / len(preds), 3),
           "mean_actual_share": round(sum(outs) / len(outs), 3)}
    json.dump(out, open(os.path.join(dest, "metrics.json"), "w"),
              indent=1)
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
