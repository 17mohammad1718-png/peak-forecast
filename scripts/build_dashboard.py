#!/usr/bin/env python3
"""Build forecast-dashboard.html v2.0-jalali-market.

Renders:
  1. Consecutive Peak Ranges Banner
  2. 90-day Daily Forecast Table (Jalali date, demand level, reason, market range, suggested price, valid rival count, confidence)
  3. Backtest & Accuracy Audit
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config

def main():
    latest_path = os.path.join(config.DATA, "forecast", "latest.json")
    if not os.path.exists(latest_path):
        print(f"Error: {latest_path} not found. Run scripts/run_forecast.py first.")
        return

    latest = json.load(open(latest_path, encoding="utf-8"))
    bt_path = os.path.join(config.DATA, "backtest", "metrics.json")
    bt = json.load(open(bt_path, encoding="utf-8")) if os.path.exists(bt_path) else {}

    payload = {"latest": latest, "backtest": bt}
    jseason = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    html = HTML_TPL.replace("__PAYLOAD__", jseason)
    dest = os.path.join(config.PF_ROOT, "forecast-dashboard.html")
    open(dest, "w", encoding="utf-8").write(html)
    print("wrote", dest, f"({len(html):,} bytes, {len(latest['nights'])} nights)")

HTML_TPL = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>پیش‌بینی تقاضای بازار و قیمت پیشنهادی — کلبه سوئیسی</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
<style>
:root {
  --bg0: #090c10; --bg1: #0d1117; --card: #11161d; --card2: #161c25;
  --border: #232a35; --fg: #e6edf3; --muted: #7d8896;
  --accent: #4ea3ff; --green: #3fb950; --gold: #e3b341; --red: #f85149;
  --purple: #bc8cff; --orange: #f0883e;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: radial-gradient(1200px 500px at 80% -10%, #12233d33, transparent), var(--bg0);
  color: var(--fg); font-family: Vazirmatn, Tahoma, sans-serif; font-size: 13.5px; line-height: 1.7;
}
.en { font-family: Consolas, monospace; direction: ltr; unicode-bidi: embed; }
.wrap { padding: 20px; max-width: 1280px; margin: 0 auto; }
header.hero { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; }
h1 { font-size: 20px; margin: 0; display: flex; align-items: center; gap: 10px; }
h1 .logo { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; font-size: 18px; background: #1a3a5c; border: 1px solid var(--border); }
h1 small { color: var(--muted); font-size: 12px; font-weight: normal; display: block; }
.hero-meta { color: var(--muted); font-size: 12px; }
.hero-meta b { color: var(--fg); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 18px; margin-bottom: 20px; }
.card h3 { margin: 0 0 12px; font-size: 15px; display: flex; gap: 8px; align-items: center; }
.card h3 .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
.peak-range-item { background: #3b1e1022; border: 1px solid #f0883e55; border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
.peak-range-item strong { color: var(--orange); }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px 12px; border-bottom: 1px solid var(--border); text-align: center; }
th { color: var(--muted); font-weight: normal; background: var(--card); position: sticky; top: 0; }
tbody tr:hover { background: #ffffff06; }
.level-normal { color: var(--muted); }
.level-high { color: var(--accent); font-weight: bold; }
.level-peak { color: var(--gold); font-weight: bold; }
.level-super { color: var(--red); font-weight: bold; }
.badge { border-radius: 6px; padding: 2px 8px; font-size: 11px; display: inline-block; }
.b-conf-high { background: #10261a; color: var(--green); border: 1px solid #3fb95044; }
.b-conf-low { background: #33141b; color: var(--red); border: 1px solid #f8514944; }
.b-warning { background: #3b1e10; color: var(--orange); border: 1px solid #f0883e44; }
.tablewrap { overflow: auto; max-height: 700px; border-radius: 10px; border: 1px solid var(--border); }
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <h1>
      <span class="logo">🎯</span>
      <span>پیش‌بینی تقاضای بازار و قیمت پیشنهادی<small>کلبه سوئیسی سیدکلا — نسخه <span class="en" id="ver">v2.0-jalali-market</span></small></span>
    </h1>
    <div class="hero-meta">
      <span>تاریخ صدور: <b class="en" id="gen">—</b></span>
    </div>
  </header>

  <!-- Consecutive Peak Ranges -->
  <div class="card" id="peak-ranges-card">
    <h3><span class="dot" style="background:var(--orange)"></span>🔥 بازه‌های شب‌های پیک متوالی</h3>
    <div id="peak-ranges-list">هیچ بازهٔ پیک متوالی کشف نشد.</div>
  </div>

  <!-- 90-Day Output Table -->
  <div class="card">
    <h3><span class="dot"></span>📋 پیش‌بینی روزانه تقاضا و قیمت پیشنهادی</h3>
    <div class="tablewrap">
      <table>
        <thead>
          <tr>
            <th>تاریخ شمسی</th>
            <th>تاریخ میلادی (روز)</th>
            <th>سطح تقاضا</th>
            <th>دلیل / عوامل تقاضا</th>
            <th>بازهٔ قیمت پیشنهادی بازار</th>
            <th>قیمت پیشنهادی کلبه</th>
            <th>رقبای معتبر</th>
            <th>اطمینان</th>
          </tr>
        </thead>
        <tbody id="forecast-rows"></tbody>
      </table>
    </div>
  </div>

  <!-- Backtest & Accuracy Audit -->
  <div class="card">
    <h3><span class="dot" style="background:var(--purple)"></span>⚖️ صحت‌سنجی و ارزیابی مدل</h3>
    <div id="backtest-info" class="en"></div>
  </div>
</div>

<script>
const DATA = __PAYLOAD__;
const latest = DATA.latest || {};
const bt = DATA.backtest || {};

document.getElementById('gen').innerText = latest.generated_at || '—';
document.getElementById('ver').innerText = latest.model_version || 'v2.0';

// Render peak ranges
const rangesList = document.getElementById('peak-ranges-list');
if (latest.consecutive_peak_ranges && latest.consecutive_peak_ranges.length > 0) {
  rangesList.innerHTML = latest.consecutive_peak_ranges.map(r => `
    <div class="peak-range-item">
      <span>🔥 <strong>${r.start} تا ${r.end}</strong> (${r.nights_count} شب متوالی)</span>
      <span class="badge b-warning">سطح: ${r.level}</span>
    </div>
  `).join('');
} else {
  rangesList.innerHTML = '<span style="color:var(--muted)">هیچ بازهٔ پیک متوالی در افق پیش‌بینی یافت نشد.</span>';
}

// Render daily table rows
const tbody = document.getElementById('forecast-rows');
const nights = latest.nights || [];
tbody.innerHTML = nights.map(n => {
  const lvl = n.demand_level || n.class_ || 'عادی';
  let lvlClass = 'level-normal';
  if (lvl === 'پرتقاضا' || lvl === 'High') lvlClass = 'level-high';
  if (lvl === 'پیک' || lvl === 'Peak') lvlClass = 'level-peak';
  if (lvl === 'ابرپیک' || lvl === 'Super-Peak') lvlClass = 'level-super';

  const mRange = n.market_range ? 
    `${n.market_range.p25.toLocaleString()} تا ${n.market_range.p75.toLocaleString()} تومان` : '—';
  
  const priceDisplay = (n.suggested_price || n.price || 0).toLocaleString() + ' تومان';
  const conf = n.confidence || '—';
  const confBadge = conf.includes('پایین') ? 'b-conf-low' : 'b-conf-high';

  return `
    <tr>
      <td><strong class="en">${n.jalali || '—'}</strong></td>
      <td class="en">${n.date} (${n.dow_fa || n.dow})</td>
      <td class="${lvlClass}">${lvl}</td>
      <td style="text-align:right; font-size:12px;">${n.reason || '—'}</td>
      <td class="en">${mRange}</td>
      <td><strong style="color:var(--green)">${priceDisplay}</strong> ${n.infeasible ? '<br><span class="badge b-warning">کف اقتصادی > بازار</span>' : ''}</td>
      <td class="en">${n.valid_rival_count != null ? n.valid_rival_count : (n.rival ? n.rival.n_with_price : 0)}</td>
      <td><span class="badge ${confBadge}">${conf}</span></td>
    </tr>
  `;
}).join('');

// Render backtest info
document.getElementById('backtest-info').innerHTML = `
  <p style="color:var(--fg); font-family:inherit;">
    <strong>Pairs Evaluated:</strong> ${bt.pairs_evaluated || 0} <br>
    <strong>Brier Score:</strong> ${bt.brier_score != null ? bt.brier_score : 'N/A'} <br>
    <strong>Evaluation Note:</strong> ${bt.evaluation_note || '—'} <br>
    <strong>Status:</strong> ${bt.trade_price_metric_status || '—'}
  </p>
`;
</script>
</body>
</html>
"""
