"""Jalali calendar helpers: holidays (persian_holiday.db), weekends, holiday eves, bridges."""
import datetime
import sqlite3
import jdatetime
from . import config

DOW_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DOW_FA = {
    "Mon": "دوشنبه",
    "Tue": "سه‌شنبه",
    "Wed": "چهارشنبه",
    "Thu": "پنجشنبه",
    "Fri": "جمعه",
    "Sat": "شنبه",
    "Sun": "یکشنبه",
}

def load_holidays():
    """{jalali_yyyy-mm-dd: [events]} for official holidays only."""
    if not os_path_exists(config.HOLIDAYS_DB):
        return {}
    con = sqlite3.connect(config.HOLIDAYS_DB)
    rows = con.execute(
        "SELECT year, month, day, event FROM events WHERE is_holiday=1"
    ).fetchall()
    con.close()
    out = {}
    for y, m, d, ev in rows:
        out.setdefault(f"{y:04d}-{m:02d}-{d:02d}", []).append(ev or "")
    return out

def os_path_exists(p):
    import os
    return os.path.exists(p)

def to_jalali(d):
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d)
    return jdatetime.date.fromgregorian(date=d)

def jkey(d):
    j = to_jalali(d)
    return f"{j.year:04d}-{j.month:02d}-{j.day:02d}"

def is_off_day(d, holidays):
    """Off day = weekend (Thu/Fri) OR official holiday."""
    if d.weekday() in (3, 4):
        return True
    return jkey(d) in holidays

def day_type(d, holidays):
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d)
    dow = d.weekday()  # Mon=0 ... Sun=6
    j = to_jalali(d)
    is_holiday = jkey(d) in holidays
    is_weekend = dow in (3, 4)
    
    # Eve of holiday/weekend: tomorrow is an off day while today is a working/normal day or Wed
    tomorrow = d + datetime.timedelta(days=1)
    is_eve = is_off_day(tomorrow, holidays) and not is_weekend

    return {
        "date": d.isoformat(),
        "dow": DOW_EN[dow],
        "dow_fa": DOW_FA[DOW_EN[dow]],
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
        "is_eve": is_eve,
        "jalali": jkey(d),
        "jyear": j.year,
        "jmonth": j.month,
        "jday": j.day,
    }

def bridge_info(d, holidays):
    """Info about bridged days and consecutive long weekends."""
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d)
        
    cur_key = jkey(d)
    cur_holiday = cur_key in holidays
    
    def off(delta):
        dt = d + datetime.timedelta(days=delta)
        return is_off_day(dt, holidays)

    # Bridge: normal day sandwiched between off days within +-2 days
    is_bridge = (not is_off_day(d, holidays)) and (
        (off(-1) or off(-2)) and (off(1) or off(2))
    )

    # Consecutive off days span around d (if d is off day)
    span = 0
    if is_off_day(d, holidays):
        left = 0
        while off(-(left + 1)):
            left += 1
        right = 0
        while off(right + 1):
            right += 1
        span = 1 + left + right

    return {
        "is_bridge": is_bridge,
        "is_holiday": cur_holiday,
        "is_consecutive": span >= 3,
        "span_length": span,
    }
