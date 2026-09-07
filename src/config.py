"""Central config for peak-forecast. All paths absolute; all money in toman."""
import os

PF_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(PF_ROOT, "data")
DB_PATH = os.path.join(DATA, "peak_forecast.db")

JT = r"H:/projects/jajiga-tracker"
RADAR_LIVE = os.path.join(JT, "data", "radar")            # 35 live calendars
RADAR_HISTORY_DB = os.path.join(JT, "data", "radar", "history", "radar_history.db")
REVIEWS_CORPUS = os.path.join(JT, "data", "reviews_mining", "corpus.json")
HOLIDAYS_DB = os.path.join(DATA, "persian_holiday.db")

OWN_ROOM_ID = 3297585

# Frozen decisions (IDEA.md v3)
ANCHOR_PRICE = 2_400_000       # monthly review with user confirmation
COMMISSION_OWN = 0.16
COMMISSION_RIVAL = 0.12
COMMISSION_FACTOR = (1 - COMMISSION_RIVAL) / (1 - COMMISSION_OWN)  # 1.047619...
HARD_FLOOR = 1_800_000
HORIZON_DAYS = 90
TELEGRAM_CHAT_IDS = [109583793]
# bot token resolved at runtime by tg_digest.py from hermes .env files
