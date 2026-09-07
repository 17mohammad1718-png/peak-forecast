#!/usr/bin/env python3
"""Walk-forward backtest audit pipeline -> data/backtest/metrics.json"""
import json
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config
from src.backtest import evaluate_historical_occupancy_accuracy

def main():
    today_iso = datetime.date.today().isoformat()
    acc = evaluate_historical_occupancy_accuracy(config.DB_PATH, today=today_iso)

    out = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "model_version": getattr(config, "MODEL_VERSION", "v2.0-jalali-market"),
        "pairs_evaluated": acc.get("pairs", 0),
        "brier_score": acc.get("brier_score"),
        "evaluation_note": acc.get("note"),
        "trade_price_metric_status": "منسوخ شده — بدون مبلغ واقعی رزرو، دقت قیمت معامله و افزایش درآمد قابل اثبات نیست",
    }

    dest = os.path.join(config.DATA, "backtest")
    os.makedirs(dest, exist_ok=True)
    out_path = os.path.join(dest, "metrics.json")
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
