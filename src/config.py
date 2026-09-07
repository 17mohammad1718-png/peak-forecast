"""Central config for peak-forecast. All paths absolute; all money in toman."""
import os

PF_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(PF_ROOT, "data")
DB_PATH = os.path.join(DATA, "peak_forecast.db")

MODEL_VERSION = "v2.0-jalali-market"

# Total active rival listings in Babolkenar / target market segment
TOTAL_TRACKED_RIVALS = 35

# External paths with local workspace fallbacks
JT = os.environ.get("JAJIGA_TRACKER_DIR", r"H:/projects/jajiga-tracker")
RADAR_LIVE = os.path.join(JT, "data", "radar") if os.path.exists(JT) else os.path.join(DATA, "radar")
RADAR_HISTORY_DB = (
    os.path.join(JT, "data", "radar", "history", "radar_history.db")
    if os.path.exists(JT) else os.path.join(DATA, "radar_history.db")
)
REVIEWS_CORPUS = (
    os.path.join(JT, "data", "reviews_mining", "corpus.json")
    if os.path.exists(JT) else os.path.join(DATA, "corpus.json")
)
HOLIDAYS_DB = os.path.join(DATA, "persian_holiday.db")

OWN_ROOM_ID = 3297585

# Pricing & economic parameters
ANCHOR_PRICE = 2_400_000       # fallback baseline anchor in Toman
COMMISSION_OWN = 0.16
COMMISSION_RIVAL = 0.12
COMMISSION_FACTOR = (1 - COMMISSION_RIVAL) / (1 - COMMISSION_OWN)  # ~1.0476
HARD_FLOOR = 1_800_000
HORIZON_DAYS = 90
TELEGRAM_CHAT_IDS = [109583793]
