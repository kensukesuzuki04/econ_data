#!/usr/bin/env python3
"""
build_charts_inflation_unemployment.py
----------------------------------------
Build five interactive Plotly charts for ECON 10 (Inflation & Unemployment).

    1. chart_inflation.html       -- line chart, inflation rate by country (WB)
    2. chart_unemployment.html    -- line chart, unemployment rate by country (WB)
    3. chart_phillips_wb.html     -- Phillips scatter, all countries, 1991+ (WB)
    4. chart_phillips_us.html     -- Phillips scatter, US only, 1948+ (FRED)
    5. chart_phillips_oecd.html   -- Phillips scatter, OECD members, 1960+ (FRED+WB)

Prerequisites
    pip install pandas plotly requests numpy
    python scripts/econ10/collect_data_wb.py
    python scripts/econ10/collect_data_fred.py
    python scripts/econ10/collect_data_oecd.py

Usage
    python scripts/econ10/build_charts_inflation_unemployment.py

Output
    docs/econ10/chart_inflation.html
    docs/econ10/chart_unemployment.html
    docs/econ10/chart_phillips_wb.html
    docs/econ10/chart_phillips_us.html
    docs/econ10/chart_phillips_oecd.html
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

PALETTE = [
    "#1f77b4","#d62728","#2ca02c","#ff7f0e","#9467bd",
    "#8c564b","#e377c2","#17becf","#bcbd22","#636363",
    "#4e79a7","#f28e2b","#59a14f","#e15759","#76b7b2",
    "#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac",
]

FONT_FAMILY = "Helvetica Neue, Helvetica, Arial, sans-serif"

DECADE_COLORS = {
    "1890s": "#c7c7c7", "1900s": "#969696", "1910s": "#636363",
    "1920s": "#fdae6b", "1930s": "#e6550d",
    "1940s": "#aec7e8", "1950s": "#1f77b4", "1960s": "#2ca02c",
    "1970s": "#ff7f0e", "1980s": "#d62728", "1990s": "#9467bd",
    "2000s": "#8c564b", "2010s": "#17becf", "2020s": "#e377c2",
}

# Single color used for US-only scatter plots (no decade coloring)
SINGLE_COLOR = "#1f77b4"

# -- Helpers ------------------------------------------------------------------
def hex_to_rgba(hex_color: str, alpha: float = 0.35) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def load_countries(csv_path: Path) -> list:
    df = pd.read_csv(csv_path)
    names = sorted(df["country"].unique().tolist())
    if US_NAME in names:
        names.remove(US_NAME)
        names = [US_NAME] + names
    return names


def color_map(country_names: list) -> dict:
    return {n: PALETTE[i % len(PALETTE)] for i, n in enumerate(country_names)}


def make_checkboxes(names: list, default: str = US_NAME) -> str:
    lines = []
    for name in names:
        checked = "checked" if name == default else ""
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


# -- Page template ------------------------------------------------------------
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
body{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;
     background:#fafaf8;color:#1a1a1a;height:100vh;
     display:flex;flex-direction:column;overflow:hidden}
header{background:#8b0000;color:#fff;padding:.75rem 1.2rem;
       border-bottom:3px solid #5a0000;display:flex;align-items:center;
       gap:.8rem;flex-shrink:0}
header h1{font-size:.98rem;font-weight:600;letter-spacing:.01em}
header .sub{font-size:.76rem;opacity:.75}
.back{font-size:.74rem;color:#ffd0d0;text-decoration:none;margin-left:auto;white-space:nowrap}
.back:hover{color:#fff}
.toolbar{display:flex;align-items:center;gap:.5rem;padding:.45rem 1.2rem;
         background:#fff;border-bottom:1px solid #e8e8e8;flex-shrink:0}
.toolbar span{font-size:.72rem;color:#888;margin-right:.2rem}
.tbtn{font-size:.72rem;padding:.22rem .65rem;border:1px solid #ccc;border-radius:3px;
      background:#fff;cursor:pointer;color:#444;font-family:inherit}
.tbtn:hover{border-color:#8b0000;color:#8b0000}
.layout{display:flex;flex:1;overflow:hidden}
.sidebar{width:200px;min-width:170px;background:#fff;border-right:1px solid #e0e0e0;
         padding:.85rem .8rem;overflow-y:auto;flex-shrink:0;
         display:flex;flex-direction:column;gap:.7rem}
.ctrl-hd{font-size:.67rem;font-weight:600;letter-spacing:.1em;
         text-transform:uppercase;color:#8b0000}
.search-box{width:100%;font-size:.78rem;padding:.28rem .45rem;border:1px solid #ccc;
            border-radius:3px;font-family:inherit}
.search-box:focus{outline:none;border-color:#8b0000}
.btn-row{display:flex;gap:.35rem}
.sbtn{font-size:.7rem;padding:.13rem .38rem;border:1px solid #ccc;border-radius:3px;
      background:#fff;cursor:pointer;color:#555;font-family:inherit}
.sbtn:hover{border-color:#8b0000;color:#8b0000}
.cb-list{flex:1;overflow-y:auto}
.cb-wrap{display:flex;align-items:center;gap:.3rem;padding:.2rem 0}
.cb-wrap input{accent-color:#8b0000;flex-shrink:0;cursor:pointer}
.cb-wrap label{font-size:.78rem;line-height:1.3;cursor:pointer}
.cb-wrap.hidden{display:none}
.yr-section{padding-top:.7rem;border-top:1px solid #eee}
.yr-row{display:flex;align-items:center;gap:.3rem;margin-top:.35rem}
.yr-row input{width:56px;font-size:.76rem;padding:.18rem .28rem;border:1px solid #ccc;
              border-radius:3px;text-align:center;font-family:inherit}
.yr-row span{font-size:.72rem;color:#666}
.apply-btn{width:100%;margin-top:.45rem;font-size:.74rem;padding:.25rem 0;
           background:#8b0000;color:#fff;border:none;border-radius:3px;
           cursor:pointer;font-family:inherit}
.apply-btn:hover{background:#a00000}
.trend-row{display:flex;align-items:center;gap:.35rem;margin-top:.5rem}
.trend-row input{accent-color:#8b0000;cursor:pointer}
.trend-row label{font-size:.76rem;cursor:pointer}
.src-section{padding-top:.7rem;border-top:1px solid #eee;margin-top:auto}
.src-section .ctrl-hd{margin-bottom:.35rem}
.src-section p{font-size:.72rem;color:#555;line-height:1.5}
.src-section a{color:#1f77b4;font-size:.72rem}
.chart-wrap{flex:1;overflow:hidden;display:flex;flex-direction:column;padding:.35rem}
#chart{width:100%;flex:1}
footer{font-size:.68rem;color:#aaa;text-align:center;padding:.35rem;
       border-top:1px solid #eee;flex-shrink:0}
@media print{
  header .back,.toolbar,.sidebar,footer{display:none}
  body{overflow:visible;height:auto}.layout{display:block}
  .chart-wrap{padding:0}#chart{width:100% !important;height:90vh !important}}
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
      <div class="ctrl-hd">%%SIDEBAR_LABEL%%</div>
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
  <div class="chart-wrap"><div id="chart"></div></div>
</div>
<footer>
  Source: %%FOOTER_SOURCE%% &nbsp;|&nbsp;
  ECON 10 &ndash; Economics and the World Economy &nbsp;|&nbsp;
  &copy; 2026 Kensuke Suzuki, Clark University
</footer>
<script>
%%CHART_JS%%
%%CTRL_JS%%
</script>
</body>
</html>
"""

