#!/usr/bin/env python3
"""
peek_data.py — نمایش سریع موجودی داده جاجیگا برای پروژه peak-forecast
فقط خواندنی است؛ چیزی را تغییر نمی‌دهد.

Usage:
    python scripts/peek_data.py
"""
import glob
import json
import os

RADAR_DIR = r"H:/projects/jajiga-tracker/data/radar"
SNAP_DIR = r"H:/projects/jajiga-tracker/data/snapshots"
PRICING = r"H:/projects/jajiga-tracker/data/pricing/pricing-dataset.json"


def main():
    # radar calendars
    rfiles = sorted(
        f for f in glob.glob(os.path.join(RADAR_DIR, "*.json"))
        if os.path.basename(f)[0].isdigit()
    )
    own = others = 0
    horizon = 0
    for f in rfiles:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("meta", {}).get("own"):
            own += 1
        else:
            others += 1
        horizon = max(horizon, len(d.get("nights", [])))
    print(f"radar calendars : {len(rfiles)} files (own={own}, rivals={others}), max horizon {horizon} nights")

    # snapshots
    snaps = sorted(glob.glob(os.path.join(SNAP_DIR, "supply-*.json")))
    if snaps:
        first = os.path.basename(snaps[0])[7:-5]
        last = os.path.basename(snaps[-1])[7:-5]
        print(f"supply snapshots: {len(snaps)} days ({first} .. {last})")

    # pricing dataset
    try:
        rows = json.load(open(PRICING, encoding="utf-8"))
        ok = [r for r in rows if r.get("status") != "fetch_failed"]
        villages = sorted({r.get("village", "?") for r in ok})
        print(f"pricing dataset : {len(ok)}/{len(rows)} rows, villages: {', '.join(villages)}")
    except Exception as e:
        print(f"pricing dataset : ERROR {e}")

    print("\nREADY sources: radar calendars + pricing dataset (can build rule-based v0 now)")
    print("GROWING      : rival occupancy history (needs daily snapshot collection)")


if __name__ == "__main__":
    main()
