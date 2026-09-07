#!/usr/bin/env python3
"""Build forecast-dashboard.html: single file, inline payload, RTL dark."""
import json
import os
import sys
import datetime
import jdatetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config

def main():
    latest = json.load(open(os.path.join(config.DATA, "forecast", "latest.json"),
                            encoding="utf-8"))
    season = json.load(open(os.path.join(config.DATA, "seasonality.json"),
                            encoding="utf-8"))
    bt_path = os.path.join(config.DATA, "backtest", "metrics.json")
    bt = json.load(open(bt_path, encoding="utf-8")) if os.path.exists(bt_path) else {}
    payload = {"latest": latest, "season": season, "backtest": bt}
    jseason = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    JMONTH = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
              "مهر","آبان","آذر","دی","بهمن","اسفند"]
    nights = latest["nights"]
    # group by jalali month for the calendar tab
    months = {}
    for o in nights:
        months.setdefault(o["jmonth"], []).append(o)
    jrange = [f"{jdatetime.date.fromgregorian(date=datetime.date.fromisoformat(nights[0]['date'])).year}"]

    html = """<!DOCTYPE html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>رادار پیک — پیش‌بینی پیک و قیمت</title>
<style>
:root { --bg:#0d1117; --card:#161b22; --border:#30363d; --fg:#e6edf3;
        --muted:#8b949e; --accent:#58a6ff; --green:#3fb950; --gold:#d29922;
        --red:#f85149; --purple:#bc8cff; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
       font-family:Vazirmatn, Tahoma, sans-serif; font-size:14px; }
.en { font-family: Consolas, monospace; direction:ltr; unicode-bidi:embed; }
.wrap { padding:16px; max-width:1200px; margin:0 auto; }
h1 { font-size:18px; margin:8px 0; } h1 small { color:var(--muted); font-size:12px; }
.tabs { display:flex; gap:6px; margin:12px 0; flex-wrap:wrap; }
.tabs button { background:var(--card); color:var(--fg); border:1px solid var(--border);
  border-radius:8px; padding:8px 14px; cursor:pointer; font-family:inherit; font-size:13px; }
.tabs button.active { background:var(--accent); color:#04121f; font-weight:bold; }
.card { background:var(--card); border:1px solid var(--border); border-radius:10px;
        padding:14px; margin-bottom:14px; }
table { width:100%; border-collapse:collapse; }
th, td { padding:6px 8px; border-bottom:1px solid var(--border); text-align:center; }
th { color:var(--muted); position:sticky; top:0; background:var(--card); cursor:pointer; }
tr.normal td.di { color:var(--muted); }
tr.high td.di { color:var(--accent); }
tr.peak td.di { color:var(--gold); font-weight:bold; }
tr.super td.di { color:var(--red); font-weight:bold; }
.badge { border-radius:6px; padding:2px 8px; font-size:11px; }
.b-hol { background:#3b1e10; color:#f0883e; }
.b-bridge { background:#2b1a44; color:var(--purple); }
.b-orphan { background:#10261a; color:var(--green); }
.b-block { background:#33141b; color:var(--red); }
.bars { display:flex; align-items:flex-end; gap:8px; height:180px; padding:10px 4px; }
.bar { flex:1; background:linear-gradient(180deg, var(--accent), #1f4e79);
       border-radius:4px 4px 0 0; position:relative; min-width:26px; }
.bar span { position:absolute; top:-20px; right:50%; transform:translateX(50%);
            font-size:11px; color:var(--muted); white-space:nowrap; }
.bar b { position:absolute; bottom:-24px; right:50%; transform:translateX(50%);
         font-size:11px; font-weight:normal; white-space:nowrap; }
.kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; }
.kpi { background:var(--card); border:1px solid var(--border); border-radius:10px;
       padding:12px; text-align:center; }
.kpi .v { font-size:20px; font-weight:bold; color:var(--accent); }
.kpi .l { font-size:11px; color:var(--muted); margin-top:4px; }
::-webkit-scrollbar { width:10px; height:10px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:5px; }
::-webkit-scrollbar-thumb:hover { background:var(--muted); }
.muted { color:var(--muted); font-size:12px; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
@media (max-width:800px){ .grid2{ grid-template-columns:1fr; } }
.legend { display:flex; gap:14px; flex-wrap:wrap; margin:8px 0; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-left:4px; }
</style></head><body>
<div class="wrap">
<h1>🎯 رادار پیک — پیش‌بینی پیک و قیمت پیشنهادی
<small>کلبه سوئیسی سیدکلا · لنگر <span class="en">__ANCHOR__</span> · کمسیون‌اصلاح <span class="en">__CF__×</span></small></h1>
<div class="tabs" id="tabs">
  <button data-t="cal" class="active">تقویم ۹۰ روزه</button>
  <button data-t="year">نمای سال</button>
  <button data-t="rivals">رقبا</button>
  <button data-t="truth">پیش‌بینی در برابر واقعیت</button>
</div>
<div id="tab-cal"></div><div id="tab-year" style="display:none"></div>
<div id="tab-rivals" style="display:none"></div><div id="tab-truth" style="display:none"></div>
</div>
<script>
window.__PF = __PAYLOAD__;
const D = window.__PF.latest, S = window.__PF.season, BT = window.__PF.backtest||{};
const nights = D.nights;
const CLS = {"Normal":"normal","High":"high","Peak":"peak","Super-Peak":"super"};
const CLSFA = {"Normal":"عادی","High":"پرتقاضا","Peak":"پیک","Super-Peak":"ابرپیک"};
const JM = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"];
const DW = {"Mon":"دوشنبه","Tue":"سه‌شنبه","Wed":"چهارشنبه","Thu":"پنجشنبه","Fri":"جمعه","Sat":"شنبه","Sun":"یکشنبه"};
function fmt(n){ return n==null?"—":n.toLocaleString("en-US"); }
function esc(s){ return String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }

// ---- Tab 1: 90-day table grouped by jalali month
(function(){
  const byM = {};
  nights.forEach(o=>{ (byM[o.jmonth]=byM[o.jmonth]||[]).push(o); });
  let h = `<div class="legend">
    <span><i style="background:var(--muted)"></i>عادی</span>
    <span><i style="background:var(--accent)"></i>پرتقاضا</span>
    <span><i style="background:var(--gold)"></i>پیک</span>
    <span><i style="background:var(--red)"></i>ابرپیک</span>
    <span><span class="badge b-hol">تعطیل</span></span>
    <span><span class="badge b-bridge">پل</span></span>
    <span><span class="badge b-orphan">شب یتیم</span></span></div>`;
  for (const m of Object.keys(byM).sort((a,b)=>a-b)){
    h += `<div class="card"><h3 style="margin:4px 0 8px">${JM[m-1]}</h3>
      <div style="overflow:auto"><table><thead><tr>
      <th>تاریخ</th><th>روز</th><th>DI</th><th>کلاس</th><th>قیمت پیشنهادی</th>
      <th>×ضریب</th><th>مین‌استی</th><th>رقیب پر%</th><th>برچسب</th></tr></thead><tbody>`;
    for (const o of byM[m]){
      const j = o.jalali.split("-");
      const badges = [];
      if (o.is_holiday) badges.push('<span class="badge b-hol">تعطیل</span>');
      if (o.is_bridge) badges.push('<span class="badge b-bridge">پل</span>');
      if (o.is_orphan) badges.push('<span class="badge b-orphan">یتیم</span>');
      if (o.own_booked) badges.push('<span class="badge b-block">دربارهٔ ما</span>');
      h += `<tr class="${CLS[o.class_q]}">
        <td class="en">${j[0]}/${j[1]}/${j[2]}</td>
        <td>${DW[o.dow]}</td>
        <td class="di en">${o.di}</td>
        <td>${CLSFA[o.class_q]}</td>
        <td class="en" style="font-weight:bold">${fmt(o.price)}</td>
        <td class="en">${o.multiplier}</td>
        <td class="en">${o.min_stay}</td>
        <td class="en">${Math.round((o.rival.booked_share||0)*100)}%</td>
        <td>${badges.join(" ")}</td></tr>`;
    }
    h += "</tbody></table></div></div>";
  }
  document.getElementById("tab-cal").innerHTML = h;
})();

// ---- Tab 2: year view (seasonality bars)
(function(){
  const vals = Object.values(window.__PF.season);
  const mx = Math.max(...vals);
  let h = '<div class="card"><h3 style="margin:4px 0">منحنی فصلی سال (از ۷,۶۴۶ نظر بابلکنار، ۲۰۱۹–۲۰۲۶)</h3><div class="bars">';
  JM.forEach((m,i)=>{
    const v = vals[i];
    const pct = Math.round(v/mx*100);
    h += `<div class="bar" style="height:${pct}%" title="${m}: ${v}">
      <span class="en">${v}</span><b>${m}</b></div>`;
  });
  h += `</div><p class="muted">ضریب S(ماه) در موتور — نمای کل سال. پیک: ${JM[vals.indexOf(mx)]}.</p></div>`;
  document.getElementById("tab-year").innerHTML = h;
})();

// ---- Tab 3: rivals aggregate per week
(function(){
  const wk = {};
  nights.forEach(o=>{
    const key = o.date.slice(0,7)+"-"+String(Math.floor((new Date(o.date).getDate()-1)/7));
    (wk[key]=wk[key]||[]).push(o);
  });
  let h = '<div class="card"><h3 style="margin:4px 0">وضعیت تجمیعی ۳۴ رقیب (میانگین هفته)</h3><table><thead><tr><th>هفته</th><th>پر%</th><th>P20</th><th>P50</th><th>P85</th></tr></thead><tbody>';
  for (const k of Object.keys(wk).sort()){
    const arr = wk[k];
    const bs = Math.round(arr.reduce((s,o)=>s+(o.rival.booked_share||0),0)/arr.length*100);
    const p20 = arr.map(o=>o.rival.p20).filter(x=>x);
    const p50 = arr.map(o=>o.rival.p50).filter(x=>x);
    const p85 = arr.map(o=>o.rival.p85).filter(x=>x);
    const avg = a=>a.length?Math.round(a.reduce((s,x)=>s+x,0)/a.length):null;
    h += `<tr><td class="en">${k}</td><td class="en">${bs}%</td>
      <td class="en">${fmt(avg(p20))}</td><td class="en">${fmt(avg(p50))}</td>
      <td class="en">${fmt(avg(p85))}</td></tr>`;
  }
  h += "</tbody></table></div>";
  document.getElementById("tab-rivals").innerHTML = h;
})();

// ---- Tab 4: truth (backtest)
(function(){
  let h = '<div class="card"><h3 style="margin:4px 0">پیش‌بینی در برابر واقعیت (walk-forward از 2026-08-15)</h3>';
  if (BT && BT.pairs){
    h += `<div class="kpis">
      <div class="kpi"><div class="v en">${BT.pairs}</div><div class="l">جفت پیش‌بینی/واقعیت</div></div>
      <div class="kpi"><div class="v en">${BT["brier_sellout_0.7"]}</div><div class="l">Brier (پیش‌بینی فروش رقیب)</div></div>
      <div class="kpi"><div class="v en">${BT.wape_price??"—"}</div><div class="l">WAPE قیمت</div></div>
      <div class="kpi"><div class="v en">${Math.round((BT.mean_pred_share||0)*100)}%</div><div class="l">میانگین اشغال پیش‌بینی</div></div>
      <div class="kpi"><div class="v en">${Math.round((BT.mean_actual_share||0)*100)}%</div><div class="l">میانگین اشغال واقعی</div></div>
    </div><p class="muted">هرچه Brier به 0 و WAPE به 0 نزدیک‌تر، پیش‌بینی دقیق‌تر. هر روز بهتر می‌شود.</p>`;
  } else { h += '<p class="muted">هنوز بک‌تست ثبت نشده.</p>'; }
  h += "</div>";
  document.getElementById("tab-truth").innerHTML = h;
})();

// ---- tabs
document.getElementById("tabs").addEventListener("click", e=>{
  if (e.target.tagName!=="BUTTON") return;
  document.querySelectorAll("#tabs button").forEach(b=>b.classList.remove("active"));
  e.target.classList.add("active");
  ["cal","year","rivals","truth"].forEach(t=>{
    document.getElementById("tab-"+t).style.display = (t===e.target.dataset.t)?"":"none";
  });
});
</script>
</body></html>"""
    html = html.replace("__PAYLOAD__", jseason)
    html = html.replace("__ANCHOR__", f"{latest['anchor']:,}")
    html = html.replace("__CF__", str(latest.get("commission_factor", 1.0476)))
    dest = os.path.join(config.PF_ROOT, "forecast-dashboard.html")
    open(dest, "w", encoding="utf-8").write(html)
    print("wrote", dest, f"({len(html):,} bytes, {len(nights)} nights)")

if __name__ == "__main__":
    main()