EXPORT_JS = """\
function dlPNG(){Plotly.downloadImage('chart',{format:'png',filename:'%%FNAME%%',width:1400,height:700,scale:2});}
function dlSVG(){Plotly.downloadImage('chart',{format:'svg',filename:'%%FNAME%%',width:1400,height:700});}
"""

SEARCH_JS = """\
function filterSearch(q){
  q=q.toLowerCase().trim();
  document.querySelectorAll('#cb-list .cb-wrap').forEach(function(w){
    w.classList.toggle('hidden',q!==''&&!w.dataset.name.includes(q));});}
"""

# -- Data source blocks -------------------------------------------------------
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

SOURCE_PHILLIPS_WB = """\
      <p>World Bank Open Data<br>
      Unemployment: <code>SL.UEM.TOTL.ZS</code><br>
      Inflation: <code>FP.CPI.TOTL.ZG</code><br>
      Coverage: 175 countries, 1991&ndash;2024</p>
      <a href="https://data.worldbank.org"
         target="_blank">View on World Bank &rarr;</a>"""

SOURCE_PHILLIPS_OECD = """\
      <p>OECD harmonized unemployment (via FRED)<br>
      Series: <code>LRHUTTTT{ISO2}M156S</code><br>
      Inflation: World Bank <code>FP.CPI.TOTL.ZG</code><br>
      Coverage: 32 OECD members, 1960&ndash;2024</p>
      <a href="https://fred.stlouisfed.org"
         target="_blank">View on FRED &rarr;</a>"""

SOURCE_PHILLIPS_US = """\
      <p>U.S. Bureau of Labor Statistics via FRED<br>
      Unemployment: <code>UNRATE</code> (monthly SA,<br>
      &nbsp;&nbsp;annual average)<br>
      Inflation: from <code>CPIAUCSL</code> (CPI all<br>
      &nbsp;&nbsp;urban consumers, annual YoY&nbsp;%)<br>
      Coverage: United States, 1948&ndash;present</p>
      <a href="https://fred.stlouisfed.org/series/UNRATE"
         target="_blank">UNRATE on FRED &rarr;</a>"""

SOURCE_PHILLIPS_US_HIST = """\
      <p><b>Pre-1948 (estimates)</b><br>
      Unemployment: Lebergott (1964),<br>
      &nbsp;&nbsp;Manpower in Economic Growth,<br>
      &nbsp;&nbsp;Table A-3. Annual.<br>
      CPI: Robert Shiller / Yale<br>
      &nbsp;&nbsp;ie_data.xls, annual avg YoY&nbsp;%<br>
      <em>Note: Romer (1986) offers alternative<br>
      unemployment estimates (generally lower).</em></p>
      <p style="margin-top:.5rem"><b>Post-1947 (official)</b><br>
      FRED <code>UNRATE</code> &times; <code>CPIAUCSL</code></p>
      <a href="https://fred.stlouisfed.org/series/UNRATE"
         target="_blank">UNRATE on FRED &rarr;</a>"""


# -- Line charts --------------------------------------------------------------
def build_line_chart(csv_name, title, y_label, html_name, source_html=""):
    csv_path = DATA_DIR / csv_name
    if not csv_path.exists():
        sys.exit(f"ERROR: {csv_path} not found. Run collect_data_wb.py first.")

    df      = pd.read_csv(csv_path)
    names   = load_countries(csv_path)
    cmap    = color_map(names)
    fig     = go.Figure()
    plotted = []

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

    fname    = html_name.replace(".html", "")
    cbs      = make_checkboxes(plotted)
    chart_js = (
        f"var fig={fig.to_json()};\n"
        f"Plotly.newPlot('chart',fig.data,fig.layout,{{responsive:true}});\n"
        f"var TRACE_NAMES={json.dumps(plotted)};\n"
        + EXPORT_JS.replace("%%FNAME%%", fname)
        + SEARCH_JS
    )
    ctrl_js = """\
function onCbChange(cb){
  var idx=TRACE_NAMES.indexOf(cb.value); if(idx<0) return;
  Plotly.restyle('chart',{visible:cb.checked?true:'legendonly'},[idx]);}
function selAll(){
  Plotly.restyle('chart',{visible:TRACE_NAMES.map(function(){return true;})},
    TRACE_NAMES.map(function(_,i){return i;}));
  document.querySelectorAll('.ccb').forEach(function(c){c.checked=true;});}
function selNone(){
  Plotly.restyle('chart',{visible:TRACE_NAMES.map(function(){return 'legendonly';})},
    TRACE_NAMES.map(function(_,i){return i;}));
  document.querySelectorAll('.ccb').forEach(function(c){c.checked=false;});}
document.querySelectorAll('.ccb').forEach(function(c){
  c.addEventListener('change',function(){onCbChange(c);});});
"""
    html = (PAGE_TEMPLATE
            .replace("%%TITLE%%",        title)
            .replace("%%SUBTITLE%%",     f"{y_label} | World Bank")
            .replace("%%SIDEBAR_LABEL%%","Countries")
            .replace("%%CHECKBOXES%%",   cbs)
            .replace("%%EXTRA_CTRL%%",   "")
            .replace("%%SOURCE_HTML%%",  source_html)
            .replace("%%FOOTER_SOURCE%%","World Bank Open Data (data.worldbank.org)")
            .replace("%%CHART_JS%%",     chart_js)
            .replace("%%CTRL_JS%%",      ctrl_js))
    (DOCS_DIR / html_name).write_text(html, encoding="utf-8")
    print(f"  Saved -> {(DOCS_DIR / html_name).relative_to(REPO_ROOT)}")


