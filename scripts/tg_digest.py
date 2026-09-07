#!/usr/bin/env python3
"""Delta-only Telegram digest: compare latest.json vs prev.json, rotate files.

VPN/proxy requirement: uses TELEGRAM_PROXY (http://127.0.0.1:18080 or :10808).
If proxy unreachable -> exit silently (retry next day). Never blocks pipeline.
Message format: emoji rows (no monospace boxes), Persian, <=15 bullets.
"""
import json
import os
import sys
import urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config

FORECAST_DIR = os.path.join(config.DATA, "forecast")
PROXIES = ["http://127.0.0.1:18080", "http://127.0.0.1:10808"]

def _bot_token():
    """Resolve bot token from hermes .env files; never print it."""
    import re
    pat = re.compile(
        r"^TELEGRAM_BOT_TOKEN\s*=\s*['\"]?([0-9]+:[A-Za-z0-9_\-]{20,})['\"]?\s*$",
        re.M)
    for p in [os.path.expanduser(r"~/AppData/Local/hermes/.env"),
              os.path.expanduser(r"~/AppData/Local/hermes/profiles/smart/.env")]:
        if os.path.exists(p):
            m = pat.search(open(p, encoding="utf-8").read())
            if m:
                return m.group(1)
    return None

def _send(text):
    token = _bot_token()
    if not token:
        print("no bot token found; skip"); return False
    body = json.dumps({"chat_id": config.TELEGRAM_CHAT_IDS[0], "text": text}
                      ).encode("utf-8")
    last_err = None
    for proxy in PROXIES:
        try:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=body, headers={"Content-Type": "application/json"})
            with opener.open(req, timeout=20) as r:
                if r.status == 200:
                    print(f"sent via {proxy}"); return True
        except Exception as e:
            last_err = e
    print(f"send failed (proxy off?): {last_err}"); return False

def diff_msgs(new, old):
    """Return list of Persian delta bullets."""
    if not old:
        return []
    old_by = {o["date"]: o for o in old["nights"]}
    bullets = []
    for o in new["nights"]:
        p = old_by.get(o["date"])
        if not p:
            continue
        if o["price"] != p["price"]:
            d = (o["price"] - p["price"]) / p["price"] * 100
            if abs(d) >= 5:
                arrows = "🟢" if d < 0 else "🔴"
                bullets.append(f"{arrows} {o['date']} قیمت {p['price']:,} → "
                               f"{o['price']:,} ({d:+.0f}%)")
        if o["class_"] == "Super-Peak" and p["class_"] != "Super-Peak":
            bullets.append(f"⚠️ پیک جدید: {o['date']} DI={o['di']}")
        if (not p.get("is_orphan")) and o.get("is_orphan"):
            bullets.append(f"🕯️ شب یتیم جدید: {o['date']} → "
                           f"{o['price']:,} (max_stay=1)")
        if len(bullets) >= 15:
            break
    return bullets

DW_FA = {"Mon": "دوشنبه", "Tue": "سه‌شنبه", "Wed": "چهارشنبه",
         "Thu": "پنجشنبه", "Fri": "جمعه", "Sat": "شنبه", "Sun": "یکشنبه"}

def action_cards(new):
    """v1.1: up to 3 action cards — decision due, economics, response line."""
    from src.floor import gross_floor
    cands = [o for o in new["nights"]
             if not o.get("own_booked") and not o.get("is_orphan")
             and o.get("lead_days", 99) <= 14
             and o.get("ladder_mult", 1) < 1.0]
    cands.sort(key=lambda o: (o["lead_days"], -o["price"]))
    cards = []
    for o in cands[:3]:
        floor_n = gross_floor(max(1, o.get("min_stay", 1)))
        net = round(o["price"] * 0.84, -3)
        clears = "✅ کف OK" if net >= floor_n else "⚠️ زیر کف اقتصادی"
        cards.append(
            f"🎯 {o['date']} ({DW_FA.get(o['dow'], o['dow'])}) — "
            f"پیشنهاد: {o['price']:,} تومان\n"
            f"│ تخفیف {int((1-o['ladder_mult'])*100)}% · DI {o['di']} · "
            f"رقیب پر {round((o['rival'].get('booked_share') or 0)*100)}%\n"
            f"│ خالص ≈ {net:,} · {clears}\n"
            f"└ پاسخ: «done» / «hold» / «reject»")
    return cards

def main():
    latest_path = os.path.join(FORECAST_DIR, "latest.json")
    prev_path = os.path.join(FORECAST_DIR, "prev.json")
    new = json.load(open(latest_path, encoding="utf-8"))
    old = None
    if os.path.exists(prev_path):
        try:
            old = json.load(open(prev_path, encoding="utf-8"))
        except Exception:
            old = None
    bullets = diff_msgs(new, old)
    cards = action_cards(new)
    parts = []
    if bullets:
        parts.append("📡 تغییرات:\n" + "\n".join(bullets[:8]))
    if cards:
        parts.append("⚡ تصمیم امروز:\n" + "\n\n".join(cards))
    if not parts:
        print("no delta, no actions; nothing to send")
    else:
        _send("\n\n".join(parts))
    # rotate prev = latest (copy, not move)
    json.dump(new, open(prev_path, "w", encoding="utf-8"),
              ensure_ascii=False)

if __name__ == "__main__":
    main()
