"""Jalali calendar helpers: holidays (persian_holiday.db), weekends, bridges."""
import datetime
import sqlite3
import jdatetime
from . import config

def load_holidays():
    """{jalali_yyyy-mm-dd: [events]} for official holidays only."""
    con = sqlite3.connect(config.HOLIDAYS_DB)
    rows = con.execute(
        "SELECT year, month, day, event FROM events WHERE is_holiday=1").fetchall()
    con.close()
    out = {}
    for y, m, d, ev in rows:
        out.setdefault(f"{y:04d}-{m:02d}-{d:02d}", []).append(ev or "")
    return out

def to_jalali(d):
    return jdatetime.date.fromgregorian(date=d)

def jkey(d):
    j = to_jalali(d)
    return f"{j.year:04d}-{j.month:02d}-{j.day:02d}"

DOW_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def day_type(d, holidays):
    dow = d.weekday()                      # Mon=0 ... Sun=6
    is_holiday = jkey(d) in holidays
    return {"date": d.isoformat(), "dow": DOW_EN[dow],
            "is_weekend": dow in (3, 4),   # Thu, Fri (Iran)
            "is_holiday": is_holiday, "jalali": jkey(d),
            "jmonth": to_jalali(d).month}

def bridge_info(d, holidays):
    """Bridge v1 (conservative): D is a normal day sandwiched between holidays
    within +-2 days -> likely government-bridged long weekend."""
    if jkey(d) in holidays:
        return {"is_bridge": False, "is_holiday": True}
    def hol(delta):
        return jkey(d + datetime.timedelta(days=delta)) in holidays
    return {"is_bridge": (hol(-1) or hol(-2)) and (hol(1) or hol(2)),
            "is_holiday": False}
