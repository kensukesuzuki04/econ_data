#!/usr/bin/env python3
"""
build_charts_inflation_unemployment.py
----------------------------------------
Build three interactive Plotly charts for ECON 10 (Inflation & Unemployment).

    1. chart_inflation.html      -- line chart, inflation rate by country
    2. chart_unemployment.html   -- line chart, unemployment rate by country
    3. chart_phillips.html       -- scatter, unemployment x inflation (Phillips curve)
                                    with dynamic 2nd-degree polynomial trend line

Features
    - All World Bank countries, sorted alphabetically (US pinned to top)
    - Default: United States only shown
    - Country search box in sidebar
    - No range slider (use scroll/drag to zoom)
    - Export: PNG, SVG, and Print/PDF buttons
    - Segoe UI / sans-serif font throughout

Prerequisites
    pip install pandas plotly requests numpy
    python scripts/econ10/collect_data_wb.py   -- download data first

Usage
    python scripts/econ10/build_charts_inflation_unemployment.py

Output
    docs/econ10/chart_inflation.html
    docs/econ10/chart_unemployment.html
    docs/econ10/chart_phillips.html
"""

import json
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# -- Paths --------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / "data" / "econ10"
DOCS_DIR  = REPO_ROOT / "docs" / "econ10"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

US_NAME = "United States"

# Qualitative color palette (14 colors, cycles for additional countries)
PALETTE = [
    "#1f77b4","#d62728","#2ca02c","#ff7f0e","#9467bd",
    "#8c564b","#e377c2","#17becf","#bcbd22","#636363",
    "#4e79a7","#f28e2b","#59a14f","#e15759","#76b7b2",
    "#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac",
]

FONT_FAMILY = "Georgia, 'Times New Roman', serif"

# -- Helper: load and order countries -----------------------------------------
def load_countries(csv_path: Path) -> list:
    """Return country names sorted alphabetically with US pinned first."""
    df = pd.read_csv(csv_path)
    names = sorted(df["country"].unique().tolist())
    if US_NAME in names:
        names.remove(US_NAME)
        names = [US_NAME] + names
    return names


def color_map(country_names: list) -> dict:
    return {n: PALETTE[i % len(PALETTE)] for i, n in enumerate(country_names)}


# -- HTML page template -------------------------------------------------------
# Uses %%TOKEN%% placeholders to avoid f-string conflicts with CSS braces.

PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%%TITLE%% | ECON 10 | Clark University</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:Georgia,'Times New Roman',serif;
     background:#fafaf8;color:#1a1a1a;height:100vh;
     display:flex;flex-direction:column;overflow:hidden}

/* Header */
header{background:#8b0000;color:#fff;padding:.75rem 1.2rem;
       border-bottom:3px solid #5a0000;display:flex;align-items:center;
       gap:.8rem;flex-shrink:0}
header h1{font-size:.98rem;font-weight:600;letter-spacing:.01em}
header .sub{font-size:.76rem;opacity:.75}
.back{font-size:.74rem;color:#ffd0d0;text-decoration:none;margin-left:auto;
      white-space:nowrap}
