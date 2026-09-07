import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import ledger

def test_import_and_summary(tmp_path=None):
    import src.config as config
    old_db = config.DB_PATH
    config.DB_PATH = os.path.join(tempfile.mkdtemp(), "led.db")
    try:
        p = os.path.join(tempfile.mkdtemp(), "t.json")
        json.dump([{"start": "2026-09-10", "nights": 2, "payout": 5_000_000},
                   {"start": "2026-09-10", "nights": 2, "payout": 5_000_000}],  # dup
                  open(p, "w", encoding="utf-8"))
        r = ledger.import_bookings(p)
        s = ledger.summary()
        assert r["imported"] == 1            # UNIQUE dedupes
        assert s["nights"] == 2 and s["payout"] == 5_000_000
        assert abs(s["adr_net"] - 2_500_000) < 1
        ledger.record_decision("2026-10-01", 3_000_000, 2_800_000, "done", "test")
        s2 = ledger.summary()
        assert s2["decisions"].get("done") == 1
    finally:
        config.DB_PATH = old_db
