#!/usr/bin/env python3
"""Build forecast-dashboard.html v2: year HEATMAP (Jalali months x weekdays),
90-day table, rivals tab, truth tab. Single file, inline payload, RTL dark v2."""
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
    bt_path = os.path.join(config.DATA, "backtest", "metrics.json")
    bt = json.load(open(bt_path, encoding="utf-8")) if os.path.exists(bt_path) else {}
    ym = {}
    for jy in (1405, 1406):
        p = os.path.join(config.DATA, f"yearmap-{jy}.json")
        if os.path.exists(p):
            ym[str(jy)] = json.load(open(p, encoding="utf-8"))
    payload = {"latest": latest, "backtest": bt, "yearmap": ym}
    jseason = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    html = HTML_TPL.replace("__PAYLOAD__", jseason)
    html = html.replace("__ANCHOR__", f"{latest['anchor']:,}")
    html = html.replace("__CF__", str(latest.get("commission_factor", 1.0476)))
    dest = os.path.join(config.PF_ROOT, "forecast-dashboard.html")
    open(dest, "w", encoding="utf-8").write(html)
    print("wrote", dest, f"({len(html):,} bytes, {len(latest['nights'])} nights)")

HTML_TPL = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>رادار پیک — پیش‌بینی پیک و قیمت</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
<style>
:root { --bg0:#090c10; --bg1:#0d1117; --card:#11161d; --card2:#161c25;
        --border:#232a35; --fg:#e6edf3; --muted:#7d8896;
        --accent:#4ea3ff; --green:#3fb950; --gold:#e3b341; --red:#f85149;
        --purple:#bc8cff; --orange:#f0883e; }
* { box-sizing:border-box; }
body { margin:0; background:
  radial-gradient(1200px 500px at 80% -10%, #12233d33, transparent),
  radial-gradient(900px 400px at 10% -10%, #2d1a3d22, transparent),
  var(--bg0);
  color:var(--fg); font-family:Vazirmatn, Tahoma, sans-serif; font-size:13.5px;
  line-height:1.7; }
.en { font-family: Consolas, monospace; direction:ltr; unicode-bidi:embed; }
.wrap { padding:18px 20px 40px; max-width:1240px; margin:0 auto; }
header.hero { display:flex; justify-content:space-between; align-items:center;
  flex-wrap:wrap; gap:10px; margin-bottom:14px; }
h1 { font-size:19px; margin:0; display:flex; align-items:center; gap:10px; }
h1 .logo { width:34px; height:34px; border-radius:10px; display:grid;
  place-items:center; font-size:18px;
  background:linear-gradient(135deg,#1a3a5c,#0d1117); border:1px solid var(--border); }
h1 small { color:var(--muted); font-size:12px; font-weight:normal; display:block; }
.hero-meta { display:flex; gap:14px; color:var(--muted); font-size:12px; }
.hero-meta b { color:var(--fg); }
.tabs { display:flex; gap:8px; margin:14px 0 16px; flex-wrap:wrap; }
.tabs button { background:var(--card); color:var(--muted);
  border:1px solid var(--border); border-radius:12px; padding:9px 18px;
  cursor:pointer; font-family:inherit; font-size:13px; transition:all .15s; }
.tabs button:hover { color:var(--fg); border-color:var(--accent); }
.tabs button.active { background:linear-gradient(135deg,#1a3a5c,#132436);
  color:#fff; border-color:var(--accent); font-weight:bold; }
.card { background:var(--card); border:1px solid var(--border); border-radius:16px;
  padding:16px; margin-bottom:16px; box-shadow:0 2px 14px #0005; }
.card h3 { margin:0 0 10px; font-size:14.5px; display:flex; gap:8px; align-items:center; }
.card h3 .dot { width:8px; height:8px; border-radius:50%; background:var(--accent); }
.muted { color:var(--muted); font-size:12px; }
table { width:100%; border-collapse:collapse; }
th, td { padding:7px 10px; border-bottom:1px solid var(--border); text-align:center; }
th { color:var(--muted); font-weight:normal; position:sticky; top:0; background:var(--card); cursor:pointer; user-select:none; }
th:hover { color:var(--accent); }
tbody tr:hover { background:#ffffff06; }
tr.normal td.di { color:var(--muted); }
tr.high td.di { color:var(--accent); }
tr.peak td.di { color:var(--gold); font-weight:bold; }
tr.super td.di { color:var(--red); font-weight:bold; }
.price { font-weight:bold; }
tr.normal .price { color:var(--fg); } tr.high .price { color:var(--accent); }
tr.peak .price { color:var(--gold); } tr.super .price { color:var(--red); }
.badge { border-radius:7px; padding:1.5px 9px; font-size:10.5px; margin:0 2px; }
.b-hol { background:#3b1e1033; color:var(--orange); border:1px solid #f0883e33; }
.b-bridge { background:#2b1a4433; color:var(--purple); border:1px solid #bc8cff33; }
.b-orphan { background:#10261a33; color:var(--green); border:1px solid #3fb95033; }
.b-block { background:#33141b33; color:var(--red); border:1px solid #f8514933; }
.b-rival { background:#0e2a4d33; color:var(--accent); border:1px solid #4ea3ff33; }
.kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
.kpi { background:linear-gradient(180deg,var(--card2),var(--card));
  border:1px solid var(--border); border-radius:14px; padding:14px; text-align:center; }
.kpi .v { font-size:22px; font-weight:800; color:var(--accent); }
.kpi .l { font-size:11px; color:var(--muted); margin-top:3px; }
/* ---- HEATMAP ---- */
.hm-year { display:flex; gap:8px; margin-bottom:8px; flex-wrap:wrap; }
.hm-year button { background:var(--card2); color:var(--fg); border:1px solid var(--border);
  border-radius:10px; padding:6px 16px; cursor:pointer; font-family:inherit; font-size:12.5px; }
.hm-year button.active { border-color:var(--accent); color:var(--accent); font-weight:bold; }
.hm { display:grid; grid-template-columns:repeat(7,1fr); gap:4px; min-width:640px; }
.hm .cell { border-radius:6px; padding:7px 4px; text-align:center; cursor:default;
  border:1px solid #ffffff0d; transition:transform .06s; position:relative; }
.hm .cell:hover { transform:scale(1.08); z-index:3; border-color:var(--fg); }
.hm .cell .d { font-size:11px; font-weight:bold; display:block; }
.hm .cell .t { font-size:9.5px; opacity:.85; }
.hm .cell.hol { box-shadow:inset 0 0 0 1.5px var(--orange); }
.hm .cell.bri { box-shadow:inset 0 0 0 1.5px var(--purple); }
.hm .cell.riv { box-shadow:inset 0 0 0 1.5px var(--accent); }
.hm .cell.riv::after { content:"◆"; position:absolute; top:1px; left:3px; font-size:7px; color:var(--accent); }
.hm .monthlabel { grid-column:1/-1; color:var(--muted); font-size:12px; font-weight:bold;
  border-bottom:1px dashed var(--border); padding:6px 0 4px; margin:2px 0; }
.hmT { width:100%; border-collapse:collapse; min-width:640px; }
.hmT th { color:var(--muted); font-weight:normal; padding:8px 10px; border-bottom:1px solid var(--border); cursor:default; }
.hmT th:hover { color:var(--muted); }
.hmT td { padding:4px 6px; border-bottom:1px solid var(--border); text-align:center; }
.hmT tbody tr:hover { background:#ffffff06; }
.hmT .cell { display:inline-block; min-width:58px; cursor:default; }
.mcell { display:flex; flex-direction:column; align-items:center; gap:2px;
  padding:10px 8px; border-radius:10px; }
.mcell .tname { font-size:10px; opacity:.92; }
.mhead { display:flex; justify-content:space-between; align-items:center;
  gap:8px; padding:10px 12px; border-radius:10px; min-width:110px;
  color:#0b0f14; font-weight:bold; }
.mhead .muted { color:#0b0f14; opacity:.75; font-size:10.5px; font-weight:normal; }
.legend2 { display:flex; gap:16px; flex-wrap:wrap; margin-top:10px; align-items:center; }
.lg-bar { width:160px; height:10px; border-radius:5px;
  background:linear-gradient(90deg,#1a2332,#1d4d7c,#2e8bc0,#e3b341,#f85149); }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
@media (max-width:900px){ .grid2{ grid-template-columns:1fr; } .hm{ min-width:560px; } }
.tablewrap { overflow:auto; max-height:640px; border-radius:10px; }
::-webkit-scrollbar { width:11px; height:11px; }
::-webkit-scrollbar-track { background:var(--bg1); }
::-webkit-scrollbar-thumb { background:#2a3340; border-radius:6px; border:2px solid var(--bg1); }
::-webkit-scrollbar-thumb:hover { background:#3a4553; }
.tooltip { position:fixed; background:#1c2430; border:1px solid var(--border);
  padding:8px 12px; border-radius:10px; font-size:11.5px; pointer-events:none;
  opacity:0; transition:opacity .1s; z-index:99; box-shadow:0 6px 20px #0009; max-width:260px; }
</style></head><body>
<div class="wrap">
<header class="hero">
  <h1><span class="logo">🎯</span>
    <span>رادار پیک<small>پیش‌بینی پیک و قیمت پیشنهادی — کلبه سوئیسی سیدکلا</small></span></h1>
  <div class="hero-meta">
    <span>لنگر <b class="en">__ANCHOR__</b></span>
    <span>اصلاح کمسیون <b class="en">__CF__×</b></span>
    <span>ساخته <b class="en" id="gen">—</b></span>
  </div>
</header>
<div class="tabs" id="tabs">
  <button data-t="hm" class="active">🗓️ هیت‌مپ سال</button>
  <button data-t="cal">📋 تقویم ۹۰ روزه</button>
  <button data-t="rivals">📡 رقبا</button>
  <button data-t="truth">⚖️ پیش‌بینی در برابر واقعیت</button>
</div>
<div id="tab-hm"></div><div id="tab-cal" style="display:none"></div>
<div id="tab-rivals" style="display:none"></div><div id="tab-truth" style="display:none"></div>
<div id="tip" class="tooltip"></div>
</div>
<script>
const DATA = __PAYLOAD__;
const nights = DATA.latest.nights, YM = DATA.yearmap, BT = DATA.backtest||{};
const CLS = {"Normal":"normal","High":"high","Peak":"peak","Super-Peak":"super"};
const CLSFA = {"Normal":"عادی","High":"پرتقاضا","Peak":"پیک","Super-Peak":"ابرپیک"};
const JM = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"];
const DW = {"Mon":"دوشنبه","Tue":"سه‌شنبه","Wed":"چهارشنبه","Thu":"پنجشنبه","Fri":"جمعه","Sat":"شنبه","Sun":"یکشنبه"};
function fmt(n){ return n==null?"—":Math.round(n).toLocaleString("en-US"); }
function tierColor(t){
  const stops = ["#1a2332","#1d4d7c","#2e8bc0","#e3b341","#f85149"];
  const th = [25,50,72,88];
  if (t<=th[0]) return stops[0]; if (t<=th[1]) return stops[1];
  if (t<=th[2]) return stops[2]; if (t<=th[3]) return stops[3]; return stops[4];
}
function fgColor(t){ return t>=72?"#0b0f14":"#c9d4e0"; }
function renderMonthly(root, rows, year){
  const DOWS = ["Sat","Sun","Mon","Tue","Wed","Thu","Fri"];
  const DOW_FA = {"Sat":"شنبه","Sun":"یکشنبه","Mon":"دوشنبه","Tue":"سه‌شنبه",
                  "Wed":"چهارشنبه","Thu":"پنجشنبه","Fri":"جمعه"};
  const agg = {};
  rows.forEach(r=>{
    const k = r.jmonth+"-"+r.dow;
    (agg[k]=agg[k]||[]).push(r.tier);
  });
  const avg = arr => Math.round(arr.reduce((s,x)=>s+x,0)/arr.length);
  let h = "";
  h += `<div style="overflow:auto"><table class="hmT"><thead><tr>
    <th style="min-width:90px">ماه</th>`;
  for (const d of DOWS) h += `<th>${DOW_FA[d]}</th>`;
  h += `<th>میانگین ماه</th></tr></thead><tbody>`;
  for (let m=1;m<=12;m++){
    const rowCells = DOWS.map(d=>{
      const a = agg[m+"-"+d];
      if (!a) return `<td class="muted">—</td>`;
      const t = avg(a);
      return `<td><div class="cell" data-tip="${JM[m-1]} ${year} · ${DOW_FA[d]} | شدت: ${t}"
        style="background:${tierColor(t)};color:${fgColor(t)}">
        <span class="en">${t}</span></div></td>`;
    }).join("");
    const monthVals = [];
    for (const d of DOWS){ const a = agg[m+"-"+d]; if(a) monthVals.push(avg(a)); }
    const mt = monthVals.length?avg(monthVals):0;
    h += `<tr><td style="font-weight:bold;white-space:nowrap">${JM[m-1]} <span class="muted en">${year}</span></td>${rowCells}
      <td><b class="en">${mt}</b></td></tr>`;
  }
  h += `</tbody></table></div>
    <div class="legend2"><span class="muted">کم</span>
    <div class="lg-bar"></div><span class="muted">پیک</span>
    <span class="muted" style="margin-inline-start:14px">هر سلول = میانگین شدت تقاضای آن روزِ هفته در آن ماه</span></div>`;
  root.innerHTML = h;
  root.querySelectorAll(".hm-year button").forEach(b=>{
    b.onclick = ()=>{
      if (b.dataset.y){ hmYear = b.dataset.y; }
      if (b.dataset.m){ hmMode = b.dataset.m; }
      render();
    };
  });
}
document.getElementById("gen").textContent = DATA.latest.generated_at.slice(0,10);

/* ================= TAB: YEAR HEATMAP (rolling 12 months) ================= */
let hmMode = "daily";   // no year switch: always the NEXT 12 months (rolling)
function tierColor(t){
  const stops = ["#1a2332","#1d4d7c","#2e8bc0","#e3b341","#f85149"];
  const th = [25,50,72,88];
  if (t<=th[0]) return stops[0]; if (t<=th[1]) return stops[1];
  if (t<=th[2]) return stops[2]; if (t<=th[3]) return stops[3]; return stops[4];
}
function fgColor(t){ return t>=72?"#0b0f14":"#c9d4e0"; }
function rollingWindow(){
  /* Union of yearmap rows inside [today, today+365d]. Rows come from 1405+1406. */
  const today = new Date(); today.setHours(0,0,0,0);
  const end = new Date(today.getTime()+365*24*3600*1000);
  const out = [];
  for (const y of Object.keys(YM).sort()){
    for (const r of (YM[y]||[])){
      const d = new Date(r.date+"T00:00:00");
      if (d>=today && d<=end) out.push(r);
    }
  }
  out.sort((a,b)=>a.date<b.date?-1:1);
  return out;
}
function renderMonthly(root, rows){
  const DOWS = ["Sat","Sun","Mon","Tue","Wed","Thu","Fri"];
  const DOW_FA = {"Sat":"شنبه","Sun":"یکشنبه","Mon":"دوشنبه","Tue":"سه‌شنبه",
                  "Wed":"چهارشنبه","Thu":"پنجشنبه","Fri":"جمعه"};
  const agg = {};
  rows.forEach(r=>{
    const k = r.jyear+"-"+r.jmonth+"-"+r.dow;
    (agg[k]=agg[k]||[]).push(r.tier);
  });
  const avg = arr => Math.round(arr.reduce((s,x)=>s+x,0)/arr.length);
  // month order present in window (e.g. 1405-08 .. 1406-07)
  const months = [];
  rows.forEach(r=>{
    const k = r.jyear+"-"+String(r.jmonth).padStart(2,"0");
    if (!months.includes(k)) months.push(k);
  });
  let h = `<div style="overflow:auto"><table class="hmT"><thead><tr>
    <th style="min-width:110px">ماه</th>`;
  for (const d of DOWS) h += `<th>${DOW_FA[d]}</th>`;
  h += `<th>میانگین</th></tr></thead><tbody>`;
  for (const mk of months){
    const [jy, jm] = mk.split("-").map(Number);
    const rowCells = DOWS.map(d=>{
      const a = agg[jy+"-"+jm+"-"+d];
      if (!a) return `<td><span class="muted">—</span></td>`;
      const t = avg(a);
      return `<td><div class="cell mcell" data-tip="${JM[jm-1]} ${jy} · ${DOW_FA[d]} | شدت: ${t}"
        style="background:linear-gradient(135deg, ${tierColor(t)}cc, ${tierColor(t)}), ${tierColor(t)}">
        <span class="tname">${JM[jm-1]}</span>
        <b class="en">${t}</b></div></td>`;
    }).join("");
    const monthVals = [];
    for (const d of DOWS){ const a = agg[jy+"-"+jm+"-"+d]; if(a) monthVals.push(avg(a)); }
    const mt = monthVals.length?avg(monthVals):0;
    h += `<tr><td><div class="mhead" style="background:linear-gradient(135deg, ${tierColor(mt)}cc, ${tierColor(mt)})">
      <span>${JM[jm-1]} <span class="en muted">${jy}</span></span>
      <b class="en">${mt}</b></div></td>${rowCells}
      <td class="en muted" style="font-size:11px">ↆ</td></tr>`;
  }
  h += `</tbody></table></div>
    <div class="legend2"><span class="muted">کم</span>
    <div class="lg-bar"></div><span class="muted">پیک</span>
    <span class="muted" style="margin-inline-start:14px">هر سلول: نام ماه + امتیاز میانگین · ۱۲ ماه آینده</span></div>`;
  root.innerHTML = h;
}
(function(){
  const root = document.getElementById("tab-hm");
  function render(){
    const rows = rollingWindow();
    const byM = {};
    rows.forEach(r=>{ (byM[r.jyear+"-"+r.jmonth]=byM[r.jmonth]||[]).push(r); });
    let h = `<div class="card">
      <h3><span class="dot"></span>هیت‌مپ تقاضا — ۱۲ ماه آینده
      <span class="muted" style="margin-inline-start:auto">
      چشمک ◆ = شب‌هایی که رزرو واقعی رقبا ثبت شده</span></h3>
      <div class="hm-year">
      <button class="${hmMode=="daily"?"active":""}" data-m="daily">روزانه</button>
      <button class="${hmMode=="monthly"?"active":""}" data-m="monthly">ماهانه (روز هفته)</button>
      </div>`;
    if (hmMode === "monthly"){
      renderMonthly(root, rows);
      return;
    }
    h += `<div style="overflow:auto"><div class="hm">`;
    let lastKey = "";
    for (const m of Object.keys(byM).sort()){
      h += `<div class="monthlabel">${m.replace("-", " · ")}</div>`;
      const cells = byM[m];
      const padMap = {"Sat":0,"Sun":1,"Mon":2,"Tue":3,"Wed":4,"Thu":5,"Fri":6};
      for (let i=0;i<padMap[cells[0].dow];i++) h += `<div></div>`;
      for (const c of cells){
        const cls = (c.is_holiday?"hol ":"")+(c.is_bridge?"bri ":"")+(c.has_rival_data?"riv":"");
        h += `<div class="cell ${cls}" data-tip="${JM[c.jmonth-1]} ${c.jalali.split('-')[2]} — ${DW[c.dow]} | شدت: ${c.tier}${c.is_holiday?" | تعطیل رسمی":""}${c.is_bridge?" | پل":""}${c.rival_share!=null?" | رقبا: "+c.rival_share+"%":""}"
              style="background:${tierColor(c.tier)};color:${fgColor(c.tier)}">
              <span class="d en">${c.jalali.split('-')[2]}</span>
              <span class="t">${c.is_holiday?"تعطیل":DW[c.dow].slice(0,2)}</span></div>`;
      }
    }
    h += `</div></div>
      <div class="legend2"><span class="muted">کم</span>
        <div class="lg-bar"></div><span class="muted">پیک</span>
        <span class="muted" style="margin-inline-start:14px">
        <i style="box-shadow:inset 0 0 0 1.5px var(--orange);width:12px;height:12px;border-radius:3px;display:inline-block"></i> تعطیل رسمی</span>
        <span class="muted"><i style="box-shadow:inset 0 0 0 1.5px var(--purple);width:12px;height:12px;border-radius:3px;display:inline-block"></i> پل تعطیلات</span>
        <span class="muted"><i style="box-shadow:inset 0 0 0 1.5px var(--accent);width:12px;height:12px;border-radius:3px;display:inline-block"></i> داده رزرو واقعی</span>
      </div></div>`;
    root.innerHTML = h;
    root.querySelectorAll(".hm-year button").forEach(b=>{
      b.onclick = ()=>{
        if (b.dataset.m) hmMode = b.dataset.m;
        render();
      };
    });
  }
  render();
})();
/* tooltip */
const tip = document.getElementById("tip");
document.addEventListener("mousemove", e=>{
  const c = e.target.closest(".cell");
  if (c){
    tip.innerHTML = c.dataset.tip.split(" | ").join("<br>");
    tip.style.opacity = 1;
    tip.style.left = Math.min(e.clientX+14, innerWidth-280)+"px";
    tip.style.top = (e.clientY+16)+"px";
  } else tip.style.opacity = 0;
});

/* ================= TAB: 90-day table ================= */
(function(){
  const byM = {};
  nights.forEach(o=>{ (byM[o.jmonth]=byM[o.jmonth]||[]).push(o); });
  let h = `<div class="legend" style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:10px">
    <span class="muted"><i style="background:var(--muted);width:10px;height:10px;border-radius:2px;display:inline-block"></i> عادی</span>
    <span class="muted"><i style="background:var(--accent);width:10px;height:10px;border-radius:2px;display:inline-block"></i> پرتقاضا</span>
    <span class="muted"><i style="background:var(--gold);width:10px;height:10px;border-radius:2px;display:inline-block"></i> پیک</span>
    <span class="muted"><i style="background:var(--red);width:10px;height:10px;border-radius:2px;display:inline-block"></i> ابرپیک</span>
    <span class="muted">قیمت‌ها تومان / شب · پس از اصلاح کمسیون</span></div>`;
  for (const m of Object.keys(byM).sort((a,b)=>a-b)){
    h += `<div class="card"><h3><span class="dot"></span>${JM[m-1]} <span class="muted en">${byM[m][0].jalali.split('-')[0]}</span></h3>
      <div class="tablewrap"><table><thead><tr>
      <th data-k="jalali">تاریخ</th><th>روز</th><th data-k="di">DI ▾</th><th>کلاس</th>
      <th data-k="price">قیمت پیشنهادی</th><th data-k="multiplier">×ضریب</th>
      <th>مین‌استی</th><th data-k="share">رقیب پر%</th><th>برچسب</th></tr></thead><tbody>`;
    for (const o of byM[m]){
      const j = o.jalali.split("-");
      const badges = [];
      if (o.is_holiday) badges.push('<span class="badge b-hol">تعطیل</span>');
      if (o.is_bridge) badges.push('<span class="badge b-bridge">پل</span>');
      if (o.is_orphan) badges.push('<span class="badge b-orphan">شب یتیم</span>');
      if (o.own_booked) badges.push('<span class="badge b-block">مشغول (خودم)</span>');
      if (o.rival.booked_share>0.7) badges.push('<span class="badge b-rival">رقبا پر</span>');
      h += `<tr class="${CLS[o.class_q]}">
        <td class="en">${j[0]}/${j[1]}/${j[2]}</td>
        <td>${DW[o.dow]}</td>
        <td class="di en">${o.di}</td>
        <td>${CLSFA[o.class_q]}</td>
        <td class="price en">${fmt(o.price)}</td>
        <td class="en muted">${o.multiplier}</td>
        <td class="en">${o.min_stay}</td>
        <td class="en muted">${Math.round((o.rival.booked_share||0)*100)}%</td>
        <td>${badges.join(" ")}</td></tr>`;
    }
    h += "</tbody></table></div></div>";
  }
  document.getElementById("tab-cal").innerHTML = h;
  // simple sort on click
  document.querySelectorAll("#tab-cal th[data-k]").forEach(th=>{
    th.onclick = ()=>{
      const k = th.dataset.k;
      const tbl = th.closest("table"), tb = tbl.querySelector("tbody");
      const rows = [...tb.querySelectorAll("tr")];
      rows.sort((a,b)=>{
        const va = a.children[th.cellIndex].textContent.replace(/[^0-9.]/g,"");
        const vb = b.children[th.cellIndex].textContent.replace(/[^0-9.]/g,"");
        return (parseFloat(vb)||0)-(parseFloat(va)||0);
      });
      rows.forEach(r=>tb.appendChild(r));
    };
  });
})();

/* ================= TAB: rivals (Jalali) ================= */
(function(){
  const JM_EN = ["Farvardin","Ordibehesht","Khordad","Tir","Mordad","Shahrivar",
                 "Mehr","Aban","Azar","Dey","Bahman","Esfand"];
  // group by jalali month, then by jalali week-of-month (7-day chunks)
  const wk = {};
  nights.forEach(o=>{
    const [jy, jm, jd] = o.jalali.split("-").map(Number);
    const weekNum = Math.floor((jd-1)/7);           // 0..4
    const key = jy+"-"+String(jm).padStart(2,"0")+"-"+weekNum;
    (wk[key]=wk[key]||[]).push(o);
  });
  const MW = ["هفته ۱","هفته ۲","هفته ۳","هفته ۴","هفته ۵"];
  let h = '<div class="card"><h3><span class="dot"></span>اشغال تجمیعی ۳۴ رقیب (تقویم شمسی، ماه به ماه)</h3><table><thead><tr><th>ماه</th><th>هفته</th><th>پر%</th><th>P20</th><th>P50 (میانه)</th><th>P85</th></tr></thead><tbody>';
  const keys = Object.keys(wk).sort();
  let lastMonth = "";
  for (const k of keys){
    const [jy, jm, wnum] = k.split("-");
    const monthLabel = `${JM[Number(jm)-1]} <span class="en">${jy}</span>`;
    if (jm !== lastMonth){
      h += `<tr style="background:#ffffff08"><td colspan="6" style="text-align:right;font-weight:bold;color:var(--accent)">${monthLabel}</td></tr>`;
      lastMonth = jm;
    }
    const arr = wk[k];
    const bs = Math.round(arr.reduce((s,o)=>s+(o.rival.booked_share||0),0)/arr.length*100);
    const p20 = arr.map(o=>o.rival.p20).filter(x=>x);
    const p50 = arr.map(o=>o.rival.p50).filter(x=>x);
    const p85 = arr.map(o=>o.rival.p85).filter(x=>x);
    const avg = a=>a.length?Math.round(a.reduce((s,x)=>s+x,0)/a.length):null;
    h += `<tr><td class="muted"></td><td>${MW[Number(wnum)]}</td>
      <td class="en">${bs}%</td>
      <td class="en muted">${fmt(avg(p20))}</td><td class="en">${fmt(avg(p50))}</td>
      <td class="en muted">${fmt(avg(p85))}</td></tr>`;
  }
  h += `</tbody></table><p class="muted">اواخر تقویم رقبا هنوز باز نشده (۰٪ طبیعی است؛ هرچه نزدیک‌تر شویم داده پر می‌شود). مبنا: آخرین snapshot روزانه.</p></div>`;
  document.getElementById("tab-rivals").innerHTML = h;
})();

/* ================= TAB: truth ================= */
(function(){
  let h = '<div class="card"><h3><span class="dot"></span>پیش‌بینی در برابر واقعیت — walk-forward از 2026-08-15</h3>';
  if (BT && BT.pairs){
    h += `<div class="kpis">
      <div class="kpi"><div class="v en">${BT.pairs}</div><div class="l">جفت پیش‌بینی/واقعیت</div></div>
      <div class="kpi"><div class="v en">${BT["brier_sellout_0.7"]}</div><div class="l">Brier (فروش رقیب)</div></div>
      <div class="kpi"><div class="v en">${BT.wape_price??"—"}</div><div class="l">WAPE قیمت</div></div>
      <div class="kpi"><div class="v en">${Math.round((BT.mean_pred_share||0)*100)}%</div><div class="l">اشغال پیش‌بینی</div></div>
      <div class="kpi"><div class="v en">${Math.round((BT.mean_actual_share||0)*100)}%</div><div class="l">اشغال واقعی</div></div>
    </div><p class="muted">Brier و WAPE هرچه به ۰ نزدیک‌تر بهتر. این شاخص‌ها با هر روز داده بیشتر دقیق‌تر می‌شوند.</p>`;
  } else { h += '<p class="muted">هنوز بک‌تست ثبت نشده.</p>'; }
  h += "</div>";
  document.getElementById("tab-truth").innerHTML = h;
})();

/* tabs */
document.getElementById("tabs").addEventListener("click", e=>{
  if (e.target.tagName!=="BUTTON") return;
  document.querySelectorAll("#tabs button").forEach(b=>b.classList.remove("active"));
  e.target.classList.add("active");
  ["hm","cal","rivals","truth"].forEach(t=>{
    document.getElementById("tab-"+t).style.display = (t===e.target.dataset.t)?"":"none";
  });
  if (e.target.dataset.t==="hm" && window.__hmRender) window.__hmRender();
});
</script>
</body></html>"""

if __name__ == "__main__":
    main()