# -- Phillips curve: shared helpers -------------------------------------------
def poly2_fit(xs, ys):
    if len(xs) < 5:
        return None, None, None
    coeffs  = np.polyfit(xs, ys, 2)
    x_range = np.linspace(min(xs), max(xs), 200)
    y_fit   = np.polyval(coeffs, x_range)
    return coeffs, x_range.tolist(), y_fit.tolist()


def _phillips_extra_ctrl(ymin, ymax):
    return (
        f'    <div class="yr-section">\n'
        f'      <div class="ctrl-hd">Year Range</div>\n'
        f'      <div class="yr-row">\n'
        f'        <input type="number" id="yrMin" value="{ymin}" '
        f'min="{ymin}" max="{ymax}">\n'
        f'        <span>-</span>\n'
        f'        <input type="number" id="yrMax" value="{ymax}" '
        f'min="{ymin}" max="{ymax}">\n'
        f'      </div>\n'
        f'      <button class="apply-btn" onclick="applyFilter()">Apply</button>\n'
        f'      <div class="trend-row">\n'
        f'        <input type="checkbox" id="showTrend" checked>\n'
        f'        <label for="showTrend">Show fitted line</label>\n'
        f'      </div>\n'
        f'      <div class="trend-row">\n'
        f'        <input type="checkbox" id="showLabels">\n'
        f'        <label for="showLabels">Show year labels</label>\n'
        f'      </div>\n'
        f'      <div class="trend-row">\n'
        f'        <input type="checkbox" id="showConn">\n'
        f'        <label for="showConn">Connect by year</label>\n'
        f'      </div>\n'
        f'    </div>'
    )


# Shared Phillips JS (poly regression + year filter + trend + label + connect toggling)
_PJS = [
    "function polyfit2(xs,ys){",
    "var n=xs.length;if(n<5)return null;",
    "var s0=n,s1=0,s2=0,s3=0,s4=0,t1=0,t2=0,t3=0;",
    "for(var i=0;i<n;i++){var x=xs[i],y=ys[i];",
    "s1+=x;s2+=x*x;s3+=x*x*x;s4+=x*x*x*x;t1+=y;t2+=x*y;t3+=x*x*y;}",
    "var A=[[s0,s1,s2,t1],[s1,s2,s3,t2],[s2,s3,s4,t3]];",
    "for(var col=0;col<3;col++)for(var row=col+1;row<3;row++){",
    "var f=A[row][col]/A[col][col];",
    "for(var k=col;k<=3;k++)A[row][k]-=f*A[col][k];}",
    "var c2=A[2][3]/A[2][2],c1=(A[1][3]-A[1][2]*c2)/A[1][1],",
    "c0=(A[0][3]-A[0][1]*c1-A[0][2]*c2)/A[0][0];return [c2,c1,c0];}",
    "function evalPoly(c,x){return x.map(function(v){return c[0]*v*v+c[1]*v+c[2];});}",
    "function linspace(a,b,n){var s=(b-a)/(n-1),r=[];for(var i=0;i<n;i++)r.push(a+i*s);return r;}",
    "function updateTrend(xs,ys){",
    "var ok=document.getElementById('showTrend').checked;",
    "if(!ok||xs.length<5){Plotly.restyle('chart',{visible:false},[TREND_IDX]);return;}",
    "var c=polyfit2(xs,ys);if(!c){Plotly.restyle('chart',{visible:false},[TREND_IDX]);return;}",
    "var lo=Math.min.apply(null,xs),hi=Math.max.apply(null,xs),xf=linspace(lo,hi,200);",
    "Plotly.restyle('chart',{x:[xf],y:[evalPoly(c,xf)],visible:true},[TREND_IDX]);}",
    # helper: update line-connection traces after a filter/toggle
    "function updateConnLines(showConn,y0,y1){",
    "if(typeof LINE_IDXS==='undefined')return;",
    "var lineUpd={x:[],y:[]},lineIdxArr=[];",
    "TRACE_NAMES.forEach(function(nm){",
    "var d=ALL_DATA[nm],xs=[],ys=[];",
    "d.years.forEach(function(yr,j){if(yr>=y0&&yr<=y1){xs.push(d.x[j]);ys.push(d.y[j]);}});",
    "lineUpd.x.push(xs);lineUpd.y.push(ys);lineIdxArr.push(LINE_IDXS[nm]);});",
    "Plotly.restyle('chart',lineUpd,lineIdxArr);",
    "TRACE_NAMES.forEach(function(nm){",
    "var cb=document.querySelector('.ccb[value=\"'+nm+'\"]');",
    "Plotly.restyle('chart',{visible:(showConn&&cb&&cb.checked)?true:false},[LINE_IDXS[nm]]);});}",
    "function applyFilter(){",
    "var y0=parseInt(document.getElementById('yrMin').value);",
    "var y1=parseInt(document.getElementById('yrMax').value);",
    "if(y0>y1){alert('Min year must be <= max year.');return;}",
    "var upd={x:[],y:[],text:[],customdata:[]},axv=[],ayv=[];",
    "TRACE_NAMES.forEach(function(nm,i){",
    "var d=ALL_DATA[nm],xs=[],ys=[],ts=[],hs=[];",
    "d.years.forEach(function(yr,j){if(yr>=y0&&yr<=y1){xs.push(d.x[j]);ys.push(d.y[j]);ts.push(d.text[j]);hs.push(d.hoverText?d.hoverText[j]:d.text[j]);}});",
    "upd.x.push(xs);upd.y.push(ys);upd.text.push(ts);upd.customdata.push(hs);",
    "var cb=document.querySelector('.ccb[value=\"'+nm+'\"]');",
    "if(cb&&cb.checked){axv=axv.concat(xs);ayv=ayv.concat(ys);}});",
    "Plotly.restyle('chart',upd,TRACE_NAMES.map(function(_,i){return i;}));",
    "var showConn=document.getElementById('showConn')&&document.getElementById('showConn').checked;",
    "updateConnLines(showConn,y0,y1);",
    "updateTrend(axv,ayv);",
    "TRACE_NAMES.forEach(function(nm,i){",
    "var cb=document.querySelector('.ccb[value=\"'+nm+'\"]');",
    "Plotly.restyle('chart',{visible:(cb&&cb.checked)?true:'legendonly'},[i]);});}",
    "function onCbChange(cb){",
    "var idx=TRACE_NAMES.indexOf(cb.value);if(idx<0)return;",
    "Plotly.restyle('chart',{visible:cb.checked?true:'legendonly'},[idx]);",
    "if(typeof LINE_IDXS!=='undefined'){",
    "var showConn=document.getElementById('showConn')&&document.getElementById('showConn').checked;",
    "Plotly.restyle('chart',{visible:(cb.checked&&showConn)?true:false},[LINE_IDXS[cb.value]]);}",
    "var y0=parseInt(document.getElementById('yrMin').value);",
    "var y1=parseInt(document.getElementById('yrMax').value);",
    "var ax=[],ay=[];",
    "document.querySelectorAll('.ccb:checked').forEach(function(c){",
    "var d=ALL_DATA[c.value];if(!d)return;",
    "d.years.forEach(function(yr,j){if(yr>=y0&&yr<=y1){ax.push(d.x[j]);ay.push(d.y[j]);}});});",
    "updateTrend(ax,ay);}",
    "function selAll(){document.querySelectorAll('.ccb').forEach(function(c){c.checked=true;});applyFilter();}",
    "function selNone(){",
    "document.querySelectorAll('.ccb').forEach(function(c){c.checked=false;});",
    "Plotly.restyle('chart',{visible:'legendonly'},TRACE_NAMES.map(function(_,i){return i;}));",
    "if(typeof LINE_IDXS!=='undefined'){",
    "Plotly.restyle('chart',{visible:false},Object.values(LINE_IDXS));}",
    "Plotly.restyle('chart',{visible:false},[TREND_IDX]);}",
    "document.querySelectorAll('.ccb').forEach(function(c){c.addEventListener('change',function(){onCbChange(c);});});",
    "document.getElementById('showTrend').addEventListener('change',function(){",
    "var y0=parseInt(document.getElementById('yrMin').value);",
    "var y1=parseInt(document.getElementById('yrMax').value);",
    "var ax=[],ay=[];",
    "document.querySelectorAll('.ccb:checked').forEach(function(c){",
    "var d=ALL_DATA[c.value];if(!d)return;",
    "d.years.forEach(function(yr,j){if(yr>=y0&&yr<=y1){ax.push(d.x[j]);ay.push(d.y[j]);}});});",
    "updateTrend(ax,ay);});",
    "document.getElementById('showLabels').addEventListener('change',function(){",
    "var show=this.checked;",
    "var idxs=TRACE_NAMES.map(function(_,i){return i;});",
    "Plotly.restyle('chart',{mode:show?'markers+text':'markers'},idxs);});",
    "document.getElementById('showConn').addEventListener('change',function(){",
    "var show=this.checked;",
    "var y0=parseInt(document.getElementById('yrMin').value);",
    "var y1=parseInt(document.getElementById('yrMax').value);",
    "updateConnLines(show,y0,y1);});",
]
PHILLIPS_JS = "\n".join(_PJS)


