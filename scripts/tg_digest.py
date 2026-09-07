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
    # resolve from hermes .env files without printing it
    import re
    for p in [os.path.expanduser(r"~/AppData/Local/hermes/profiles/smart/.env"),
              os.path.expanduser(r"~/AppData/Local/hermes/.env")]:
        if os.path.exists(p):
            m = re.search(r"TELEGRAM_BOT_TOKEN\s*=\s*(\S+)", open(p, encoding="utf-8").read())
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
        if o["class_q"] == "Super-Peak" and p["class_q"] != "Super-Peak":
            bullets.append(f"⚠️ پیک جدید: {o['date']} DI={o['di']}")
        if (not p.get("is_orphan")) and o.get("is_orphan"):
            bullets.append(f"🕯️ شب یتیم جدید: {o['date']} → "
                           f"{o['price']:,} (max_stay=1)")
        if len(bullets) >= 15:
            break
    return bullets

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
    if not bullets:
        print("no delta; nothing to send")
    else:
        text = "📡 رادار پیک — تغییرات امروز:\n" + "\n".join(bullets)
        _send(text)
    # rotate prev = latest (copy, not move)
    json.dump(new, open(prev_path, "w", encoding="utf-8"),
              ensure_ascii=False)

if __name__ == "__main__":
    main()