.back:hover{color:#fff}

/* Export toolbar */
.toolbar{display:flex;align-items:center;gap:.5rem;padding:.45rem 1.2rem;
         background:#fff;border-bottom:1px solid #e8e8e8;flex-shrink:0}
.toolbar span{font-size:.72rem;color:#888;margin-right:.2rem}
.tbtn{font-size:.72rem;padding:.22rem .65rem;border:1px solid #ccc;
      border-radius:3px;background:#fff;cursor:pointer;color:#444;
      font-family:inherit}
.tbtn:hover{border-color:#8b0000;color:#8b0000}

/* Layout */
.layout{display:flex;flex:1;overflow:hidden}

/* Sidebar */
.sidebar{width:200px;min-width:170px;background:#fff;
         border-right:1px solid #e0e0e0;padding:.85rem .8rem;
         overflow-y:auto;flex-shrink:0;display:flex;flex-direction:column;gap:.7rem}
.ctrl-hd{font-size:.67rem;font-weight:600;letter-spacing:.1em;
         text-transform:uppercase;color:#8b0000}
.search-box{width:100%;font-size:.78rem;padding:.28rem .45rem;
            border:1px solid #ccc;border-radius:3px;font-family:inherit}
.search-box:focus{outline:none;border-color:#8b0000}
.btn-row{display:flex;gap:.35rem}
.sbtn{font-size:.7rem;padding:.13rem .38rem;border:1px solid #ccc;
      border-radius:3px;background:#fff;cursor:pointer;color:#555;font-family:inherit}
.sbtn:hover{border-color:#8b0000;color:#8b0000}
.cb-list{flex:1;overflow-y:auto}
.cb-wrap{display:flex;align-items:center;gap:.3rem;padding:.2rem 0}
.cb-wrap input{accent-color:#8b0000;flex-shrink:0;cursor:pointer}
.cb-wrap label{font-size:.78rem;line-height:1.3;cursor:pointer}
.cb-wrap.hidden{display:none}

/* Year range (Phillips only) */
.yr-section{padding-top:.7rem;border-top:1px solid #eee}
.yr-row{display:flex;align-items:center;gap:.3rem;margin-top:.35rem}
.yr-row input{width:56px;font-size:.76rem;padding:.18rem .28rem;
              border:1px solid #ccc;border-radius:3px;text-align:center;
              font-family:inherit}
.yr-row span{font-size:.72rem;color:#666}
.apply-btn{width:100%;margin-top:.45rem;font-size:.74rem;padding:.25rem 0;
           background:#8b0000;color:#fff;border:none;border-radius:3px;
           cursor:pointer;font-family:inherit}
.apply-btn:hover{background:#a00000}
.trend-row{display:flex;align-items:center;gap:.35rem;margin-top:.5rem}
.trend-row input{accent-color:#8b0000;cursor:pointer}
.trend-row label{font-size:.76rem;cursor:pointer}

/* Data source box */
.src-section{padding-top:.7rem;border-top:1px solid #eee;margin-top:auto}
.src-section .ctrl-hd{margin-bottom:.35rem}
.src-section p{font-size:.72rem;color:#555;line-height:1.5}
.src-section a{color:#1f77b4;font-size:.72rem}

/* Chart */
.chart-wrap{flex:1;overflow:hidden;display:flex;flex-direction:column;padding:.35rem}
#chart{width:100%;flex:1}

/* Footer */
footer{font-size:.68rem;color:#aaa;text-align:center;padding:.35rem;
       border-top:1px solid #eee;flex-shrink:0}

/* Print */
@media print{
  header .back, .toolbar, .sidebar, footer{display:none}
  body{overflow:visible;height:auto}
  .layout{display:block}
  .chart-wrap{padding:0}
  #chart{width:100% !important;height:90vh !important}
}
</style>
</head>
<body>

<header>
  <h1>%%TITLE%%</h1>
  <span class="sub">%%SUBTITLE%%</span>
  <a class="back" href="../index.html">&larr; All Charts</a>
</header>

<div class="toolbar">
  <span>Export:</span>
  <button class="tbtn" onclick="dlPNG()">PNG</button>
  <button class="tbtn" onclick="dlSVG()">SVG</button>
  <button class="tbtn" onclick="window.print()">Print / PDF</button>
</div>

<div class="layout">
  <aside class="sidebar">
    <div>
      <div class="ctrl-hd">Countries</div>
      <input class="search-box" type="text" placeholder="Search..."
             oninput="filterSearch(this.value)">
    </div>
    <div class="btn-row">
      <button class="sbtn" onclick="selAll()">All</button>
      <button class="sbtn" onclick="selNone()">None</button>
    </div>
    <div class="cb-list" id="cb-list">
%%CHECKBOXES%%
    </div>
%%EXTRA_CTRL%%
    <div class="src-section">
      <div class="ctrl-hd">Data Source</div>
%%SOURCE_HTML%%
    </div>
  </aside>

  <div class="chart-wrap">
    <div id="chart"></div>
  </div>
</div>

<footer>
  Source: World Bank Open Data (data.worldbank.org) &nbsp;|&nbsp;
  ECON 10 &ndash; Introductory Economics &nbsp;|&nbsp;
  &copy; 2026 Kensuke Suzuki, Clark University
</footer>

<script>
%%CHART_JS%%
%%CTRL_JS%%
</script>
</body>
</html>
"""


def make_checkboxes(country_names: list, default_country: str = US_NAME) -> str:
    lines = []
    for name in country_names:
        checked = "checked" if name == default_country else ""
        esc = name.replace('"', "&quot;")
        lines.append(
            f'      <div class="cb-wrap" data-name="{esc.lower()}">'
            f'<input type="checkbox" class="ccb" id="cb_{esc}" value="{esc}" {checked}>'
            f'<label for="cb_{esc}">{name}</label></div>'
        )
    return "\n".join(lines)


def base_layout(**kwargs):
    defaults = dict(
        margin=dict(l=55, r=20, t=30, b=50),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        hovermode="closest",
        showlegend=False,
        font=dict(family=FONT_FAMILY, size=12),
    )
    defaults.update(kwargs)
    return go.Layout(**defaults)


EXPORT_JS = """\
function dlPNG() {
  Plotly.downloadImage('chart', {format:'png', filename:'%%FNAME%%',
                                  width:1400, height:700, scale:2});
}
function dlSVG() {
  Plotly.downloadImage('chart', {format:'svg', filename:'%%FNAME%%',
                                  width:1400, height:700});
}
"""

SEARCH_JS = """\
function filterSearch(q) {
  q = q.toLowerCase().trim();
  document.querySelectorAll('#cb-list .cb-wrap').forEach(function(w) {
    w.classList.toggle('hidden', q !== '' && !w.dataset.name.includes(q));
  });
}
"""


# -- Line chart ---------------------------------------------------------------
SOURCE_INFLATION = """\
      <p>World Bank Open Data<br>
      Indicator: <code>FP.CPI.TOTL.ZG</code><br>
      Inflation, consumer prices (annual&nbsp;%)<br>
      Coverage: 175 countries, 1960&ndash;2024</p>
      <a href="https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG"
         target="_blank">View on World Bank &rarr;</a>"""

SOURCE_UNEMPLOYMENT = """\
      <p>World Bank Open Data<br>
      Indicator: <code>SL.UEM.TOTL.ZS</code><br>
      Unemployment, total (% of labor force,<br>ILO modeled estimate)<br>
      Coverage: 141 countries, 1991&ndash;2024<br>
      <em>ILO estimates begin 1991; no earlier<br>global data available.</em></p>
      <a href="https://data.worldbank.org/indicator/SL.UEM.TOTL.ZS"
         target="_blank">View on World Bank &rarr;</a>"""

SOURCE_PHILLIPS = """\
      <p>World Bank Open Data<br>
      Unemployment: <code>SL.UEM.TOTL.ZS</code><br>
      Inflation: <code>FP.CPI.TOTL.ZG</code><br>
      Coverage: 1991&ndash;2024 (ILO estimates)</p>
      <a href="https://data.worldbank.org"
         target="_blank">View on World Bank &rarr;</a>"""


def build_line_chart(csv_name: str, title: str, y_label: str, html_name: str,
                     source_html: str = ""):
    csv_path = DATA_DIR / csv_name
    if not csv_path.exists():
        sys.exit(f"ERROR: {csv_path} not found. Run collect_data_wb.py first.")

    df       = pd.read_csv(csv_path)
    names    = load_countries(csv_path)
    cmap     = color_map(names)
    fig      = go.Figure()
    plotted  = []

    for country in names:
        sub = df[df["country"] == country].sort_values("year")
        if sub.empty:
            continue
        plotted.append(country)
        fig.add_trace(go.Scatter(
            x=sub["year"].tolist(),
            y=sub["value"].round(2).tolist(),
            name=country,
            mode="lines+markers",
            visible=True if country == US_NAME else "legendonly",
            showlegend=False,
            line=dict(color=cmap[country], width=2.5),
            marker=dict(size=5),
            hovertemplate=(
                f"<b>{country}</b><br>Year: %{{x}}<br>"
                f"{y_label}: %{{y:.1f}}%<extra></extra>"
            ),
        ))

    fig.update_layout(base_layout(
        xaxis=dict(title="Year", tickformat="d", gridcolor="#f0f0f0"),
        yaxis=dict(title=y_label, gridcolor="#f0f0f0",
                   zeroline=True, zerolinecolor="#ddd", zerolinewidth=1),
    ))

    fname   = html_name.replace(".html", "")
    cbs     = make_checkboxes(plotted)
    chart_js = (
        f"var fig = {fig.to_json()};\n"
        f"Plotly.newPlot('chart', fig.data, fig.layout, {{responsive:true}});\n"
        f"var TRACE_NAMES = {json.dumps(plotted)};\n"
        + EXPORT_JS.replace("%%FNAME%%", fname)
        + SEARCH_JS
    )

    ctrl_js = """\
function onCbChange(cb) {
  var idx = TRACE_NAMES.indexOf(cb.value);
  if (idx < 0) return;
  Plotly.restyle('chart', {visible: cb.checked ? true : 'legendonly'}, [idx]);
}
function selAll() {
  var vis = TRACE_NAMES.map(function(){return true;});
  Plotly.restyle('chart', {visible: vis}, TRACE_NAMES.map(function(_,i){return i;}));
  document.querySelectorAll('.ccb').forEach(function(c){c.checked=true;});
}
function selNone() {
  var vis = TRACE_NAMES.map(function(){return 'legendonly';});
  Plotly.restyle('chart', {visible: vis}, TRACE_NAMES.map(function(_,i){return i;}));
  document.querySelectorAll('.ccb').forEach(function(c){c.checked=false;});
}
document.querySelectorAll('.ccb').forEach(function(c){
  c.addEventListener('change', function(){onCbChange(c);});
});
"""

    html = (PAGE_TEMPLATE
            .replace("%%TITLE%%",      title)
            .replace("%%SUBTITLE%%",   f"{y_label} | World Bank")
            .replace("%%CHECKBOXES%%", cbs)
            .replace("%%EXTRA_CTRL%%", "")
            .replace("%%SOURCE_HTML%%", source_html)
            .replace("%%CHART_JS%%",   chart_js)
            .replace("%%CTRL_JS%%",    ctrl_js))

    out = DOCS_DIR / html_name
    out.write_text(html, encoding="utf-8")
    print(f"  Saved -> {out.relative_to(REPO_ROOT)}")


# -- Phillips curve -----------------------------------------------------------
def poly2_fit(xs, ys):
    """Fit y = a + b*x + c*x^2 using numpy. Returns (coeffs, x_range, y_fit)."""
    if len(xs) < 5:
        return None, None, None
    coeffs  = np.polyfit(xs, ys, 2)          # [c, b, a] (highest degree first)
    x_range = np.linspace(min(xs), max(xs), 200)
    y_fit   = np.polyval(coeffs, x_range)
    return coeffs, x_range.tolist(), y_fit.tolist()


def build_phillips_chart():
    inf_path   = DATA_DIR / "inflation_wb.csv"
    unemp_path = DATA_DIR / "unemployment_wb.csv"
    for p in (inf_path, unemp_path):
        if not p.exists():
            sys.exit(f"ERROR: {p} not found. Run collect_data_wb.py first.")

    inf_df   = pd.read_csv(inf_path).rename(columns={"value": "inflation"})
    unemp_df = pd.read_csv(unemp_path).rename(columns={"value": "unemployment"})
    merged   = (pd.merge(inf_df, unemp_df, on=["country", "year"])
                  .dropna(subset=["inflation", "unemployment"]))

    names    = load_countries(inf_path)
    # Filter to countries that have at least some merged data
    names    = [n for n in names if not merged[merged["country"] == n].empty]
    cmap     = color_map(names)

    fig      = go.Figure()
    plotted  = []
    all_data = {}

    for country in names:
        sub = merged[merged["country"] == country].sort_values("year")
        if sub.empty:
            continue
        plotted.append(country)
        xs    = sub["unemployment"].round(2).tolist()
        ys    = sub["inflation"].round(2).tolist()
        years = sub["year"].tolist()
        texts = [
            f"<b>{country}</b><br>Year: {yr}<br>"
            f"Unemployment: {u:.1f}%<br>Inflation: {inf:.1f}%"
            for yr, u, inf in zip(years, xs, ys)
        ]
        all_data[country] = {"x": xs, "y": ys, "years": years, "text": texts}

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            name=country,
            mode="markers",
            text=texts,
            visible=True if country == US_NAME else "legendonly",
            showlegend=False,
            hovertemplate="%{text}<extra></extra>",
            marker=dict(color=cmap[country], size=7,
                        line=dict(color="white", width=0.5)),
        ))

    # Initial trend line: US data only
    us_data = all_data.get(US_NAME, {})
    _, x_fit, y_fit = poly2_fit(us_data.get("x", []), us_data.get("y", []))
    TREND_IDX = len(plotted)
    fig.add_trace(go.Scatter(
        x=x_fit or [], y=y_fit or [],
        name="Trend (2nd degree)",
        mode="lines",
        line=dict(color="#333", width=2, dash="dash"),
        hoverinfo="skip",
        showlegend=True,
        visible=True,
    ))

    ymin = int(merged["year"].min())
    ymax = int(merged["year"].max())

    fig.update_layout(base_layout(
        xaxis=dict(title="Unemployment Rate (%)", gridcolor="#f0f0f0", zeroline=False),
        yaxis=dict(title="Inflation Rate (%)", gridcolor="#f0f0f0",
                   zeroline=True, zerolinecolor="#ddd", zerolinewidth=1),
        shapes=[dict(type="line", x0=0, x1=1, xref="paper",
                     y0=0, y1=0, yref="y",
                     line=dict(color="#ccc", width=1, dash="dot"))],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, font=dict(size=10)),
    ))

    extra_ctrl = f"""\
    <div class="yr-section">
      <div class="ctrl-hd">Year Range</div>
      <div class="yr-row">
        <input type="number" id="yrMin" value="{ymin}" min="{ymin}" max="{ymax}">
        <span>-</span>
        <input type="number" id="yrMax" value="{ymax}" min="{ymin}" max="{ymax}">
      </div>
      <button class="apply-btn" onclick="applyFilter()">Apply</button>
      <div class="trend-row">
        <input type="checkbox" id="showTrend" checked>
        <label for="showTrend">Show trend line</label>
      </div>
    </div>"""

    cbs      = make_checkboxes(plotted)
    fname    = "chart_phillips"
    chart_js = (
        f"var fig = {fig.to_json()};\n"
        f"Plotly.newPlot('chart', fig.data, fig.layout, {{responsive:true}});\n"
        f"var TRACE_NAMES = {json.dumps(plotted)};\n"
        f"var TREND_IDX = {TREND_IDX};\n"
        f"var ALL_DATA = {json.dumps(all_data)};\n"
        + EXPORT_JS.replace("%%FNAME%%", fname)
        + SEARCH_JS
    )

    # JS quadratic regression (Gauss elimination on 3x3 normal equations)
    ctrl_js = """\
/* ---- Polynomial regression (degree 2) ---- */
function polyfit2(xs, ys) {
  var n = xs.length;
  if (n < 5) return null;
  var s0=n, s1=0, s2=0, s3=0, s4=0, t1=0, t2=0, t3=0;
  for (var i=0; i<n; i++) {
    var x=xs[i], y=ys[i];
    s1+=x; s2+=x*x; s3+=x*x*x; s4+=x*x*x*x;
    t1+=y; t2+=x*y; t3+=x*x*y;
  }
  var A = [
    [s0, s1, s2, t1],
    [s1, s2, s3, t2],
    [s2, s3, s4, t3]
  ];
  for (var col=0; col<3; col++) {
    for (var row=col+1; row<3; row++) {
      var f = A[row][col] / A[col][col];
      for (var k=col; k<=3; k++) A[row][k] -= f * A[col][k];
    }
  }
  var c2 = A[2][3]/A[2][2];
  var c1 = (A[1][3]-A[1][2]*c2)/A[1][1];
  var c0 = (A[0][3]-A[0][1]*c1-A[0][2]*c2)/A[0][0];
  return [c2, c1, c0]; // a*x^2 + b*x + c  (highest degree first)
}

function evalPoly(coeffs, xArr) {
  return xArr.map(function(x) {
    return coeffs[0]*x*x + coeffs[1]*x + coeffs[2];
  });
}

function linspace(lo, hi, n) {
  var step = (hi-lo)/(n-1), arr = [];
  for (var i=0; i<n; i++) arr.push(lo + i*step);
  return arr;
}

/* ---- Filter and update chart ---- */
function getVisible() {
  return Array.from(document.querySelectorAll('.ccb:checked')).map(function(c){return c.value;});
}

function applyFilter() {
  var yMin = parseInt(document.getElementById('yrMin').value);
  var yMax = parseInt(document.getElementById('yrMax').value);
  if (yMin > yMax) { alert('Min year must be <= max year.'); return; }

  var updates = {x:[], y:[], text:[]};
  var allXvis = [], allYvis = [];

  TRACE_NAMES.forEach(function(name, i) {
    var d = ALL_DATA[name];
    var xs=[], ys=[], ts=[];
    d.years.forEach(function(yr, j) {
      if (yr >= yMin && yr <= yMax) {
        xs.push(d.x[j]); ys.push(d.y[j]); ts.push(d.text[j]);
      }
    });
    updates.x.push(xs); updates.y.push(ys); updates.text.push(ts);
    var cb = document.querySelector('.ccb[value="'+name+'"]');
    if (cb && cb.checked) { allXvis = allXvis.concat(xs); allYvis = allYvis.concat(ys); }
  });
  Plotly.restyle('chart', updates, TRACE_NAMES.map(function(_,i){return i;}));

  // Update trend line
  updateTrend(allXvis, allYvis);

  // Re-apply country visibility
  TRACE_NAMES.forEach(function(name, i) {
    var cb = document.querySelector('.ccb[value="'+name+'"]');
    Plotly.restyle('chart', {visible: (cb && cb.checked) ? true : 'legendonly'}, [i]);
  });
}

function updateTrend(xs, ys) {
  var showTrend = document.getElementById('showTrend').checked;
  if (!showTrend || xs.length < 5) {
    Plotly.restyle('chart', {visible: false}, [TREND_IDX]);
    return;
  }
  var coeffs = polyfit2(xs, ys);
  if (!coeffs) { Plotly.restyle('chart', {visible: false}, [TREND_IDX]); return; }
  var xMin = Math.min.apply(null, xs), xMax = Math.max.apply(null, xs);
  var xFit = linspace(xMin, xMax, 200);
  var yFit = evalPoly(coeffs, xFit);
  Plotly.restyle('chart', {x:[xFit], y:[yFit], visible:true}, [TREND_IDX]);
}

/* ---- Country toggle ---- */
function onCbChange(cb) {
  var idx = TRACE_NAMES.indexOf(cb.value);
  if (idx < 0) return;
  Plotly.restyle('chart', {visible: cb.checked ? true : 'legendonly'}, [idx]);
  // Recompute trend from currently visible + filtered data
  var yMin = parseInt(document.getElementById('yrMin').value);
  var yMax = parseInt(document.getElementById('yrMax').value);
  var allX=[], allY=[];
  document.querySelectorAll('.ccb:checked').forEach(function(c) {
    var d = ALL_DATA[c.value];
    if (!d) return;
    d.years.forEach(function(yr,j){
      if (yr>=yMin && yr<=yMax){allX.push(d.x[j]); allY.push(d.y[j]);}
    });
  });
  updateTrend(allX, allY);
}

function selAll() {
  document.querySelectorAll('.ccb').forEach(function(c){c.checked=true;});
  applyFilter();
}
function selNone() {
  document.querySelectorAll('.ccb').forEach(function(c){c.checked=false;});
  Plotly.restyle('chart', {visible:'legendonly'},
    TRACE_NAMES.map(function(_,i){return i;}));
  Plotly.restyle('chart', {visible:false}, [TREND_IDX]);
}

document.querySelectorAll('.ccb').forEach(function(c){
  c.addEventListener('change', function(){onCbChange(c);});
});
document.getElementById('showTrend').addEventListener('change', function() {
  var yMin = parseInt(document.getElementById('yrMin').value);
  var yMax = parseInt(document.getElementById('yrMax').value);
  var allX=[], allY=[];
  document.querySelectorAll('.ccb:checked').forEach(function(c){
    var d=ALL_DATA[c.value]; if(!d) return;
    d.years.forEach(function(yr,j){
      if(yr>=yMin&&yr<=yMax){allX.push(d.x[j]);allY.push(d.y[j]);}
    });
  });
  updateTrend(allX, allY);
});
"""

    html = (PAGE_TEMPLATE
            .replace("%%TITLE%%",      "Unemployment vs. Inflation")
            .replace("%%SUBTITLE%%",   "Phillips Curve | World Bank")
            .replace("%%CHECKBOXES%%", cbs)
            .replace("%%EXTRA_CTRL%%", extra_ctrl)
            .replace("%%SOURCE_HTML%%", SOURCE_PHILLIPS)
            .replace("%%CHART_JS%%",   chart_js)
            .replace("%%CTRL_JS%%",    ctrl_js))

    out = DOCS_DIR / "chart_phillips.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Saved -> {out.relative_to(REPO_ROOT)}")


# -- Main ---------------------------------------------------------------------
def main():
    print("=" * 55)
    print("ECON 10 - Building inflation & unemployment charts")
    print("=" * 55)

    print("\n[1/3] Inflation rate -- line chart")
    build_line_chart(
        "inflation_wb.csv",
        "Inflation Rate",
        "Inflation Rate (%)",
        "chart_inflation.html",
        source_html=SOURCE_INFLATION,
    )

    print("\n[2/3] Unemployment rate -- line chart")
    build_line_chart(
        "unemployment_wb.csv",
        "Unemployment Rate",
        "Unemployment Rate (%)",
        "chart_unemployment.html",
        source_html=SOURCE_UNEMPLOYMENT,
    )

    print("\n[3/3] Phillips curve -- scatter with trend")
    build_phillips_chart()

    print("\nAll charts saved to docs/econ10/")


if __name__ == "__main__":
    main()