def _build_phillips_multi(merged, title, subtitle, html_name,
                          source_html, default_country=US_NAME,
                          footer_source="World Bank Open Data (data.worldbank.org)"):
    names = sorted(merged["country"].unique().tolist())
    if default_country in names:
        names.remove(default_country)
        names = [default_country] + names
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
        texts = [f"<b>{country}</b><br>Year: {yr}<br>"
                 f"Unemployment: {u:.1f}%<br>Inflation: {v:.1f}%"
                 for yr, u, v in zip(years, xs, ys)]
        all_data[country] = {"x": xs, "y": ys, "years": years,
                             "text": [str(yr) for yr in years], "hoverText": texts}
        fig.add_trace(go.Scatter(
            x=xs, y=ys, name=country, mode="markers",
            text=[str(yr) for yr in years],
            textposition="top center",
            textfont=dict(size=12, color=cmap[country]),
            customdata=texts,
            visible=True if country == default_country else "legendonly",
            showlegend=False,
            hovertemplate="%{customdata}<extra></extra>",
            marker=dict(color=cmap[country], size=9,
                        line=dict(color="white", width=0.5)),
        ))

    # -- connecting line traces (hidden by default, one per country) -----------
    line_idxs = {}
    for i, country in enumerate(plotted):
        d = all_data[country]
        line_idxs[country] = len(plotted) + i
        fig.add_trace(go.Scatter(
            x=d["x"], y=d["y"], name=country,
            mode="lines",
            line=dict(color=hex_to_rgba(cmap[country], 0.35), width=1.5),
            showlegend=False, hoverinfo="skip", visible=False,
        ))

    def_data = all_data.get(default_country, {})
    _, x_fit, y_fit = poly2_fit(def_data.get("x", []), def_data.get("y", []))
    TREND_IDX = len(plotted) * 2
    fig.add_trace(go.Scatter(
        x=x_fit or [], y=y_fit or [], name="Fitted Line (2nd order polynomial)",
        mode="lines", line=dict(color="#333", width=2, dash="dash"),
        hoverinfo="skip", showlegend=True, visible=True,
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

    fname    = html_name.replace(".html", "")
    cbs      = make_checkboxes(plotted, default_country)
    chart_js = (
        f"var fig={fig.to_json()};\n"
        f"Plotly.newPlot('chart',fig.data,fig.layout,{{responsive:true}});\n"
        f"var TRACE_NAMES={json.dumps(plotted)};\n"
        f"var TREND_IDX={TREND_IDX};\n"
        f"var LINE_IDXS={json.dumps(line_idxs)};\n"
        f"var ALL_DATA={json.dumps(all_data)};\n"
        + EXPORT_JS.replace("%%FNAME%%", fname)
        + SEARCH_JS
    )
    html = (PAGE_TEMPLATE
            .replace("%%TITLE%%",        title)
            .replace("%%SUBTITLE%%",     subtitle)
            .replace("%%SIDEBAR_LABEL%%","Countries")
            .replace("%%CHECKBOXES%%",   cbs)
            .replace("%%EXTRA_CTRL%%",   _phillips_extra_ctrl(ymin, ymax))
            .replace("%%SOURCE_HTML%%",  source_html)
            .replace("%%FOOTER_SOURCE%%",footer_source)
            .replace("%%CHART_JS%%",     chart_js)
            .replace("%%CTRL_JS%%",      PHILLIPS_JS))
    (DOCS_DIR / html_name).write_text(html, encoding="utf-8")
    print(f"  Saved -> {(DOCS_DIR / html_name).relative_to(REPO_ROOT)}")


# -- 1. Phillips WB: all countries, 1991+ ------------------------------------
def build_phillips_wb_chart():
    inf_path   = DATA_DIR / "inflation_wb.csv"
    unemp_path = DATA_DIR / "unemployment_wb.csv"
    for p in (inf_path, unemp_path):
        if not p.exists():
            sys.exit(f"ERROR: {p} not found. Run collect_data_wb.py first.")
    inf_df   = pd.read_csv(inf_path).rename(columns={"value": "inflation"})
    unemp_df = pd.read_csv(unemp_path).rename(columns={"value": "unemployment"})
    merged   = (pd.merge(inf_df, unemp_df, on=["country", "year"])
                  .dropna(subset=["inflation", "unemployment"]))
    _build_phillips_multi(
        merged,
        "Unemployment vs. Inflation (World Bank)",
        "Phillips Curve | World Bank, all countries, 1991+",
        "chart_phillips_wb.html",
        SOURCE_PHILLIPS_WB,
    )


# -- 2. Phillips US: FRED, 1948+, colored by decade --------------------------
def build_phillips_us_chart():
    csv_path = DATA_DIR / "phillips_fred_us.csv"
    if not csv_path.exists():
        sys.exit(f"ERROR: {csv_path} not found. Run collect_data_fred.py first.")
    df = pd.read_csv(csv_path).dropna()

    fig      = go.Figure()
    plotted  = []
    all_data = {}

    decades = sorted({f"{(yr // 10) * 10}s" for yr in df["year"]})
    for decade in decades:
        d0 = int(decade[:-1])
        sub = df[(df["year"] >= d0) & (df["year"] < d0 + 10)].sort_values("year")
        if sub.empty:
            continue
        plotted.append(decade)
        xs    = sub["unemployment"].round(2).tolist()
        ys    = sub["inflation"].round(2).tolist()
        years = sub["year"].tolist()
        texts = [f"<b>United States, {yr}</b><br>"
                 f"Unemployment: {u:.1f}%<br>Inflation: {v:.1f}%"
                 for yr, u, v in zip(years, xs, ys)]
        all_data[decade] = {"x": xs, "y": ys, "years": years,
                            "text": [str(yr) for yr in years], "hoverText": texts}
        color = SINGLE_COLOR
        fig.add_trace(go.Scatter(
            x=xs, y=ys, name=decade, mode="markers",
            text=[str(yr) for yr in years],
            textposition="top center",
            textfont=dict(size=12, color=color),
            customdata=texts,
            visible=True, showlegend=True,
            hovertemplate="%{customdata}<extra></extra>",
            marker=dict(color=color, size=11, line=dict(color="white", width=0.5)),
        ))

    # -- connecting line traces -----------------------------------------------
    line_idxs = {}
    for i, decade in enumerate(plotted):
        d = all_data[decade]
        line_idxs[decade] = len(plotted) + i
        color = SINGLE_COLOR
        fig.add_trace(go.Scatter(
            x=d["x"], y=d["y"], name=decade,
            mode="lines",
            line=dict(color=hex_to_rgba(color, 0.35), width=1.5),
            showlegend=False, hoverinfo="skip", visible=False,
        ))

    all_xs = df["unemployment"].round(2).tolist()
    all_ys = df["inflation"].round(2).tolist()
    _, x_fit, y_fit = poly2_fit(all_xs, all_ys)
    TREND_IDX = len(plotted) * 2
    fig.add_trace(go.Scatter(
        x=x_fit or [], y=y_fit or [], name="Fitted Line (2nd order polynomial)",
        mode="lines", line=dict(color="#333", width=2, dash="dash"),
        hoverinfo="skip", showlegend=True, visible=True,
    ))

    ymin = int(df["year"].min())
    ymax = int(df["year"].max())
    fig.update_layout(base_layout(
        xaxis=dict(title="Unemployment Rate (%)", gridcolor="#f0f0f0", zeroline=False),
        yaxis=dict(title="Inflation Rate (%, CPI)", gridcolor="#f0f0f0",
                   zeroline=True, zerolinecolor="#ddd", zerolinewidth=1),
        shapes=[dict(type="line", x0=0, x1=1, xref="paper",
                     y0=0, y1=0, yref="y",
                     line=dict(color="#ccc", width=1, dash="dot"))],
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="right", x=1,
                    font=dict(size=10), bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="#ddd", borderwidth=1),
    ))

    decade_cbs = "\n".join(
        f'      <div class="cb-wrap" data-name="{d.lower()}">'
        f'<input type="checkbox" class="ccb" id="cb_{d}" value="{d}" checked>'
        f'<label for="cb_{d}">{d}</label></div>'
        for d in plotted
    )
    fname    = "chart_phillips_us"
    chart_js = (
        f"var fig={fig.to_json()};\n"
        f"Plotly.newPlot('chart',fig.data,fig.layout,{{responsive:true}});\n"
        f"var TRACE_NAMES={json.dumps(plotted)};\n"
        f"var TREND_IDX={TREND_IDX};\n"
        f"var LINE_IDXS={json.dumps(line_idxs)};\n"
        f"var ALL_DATA={json.dumps(all_data)};\n"
        + EXPORT_JS.replace("%%FNAME%%", fname)
        + SEARCH_JS
    )
    html = (PAGE_TEMPLATE
            .replace("%%TITLE%%",        "Unemployment vs. Inflation (United States)")
            .replace("%%SUBTITLE%%",     "Phillips Curve | FRED, 1948-present")
            .replace("%%SIDEBAR_LABEL%%","Decades")
            .replace("%%CHECKBOXES%%",   decade_cbs)
            .replace("%%EXTRA_CTRL%%",   _phillips_extra_ctrl(ymin, ymax))
            .replace("%%SOURCE_HTML%%",  SOURCE_PHILLIPS_US)
            .replace("%%FOOTER_SOURCE%%","FRED, Federal Reserve Bank of St. Louis")
            .replace("%%CHART_JS%%",     chart_js)
            .replace("%%CTRL_JS%%",      PHILLIPS_JS))
    (DOCS_DIR / "chart_phillips_us.html").write_text(html, encoding="utf-8")
    print(f"  Saved -> {(DOCS_DIR / 'chart_phillips_us.html').relative_to(REPO_ROOT)}")


# -- 3. Phillips OECD: FRED harmonized + WB CPI, 1960+ -----------------------
def build_phillips_oecd_chart():
    csv_path = DATA_DIR / "phillips_oecd.csv"
    if not csv_path.exists():
        sys.exit(f"ERROR: {csv_path} not found. Run collect_data_oecd.py first.")
    merged = pd.read_csv(csv_path)
    _build_phillips_multi(
        merged,
        "Unemployment vs. Inflation (OECD)",
        "Phillips Curve | OECD harmonized (FRED) + World Bank CPI, 1960+",
        "chart_phillips_oecd.html",
        SOURCE_PHILLIPS_OECD,
        footer_source="FRED / OECD harmonized unemployment; World Bank CPI",
    )


# -- 4. Phillips US historical: Lebergott + Shiller + FRED, 1890+ ------------
def build_phillips_us_historical_chart():
    csv_path = DATA_DIR / "phillips_us_historical.csv"
    if not csv_path.exists():
        sys.exit(f"ERROR: {csv_path} not found. Run collect_data_historical_us.py first.")
    df = pd.read_csv(csv_path).dropna(subset=["unemployment", "inflation"])

    fig     = go.Figure()
    plotted = []
    all_data = {}

    decades = sorted({f"{(yr // 10) * 10}s" for yr in df["year"]})
    for decade in decades:
        d0  = int(decade[:-1])
        sub = df[(df["year"] >= d0) & (df["year"] < d0 + 10)].sort_values("year")
        if sub.empty:
            continue
        plotted.append(decade)
        xs    = sub["unemployment"].round(2).tolist()
        ys    = sub["inflation"].round(2).tolist()
        years = sub["year"].tolist()
        eras  = sub["era"].tolist()
        texts = [
            f"<b>United States, {yr}</b><br>"
            f"Unemployment: {u:.1f}%<br>Inflation: {v:.1f}%"
            + ("&nbsp;&nbsp;<i>(est.)</i>" if e == "estimate" else "")
            for yr, u, v, e in zip(years, xs, ys, eras)
        ]
        all_data[decade] = {"x": xs, "y": ys, "years": years,
                            "text": [str(yr) for yr in years], "hoverText": texts}
        color  = SINGLE_COLOR
        # open markers for estimates, filled for official
        is_est = all(e == "estimate" for e in eras)
        symbol = "circle-open" if is_est else "circle"
        fig.add_trace(go.Scatter(
            x=xs, y=ys, name=decade, mode="markers",
            text=[str(yr) for yr in years],
            textposition="top center",
            textfont=dict(size=12, color=color),
            customdata=texts,
            visible=True, showlegend=True,
            hovertemplate="%{customdata}<extra></extra>",
            marker=dict(color=color, size=11, symbol=symbol,
                        line=dict(color=color, width=2)),
        ))

    # -- connecting line traces -----------------------------------------------
    line_idxs = {}
    for i, decade in enumerate(plotted):
        d = all_data[decade]
        line_idxs[decade] = len(plotted) + i
        color = SINGLE_COLOR
        fig.add_trace(go.Scatter(
            x=d["x"], y=d["y"], name=decade,
            mode="lines",
            line=dict(color=hex_to_rgba(color, 0.35), width=1.5),
            showlegend=False, hoverinfo="skip", visible=False,
        ))

    all_xs = df["unemployment"].round(2).tolist()
    all_ys = df["inflation"].round(2).tolist()
    _, x_fit, y_fit = poly2_fit(all_xs, all_ys)
    TREND_IDX = len(plotted) * 2
    fig.add_trace(go.Scatter(
        x=x_fit or [], y=y_fit or [], name="Fitted Line (2nd order polynomial)",
        mode="lines", line=dict(color="#333", width=2, dash="dash"),
        hoverinfo="skip", showlegend=True, visible=True,
    ))

    ymin = int(df["year"].min())
    ymax = int(df["year"].max())
    fig.update_layout(base_layout(
        xaxis=dict(title="Unemployment Rate (%)", gridcolor="#f0f0f0", zeroline=False),
        yaxis=dict(title="Inflation Rate (%, CPI)", gridcolor="#f0f0f0",
                   zeroline=True, zerolinecolor="#ddd", zerolinewidth=1),
        shapes=[dict(type="line", x0=0, x1=1, xref="paper",
                     y0=0, y1=0, yref="y",
                     line=dict(color="#ccc", width=1, dash="dot"))],
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="right", x=1,
                    font=dict(size=10), bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="#ddd", borderwidth=1),
    ))

    # Decade checkboxes — open-circle label for pre-1948 decades
    PRE1948 = {"1890s", "1900s", "1910s", "1920s", "1930s", "1940s"}
    decade_cbs = "\n".join(
        f'      <div class="cb-wrap" data-name="{d.lower()}">'
        f'<input type="checkbox" class="ccb" id="cb_{d}" value="{d}" checked>'
        f'<label for="cb_{d}">'
        f'{d}{"&nbsp;<em style=\'font-weight:400;font-size:.7rem\'>(est.)</em>" if d in PRE1948 else ""}'
        f'</label></div>'
        for d in plotted
    )
    fname    = "chart_phillips_us_historical"
    chart_js = (
        f"var fig={fig.to_json()};\n"
        f"Plotly.newPlot('chart',fig.data,fig.layout,{{responsive:true}});\n"
        f"var TRACE_NAMES={json.dumps(plotted)};\n"
        f"var TREND_IDX={TREND_IDX};\n"
        f"var LINE_IDXS={json.dumps(line_idxs)};\n"
        f"var ALL_DATA={json.dumps(all_data)};\n"
        + EXPORT_JS.replace("%%FNAME%%", fname)
        + SEARCH_JS
    )
    html = (PAGE_TEMPLATE
            .replace("%%TITLE%%",        "Phillips Curve — US Historical (1890–present)")
            .replace("%%SUBTITLE%%",     "Lebergott (1964) + Shiller CPI pre-1948 | FRED post-1947")
            .replace("%%SIDEBAR_LABEL%%","Decades")
            .replace("%%CHECKBOXES%%",   decade_cbs)
            .replace("%%EXTRA_CTRL%%",   _phillips_extra_ctrl(ymin, ymax))
            .replace("%%SOURCE_HTML%%",  SOURCE_PHILLIPS_US_HIST)
            .replace("%%FOOTER_SOURCE%%",
                     "Lebergott (1964); Shiller/Yale CPI; FRED UNRATE + CPIAUCSL")
            .replace("%%CHART_JS%%",     chart_js)
            .replace("%%CTRL_JS%%",      PHILLIPS_JS))
    (DOCS_DIR / "chart_phillips_us_historical.html").write_text(html, encoding="utf-8")
    print(f"  Saved -> {(DOCS_DIR / 'chart_phillips_us_historical.html').relative_to(REPO_ROOT)}")


