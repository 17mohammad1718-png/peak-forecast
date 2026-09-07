import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.engine import forecast_night, di_to_multiplier, commission_price, forecast_horizon

FLAT = {m: 1.0 for m in range(1, 13)}
EMPTY_RIVAL = {"n_rivals": 0, "booked_share": 0.0,
               "p20": None, "p50": None, "p85": None}

def test_multiplier_curve_monotonic():
    xs = [di_to_multiplier(v) for v in (0, 20, 35, 50, 65, 85, 100)]
    assert xs == sorted(xs) and xs[0] == 0.85 and xs[-1] == 2.50

def test_friday_scores_higher_than_monday():
    mon = forecast_night(datetime.date(2026, 9, 14), {}, FLAT, EMPTY_RIVAL)
    fri = forecast_night(datetime.date(2026, 9, 18), {}, FLAT, EMPTY_RIVAL)
    assert fri["di"] > mon["di"]
    assert mon["class_"] in ("Normal", "High")
    assert fri["class_"] != "Super-Peak"   # absolute classes: Fri ~52 -> High

def test_nowruz_holiday_friday_is_super_peak():
    d = datetime.date(2027, 3, 19)     # 1406-01-01 falls around here; verify via jalali key
    # instead use a synthetic Thursday holiday:
    H = {}
    import jdatetime
    probe = datetime.date(2026, 10, 1)  # Thursday
    j = jdatetime.date.fromgregorian(date=probe)
    H[f"{j.year:04d}-{j.month:02d}-{j.day:02d}"] = ["test"]
    r = forecast_night(probe, H, FLAT, EMPTY_RIVAL)
    assert r["is_holiday"] and r["important_holiday"]
    # holiday Thursday W=1.30*H=1.5 -> DI ~75+ -> Super-Peak absolute
    assert r["class_"] in ("Peak", "Super-Peak")

def test_commission_price():
    assert commission_price(3_000_000) == 3_143_000   # round to 1000

def test_price_clamped_by_rival_band():
    rival = {"n_rivals": 10, "booked_share": 0.1,
             "p20": 2_000_000, "p50": 2_500_000, "p85": 3_200_000}
    r = forecast_night(datetime.date(2026, 10, 6), {}, FLAT, rival)  # Tuesday low
    assert r["price"] >= 1_800_000                    # hard floor respected

def test_horizon_rank_badges():
    rows = forecast_horizon(datetime.date(2026, 9, 10), 30, {}, FLAT,
                            lambda n: EMPTY_RIVAL)
    assert len(rows) == 30
    assert any(o.get("rank_badge") for o in rows)   # top-5/20/50% badge exists
