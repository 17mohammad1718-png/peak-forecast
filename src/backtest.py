"""Walk-forward backtest & audit trail for peak-forecast predictions.

Prevents future data leakage by evaluating only target nights that have elapsed (night <= today)
using information available at issued_at time.
Discarded synthetic price metric (WAPE based on sellout share).
"""
import sqlite3
import json
import os
from datetime import date
from . import config

AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS forecast_audit (
    issued_at       TEXT NOT NULL,
    night           TEXT NOT NULL,
    model_version   TEXT NOT NULL,
    di              REAL,
    demand_level    TEXT,
    suggested_price INTEGER,
    confidence      TEXT,
    PRIMARY KEY (issued_at, night, model_version)
);
"""

def record_forecast_audit(db_path, forecast_rows, issued_at=None, model_version=None):
    """Store generated forecast predictions for audit trail and backtesting."""
    db_path = db_path or config.DB_PATH
    issued_at = issued_at or date.today().isoformat()
    model_version = model_version or getattr(config, "MODEL_VERSION", "v2.0-jalali-market")

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(AUDIT_SCHEMA)

    rows = []
    for r in forecast_rows:
        rows.append((
            issued_at,
            r["date"],
            model_version,
            r.get("di"),
            r.get("demand_level") or r.get("class_"),
            r.get("suggested_price") or r.get("price"),
            r.get("confidence"),
        ))

    con.executemany(
        "INSERT OR REPLACE INTO forecast_audit VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    con.close()
    return len(rows)

def brier_score(predictions, actuals):
    """Brier score for probability / binary outcomes."""
    if not predictions or not actuals or len(predictions) != len(actuals):
        return 0.0
    return sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)

def evaluate_historical_occupancy_accuracy(db_path, today=None):
    """Evaluate demand prediction accuracy on elapsed target nights using ground truth DB."""
    today_iso = today or date.today().isoformat()
    if not db_path or not os.path.exists(db_path):
        return {"pairs": 0, "brier_score": None, "note": "دیتابیس موجود نیست"}

    con = sqlite3.connect(db_path)
    
    # Select audit predictions where target night <= today_iso
    query = """
    SELECT a.night, a.di, a.demand_level, n.booked, n.status
    FROM forecast_audit a
    INNER JOIN nights n ON a.night = n.night AND n.own = 0
    WHERE a.night <= ? AND a.issued_at <= a.night
    GROUP BY a.night
    """
    rows = con.execute(query, (today_iso,)).fetchall()
    con.close()

    if not rows:
        return {
            "pairs": 0,
            "brier_score": None,
            "note": "هنوز شب سررسیده‌ای برای ارزیابی پیش‌بینی با اطلاعات زمان پیش‌بینی موجود نیست",
        }

    preds = []
    outs = []
    for night, di, level, booked, status in rows:
        pred_prob = min(1.0, max(0.0, (di or 50) / 100.0))
        actual = 1 if (booked or status in ("confirmed_booking", "unavailable_unknown")) else 0
        preds.append(pred_prob)
        outs.append(actual)

    score = brier_score(preds, outs)
    return {
        "pairs": len(rows),
        "brier_score": round(score, 4),
        "note": "ارزیابی بر اساس شب‌های سررسیده‌شده بدون نشت اطلاعات آینده انجام شد.",
    }