# -- 5/6. US historical line charts: unemployment & inflation, 1890+ ----------
def build_us_historical_line_chart(series: str, y_label: str, fname: str,
                                   title: str, subtitle: str,
                                   hover_est: str, hover_off: str,
                                   footer_source: str, source_html: str):
    """Generic builder for a single-series US historical line chart.

    series     : column name in phillips_us_historical.csv  ("unemployment" | "inflation")
    y_label    : y-axis title, e.g. "Unemployment Rate (%)"
    fname      : output file stem, e.g. "chart_unemployment_us_historical"
    """
    csv_path = DATA_DIR / "phillips_us_historical.csv"
    if not csv_path.exists():
        sys.exit(f"ERROR: {csv_path} not found. Run collect_data_historical_us.py first.")
    df = pd.read_csv(csv_path).dropna(subset=[series])

    df_est = df[df["era"] == "estimate"].sort_values("year")
    df_off = df[df["era"] == "official"].sort_values("year")

    x_est = df_est["year"].tolist()
    y_est = df_est[series].round(2).tolist()
    x_off = df_off["year"].tolist()
    y_off = df_off[series].round(2).tolist()

    # Prepend last estimate point to official trace for visual continuity
    if not df_est.empty:
        x_off = [int(df_est.iloc[-1]["year"])] + x_off
        y_off = [round(float(df_est.iloc[-1][series]), 2)] + y_off

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_est, y=y_est,
        name="Estimates (Lebergott / Shiller)",
        mode="lines+markers",
        line=dict(color=hex_to_rgba(SINGLE_COLOR, 0.55), width=2.5, dash="dash"),
        marker=dict(size=5, symbol="circle-open",
                    color=hex_to_rgba(SINGLE_COLOR, 0.55),
                    line=dict(color=hex_to_rgba(SINGLE_COLOR, 0.55), width=1.5)),
        hovertemplate=f"<b>%{{x}}</b><br>{y_label.split('(')[0].strip()}: %{{y:.1f}}%<br>"
                      f"<i>{hover_est}</i><extra></extra>",
        showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=x_off, y=y_off,
        name="Official (FRED)",
        mode="lines+markers",
        line=dict(color=SINGLE_COLOR, width=2.5),
        marker=dict(size=5),
        hovertemplate=f"<b>%{{x}}</b><br>{y_label.split('(')[0].strip()}: %{{y:.1f}}%<br>"
                      f"<i>{hover_off}</i><extra></extra>",
        showlegend=True,
    ))

    ymin = int(df["year"].min())
    ymax = int(df["year"].max())
    fig.update_layout(base_layout(
        xaxis=dict(title="Year", tickformat="d", gridcolor="#f0f0f0",
                   range=[ymin - 1, ymax + 1]),
        yaxis=dict(title=y_label, gridcolor="#f0f0f0",
                   zeroline=True, zerolinecolor="#ddd", zerolinewidth=1),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, font=dict(size=10),
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="#ddd", borderwidth=1),
    ))

    chart_js = (
        f"var fig={fig.to_json()};\n"
        f"Plotly.newPlot('chart',fig.data,fig.layout,{{responsive:true}});\n"
        + EXPORT_JS.replace("%%FNAME%%", fname)
    )
    ctrl_js = """\
function applyYearRange(){
  var y0=parseInt(document.getElementById('yrMin').value);
  var y1=parseInt(document.getElementById('yrMax').value);
  if(y0>y1){alert('Min year must be \u2264 max year.');return;}
  Plotly.relayout('chart',{'xaxis.range':[y0-0.5,y1+0.5]});}
document.getElementById('showEst').addEventListener('change',function(){
  Plotly.restyle('chart',{visible:this.checked?true:'legendonly'},[0]);});
"""

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | ECON 10 | Clark University</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js" charset="utf-8"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;
     background:#fafaf8;color:#1a1a1a;height:100vh;
     display:flex;flex-direction:column;overflow:hidden}}
header{{background:#8b0000;color:#fff;padding:.75rem 1.2rem;
       border-bottom:3px solid #5a0000;display:flex;align-items:center;
       gap:.8rem;flex-shrink:0}}
header h1{{font-size:.98rem;font-weight:600;letter-spacing:.01em}}
header .sub{{font-size:.76rem;opacity:.75}}
.back{{font-size:.74rem;color:#ffd0d0;text-decoration:none;margin-left:auto;white-space:nowrap}}
.back:hover{{color:#fff}}
.toolbar{{display:flex;align-items:center;gap:.5rem;padding:.45rem 1.2rem;
         background:#fff;border-bottom:1px solid #e8e8e8;flex-shrink:0}}
.toolbar span{{font-size:.72rem;color:#888;margin-right:.2rem}}
.tbtn{{font-size:.72rem;padding:.22rem .65rem;border:1px solid #ccc;border-radius:3px;
      background:#fff;cursor:pointer;color:#444;font-family:inherit}}
.tbtn:hover{{border-color:#8b0000;color:#8b0000}}
.layout{{display:flex;flex:1;overflow:hidden}}
.sidebar{{width:200px;min-width:170px;background:#fff;border-right:1px solid #e0e0e0;
         padding:.85rem .8rem;overflow-y:auto;flex-shrink:0;
         display:flex;flex-direction:column;gap:.7rem}}
.ctrl-hd{{font-size:.67rem;font-weight:600;letter-spacing:.1em;
         text-transform:uppercase;color:#8b0000}}
.yr-row{{display:flex;align-items:center;gap:.3rem;margin-top:.35rem}}
.yr-row input{{width:56px;font-size:.76rem;padding:.18rem .28rem;border:1px solid #ccc;
              border-radius:3px;text-align:center;font-family:inherit}}
.yr-row span{{font-size:.72rem;color:#666}}
.apply-btn{{width:100%;margin-top:.45rem;font-size:.74rem;padding:.25rem 0;
           background:#8b0000;color:#fff;border:none;border-radius:3px;
           cursor:pointer;font-family:inherit}}
.apply-btn:hover{{background:#a00000}}
.opt-row{{display:flex;align-items:center;gap:.35rem;margin-top:.5rem}}
.opt-row input{{accent-color:#8b0000;cursor:pointer}}
.opt-row label{{font-size:.76rem;cursor:pointer}}
.src-section{{padding-top:.7rem;border-top:1px solid #eee;margin-top:auto}}
.src-section .ctrl-hd{{margin-bottom:.35rem}}
.src-section p{{font-size:.72rem;color:#555;line-height:1.5}}
.src-section a{{color:#1f77b4;font-size:.72rem}}
.chart-wrap{{flex:1;overflow:hidden;display:flex;flex-direction:column;padding:.35rem}}
#chart{{width:100%;flex:1}}
footer{{font-size:.68rem;color:#aaa;text-align:center;padding:.35rem;
       border-top:1px solid #eee;flex-shrink:0}}
@media print{{
  header .back,.toolbar,.sidebar,footer{{display:none}}
  body{{overflow:visible;height:auto}}.layout{{display:block}}
  .chart-wrap{{padding:0}}#chart{{width:100% !important;height:90vh !important}}}}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <span class="sub">{subtitle}</span>
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
      <div class="ctrl-hd">Year Range</div>
      <div class="yr-row">
        <input type="number" id="yrMin" value="{ymin}" min="{ymin}" max="{ymax}">
        <span>-</span>
        <input type="number" id="yrMax" value="{ymax}" min="{ymin}" max="{ymax}">
      </div>
      <button class="apply-btn" onclick="applyYearRange()">Apply</button>
      <div class="opt-row">
        <input type="checkbox" id="showEst" checked>
        <label for="showEst">Show estimates</label>
      </div>
    </div>
    <div class="src-section">
      <div class="ctrl-hd">Data Source</div>
{source_html}
    </div>
  </aside>
  <div class="chart-wrap"><div id="chart"></div></div>
</div>
<footer>
  Source: {footer_source} &nbsp;|&nbsp;
  ECON 10 &ndash; Economics and the World Economy &nbsp;|&nbsp;
  &copy; 2026 Kensuke Suzuki, Clark University
</footer>
<script>
{chart_js}
{ctrl_js}
</script>
</body>
</html>"""

    (DOCS_DIR / f"{fname}.html").write_text(html, encoding="utf-8")
    print(f"  Saved -> {(DOCS_DIR / f'{fname}.html').relative_to(REPO_ROOT)}")


SOURCE_UNEMP_US_HIST = """\
      <p><b>Pre-1948 (estimates)</b><br>
      Lebergott (1964),<br>
      &nbsp;&nbsp;Manpower in Economic Growth,<br>
      &nbsp;&nbsp;Table A-3. Annual.<br>
      <em>Romer (1986) offers alternative<br>
      estimates (generally lower).</em></p>
      <p style="margin-top:.5rem"><b>Post-1947 (official)</b><br>
      FRED <code>UNRATE</code><br>
      U.S. Bureau of Labor Statistics</p>
      <a href="https://fred.stlouisfed.org/series/UNRATE"
         target="_blank">UNRATE on FRED &rarr;</a>"""

SOURCE_INF_US_HIST = """\
      <p><b>Pre-1948 (estimates)</b><br>
      Robert Shiller / Yale<br>
      &nbsp;&nbsp;ie_data.xls, annual avg YoY&nbsp;%<br>
      <em>Computed from Shiller CPI index.</em></p>
      <p style="margin-top:.5rem"><b>Post-1947 (official)</b><br>
      FRED <code>CPIAUCSL</code><br>
      U.S. Bureau of Labor Statistics</p>
      <a href="https://fred.stlouisfed.org/series/CPIAUCSL"
         target="_blank">CPIAUCSL on FRED &rarr;</a>"""


# -- Main ---------------------------------------------------------------------
def main():
    print("=" * 55)
    print("ECON 10 - Building inflation & unemployment charts")
    print("=" * 55)

    print("\n[1/6] Inflation rate -- line chart")
    build_line_chart(
        "inflation_wb.csv", "Inflation Rate",
        "Inflation Rate (%)", "chart_inflation.html",
        source_html=SOURCE_INFLATION,
    )

    print("\n[2/6] Unemployment rate -- line chart")
    build_line_chart(
        "unemployment_wb.csv", "Unemployment Rate",
        "Unemployment Rate (%)", "chart_unemployment.html",
        source_html=SOURCE_UNEMPLOYMENT,
    )

    print("\n[3/6] Phillips curve -- World Bank, all countries")
    build_phillips_wb_chart()

    print("\n[4/6] Phillips curve -- United States (FRED, 1948+)")
    build_phillips_us_chart()

    print("\n[5/6] Phillips curve -- OECD (FRED harmonized, 1960+)")
    build_phillips_oecd_chart()

    print("\n[6/8] Phillips curve -- US historical (1890+, Lebergott + Shiller)")
    build_phillips_us_historical_chart()

    print("\n[7/8] Unemployment rate -- US historical line chart (1890+)")
    build_us_historical_line_chart(
        series="unemployment",
        y_label="Unemployment Rate (%)",
        fname="chart_unemployment_us_historical",
        title="Unemployment Rate \u2014 United States (1890\u2013present)",
        subtitle="Lebergott (1964) pre-1948 \u2013 FRED UNRATE post-1947",
        hover_est="Lebergott (1964) estimate",
        hover_off="FRED UNRATE (official)",
        footer_source="Lebergott (1964); FRED UNRATE",
        source_html=SOURCE_UNEMP_US_HIST,
    )

    print("\n[8/8] Inflation rate -- US historical line chart (1890+)")
    build_us_historical_line_chart(
        series="inflation",
        y_label="Inflation Rate (%, CPI)",
        fname="chart_inflation_us_historical",
        title="Inflation Rate \u2014 United States (1890\u2013present)",
        subtitle="Shiller/Yale CPI pre-1948 \u2013 FRED CPIAUCSL post-1947",
        hover_est="Shiller/Yale CPI (estimate)",
        hover_off="FRED CPIAUCSL (official)",
        footer_source="Shiller/Yale CPI; FRED CPIAUCSL",
        source_html=SOURCE_INF_US_HIST,
    )

    print("\nAll charts saved to docs/econ10/")


if __name__ == "__main__":
    main()
