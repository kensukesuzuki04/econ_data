#!/usr/bin/env python3
"""
build_charts_capital_wage.py
---------------------------------------------
Build ECON 206 interactive scatter: real capital per worker vs. real wage per worker (US).

Source: Penn World Tables 11.0 (pwt110.xlsx)
  rnna  -- Capital stock at constant 2021 national prices (mil. 2021 USD)
  emp   -- Persons engaged (millions)
  labsh -- Labour share of GDP at current national prices
  rgdpna-- Real GDP at constant 2021 national prices (mil. 2021 USD)

Derived series:
  x = rnna / emp          real capital per worker (2021 USD)
  y = labsh * rgdpna / emp real wage per worker   (2021 USD)

Output:
    docs/econ206/chart_capital_wage_us.html

Usage:
    python scripts/econ206/build_charts_capital_wage.py
"""

import json
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / "data"  / "econ206"
DOCS_DIR  = REPO_ROOT / "docs"  / "econ206"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

FONT_FAMILY  = "Helvetica Neue, Helvetica, Arial, sans-serif"
SINGLE_COLOR = "#1f77b4"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def hex_to_rgba(hex_color: str, alpha: float = 0.35) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def poly2_fit(xs, ys):
    if len(xs) < 5:
        return None, None, None
    coeffs  = np.polyfit(xs, ys, 2)
    x_range = np.linspace(min(xs), max(xs), 200)
    y_fit   = np.polyval(coeffs, x_range)
    return coeffs, x_range.tolist(), y_fit.tolist()


def base_layout(**kwargs):
    defaults = dict(
        margin=dict(l=75, r=20, t=35, b=65),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        hovermode="closest",
        showlegend=False,
        font=dict(family=FONT_FAMILY, size=12),
    )
    defaults.update(kwargs)
    return go.Layout(**defaults)


# ---------------------------------------------------------------------------
# JS blocks
# ---------------------------------------------------------------------------
EXPORT_JS = """\
function dlPNG(){Plotly.downloadImage('chart',{format:'png',filename:'chart_capital_wage_us',width:1400,height:700,scale:2});}
function dlSVG(){Plotly.downloadImage('chart',{format:'svg',filename:'chart_capital_wage_us',width:1400,height:700});}
"""

# Opens a new window with an SVG snapshot sized for letter landscape —
# the user can inspect the layout and then print/save as PDF from there.
PRINT_PREVIEW_JS = r"""
function openPrintPreview(){
  Plotly.toImage('chart',{format:'svg',width:960,height:580}).then(function(dataUrl){
    var win=window.open('','_blank');
    win.document.write('<!DOCTYPE html><html><head>'
      +'<meta charset="UTF-8">'
      +'<title>Print Preview \u2014 Capital vs. Wage (US, PWT 11.0)</title>'
      +'<style>'
      +'*{box-sizing:border-box;margin:0;padding:0}'
      +'body{background:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif}'
      +'.bar{background:#8b0000;color:#fff;padding:.5rem 1rem;display:flex;'
      +'  align-items:center;gap:.7rem;position:sticky;top:0;z-index:10}'
      +'.bar span{font-size:.8rem;font-weight:600;flex:1}'
      +'.pbtn{font-size:.75rem;padding:.3rem .8rem;border:1px solid rgba(255,255,255,.4);'
      +'  border-radius:3px;background:transparent;color:#fff;cursor:pointer}'
      +'.pbtn:hover{background:rgba(255,255,255,.15)}'
      +'.page{background:#fff;width:10in;min-height:7.5in;margin:.4in auto;'
      +'  padding:.5in .6in;box-shadow:0 2px 16px rgba(0,0,0,.25)}'
      +'.caption{font-size:.72rem;color:#555;margin-top:.4rem;line-height:1.5}'
      +'@media print{'
      +'  .bar{display:none}'
      +'  body{background:#fff}'
      +'  .page{margin:0;padding:.3in .4in;box-shadow:none;width:100%}'
      +'}'
      +'</style></head><body>'
      +'<div class="bar">'
      +'  <span>Print Preview \u2014 Real Capital vs. Real Wage, United States (PWT 11.0)</span>'
      +'  <button class="pbtn" onclick="window.print()">&#128438; Print / Save PDF</button>'
      +'  <button class="pbtn" onclick="window.close()">&#x2715; Close</button>'
      +'</div>'
      +'<div class="page">'
      +'  <img src="'+dataUrl+'" style="width:100%;height:auto;display:block">'
      +'  <p class="caption">Source: Penn World Tables 11.0 (Feenstra, Inklaar &amp; Timmer, 2015).'
      +'  Real capital per worker = <em>rnna</em> / <em>emp</em>.'
      +'  Real wage per worker = <em>labsh</em> &times; <em>rgdpna</em> / <em>emp</em>.'
      +'  All values in 2021 USD.</p>'
      +'</div>'
      +'</body></html>');
    win.document.close();
  });
}
"""

CTRL_JS = r"""
function polyfit2(xs,ys){
  var n=xs.length;if(n<5)return null;
  var s0=n,s1=0,s2=0,s3=0,s4=0,t1=0,t2=0,t3=0;
  for(var i=0;i<n;i++){var x=xs[i],y=ys[i];
    s1+=x;s2+=x*x;s3+=x*x*x;s4+=x*x*x*x;t1+=y;t2+=x*y;t3+=x*x*y;}
  var A=[[s0,s1,s2,t1],[s1,s2,s3,t2],[s2,s3,s4,t3]];
  for(var col=0;col<3;col++)for(var row=col+1;row<3;row++){
    var f=A[row][col]/A[col][col];
    for(var k=col;k<=3;k++)A[row][k]-=f*A[col][k];}
  var c2=A[2][3]/A[2][2],c1=(A[1][3]-A[1][2]*c2)/A[1][1],
      c0=(A[0][3]-A[0][1]*c1-A[0][2]*c2)/A[0][0];
  return [c2,c1,c0];}
function evalPoly(c,x){return x.map(function(v){return c[0]*v*v+c[1]*v+c[2];});}
function linspace(a,b,n){var s=(b-a)/(n-1),r=[];for(var i=0;i<n;i++)r.push(a+i*s);return r;}

function updateTrend(xs,ys){
  var ok=document.getElementById('showTrend').checked;
  if(!ok||xs.length<5){Plotly.restyle('chart',{visible:false},[TREND_IDX]);return;}
  var c=polyfit2(xs,ys);if(!c){Plotly.restyle('chart',{visible:false},[TREND_IDX]);return;}
  var lo=Math.min.apply(null,xs),hi=Math.max.apply(null,xs),xf=linspace(lo,hi,200);
  Plotly.restyle('chart',{x:[xf],y:[evalPoly(c,xf)],visible:true},[TREND_IDX]);}

function getFiltered(){
  var y0=parseInt(document.getElementById('yrMin').value);
  var y1=parseInt(document.getElementById('yrMax').value);
  var xs=[],ys=[],ts=[],hs=[];
  ALL_DATA.years.forEach(function(yr,j){
    if(yr>=y0&&yr<=y1){
      xs.push(ALL_DATA.x[j]);ys.push(ALL_DATA.y[j]);
      ts.push(ALL_DATA.text[j]);hs.push(ALL_DATA.hoverText[j]);}});
  return {xs:xs,ys:ys,ts:ts,hs:hs};}

function applyFilter(){
  var y0=parseInt(document.getElementById('yrMin').value);
  var y1=parseInt(document.getElementById('yrMax').value);
  if(y0>y1){alert('Min year must be \u2264 max year.');return;}
  var f=getFiltered();
  var showLbl=document.getElementById('showLabels').checked;
  Plotly.restyle('chart',{x:[f.xs],y:[f.ys],text:[f.ts],customdata:[f.hs],
    mode:[showLbl?'markers+text':'markers']},[0]);
  var showConn=document.getElementById('showConn').checked;
  Plotly.restyle('chart',{x:[f.xs],y:[f.ys],visible:showConn},[LINE_IDX]);
  updateTrend(f.xs,f.ys);}

document.getElementById('showLabels').addEventListener('change',function(){
  var show=this.checked;
  Plotly.restyle('chart',{mode:[show?'markers+text':'markers']},[0]);});

document.getElementById('showTrend').addEventListener('change',function(){
  var f=getFiltered();updateTrend(f.xs,f.ys);});

document.getElementById('showConn').addEventListener('change',function(){
  var show=this.checked;
  var f=getFiltered();
  Plotly.restyle('chart',{visible:show,x:[f.xs],y:[f.ys]},[LINE_IDX]);});
"""


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
def build_capital_wage_us():
    pwt_path = DATA_DIR / "pwt110.xlsx"
    if not pwt_path.exists():
        sys.exit(f"ERROR: {pwt_path} not found.")

    df = pd.read_excel(pwt_path, sheet_name="Data")
    us = (df[df["countrycode"] == "USA"]
            [["year", "rnna", "emp", "labsh", "rgdpna"]]
            .dropna()
            .sort_values("year"))

    us["k_per_worker"] = us["rnna"]   / us["emp"]
    us["real_wage"]    = us["labsh"]  * us["rgdpna"] / us["emp"]
    us = us.dropna(subset=["k_per_worker", "real_wage"])

    xs    = us["k_per_worker"].round(0).tolist()
    ys    = us["real_wage"].round(0).tolist()
    years = us["year"].astype(int).tolist()

    hover_texts = [
        f"<b>United States, {yr}</b><br>"
        f"Capital per Worker: ${k:,.0f}<br>"
        f"Real Wage per Worker: ${w:,.0f}"
        for yr, k, w in zip(years, xs, ys)
    ]

    all_data = {
        "x": xs, "y": ys, "years": years,
        "text":      [str(yr) for yr in years],
        "hoverText": hover_texts,
    }

    fig = go.Figure()

    # Scatter trace (markers only by default; labels toggled via JS)
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers",
        name="United States",
        text=[str(yr) for yr in years],
        textposition="top center",
        textfont=dict(size=7, color=SINGLE_COLOR),
        customdata=hover_texts,
        hovertemplate="%{customdata}<extra></extra>",
        showlegend=False,
        marker=dict(color=SINGLE_COLOR, size=9, line=dict(color="white", width=0.5)),
    ))

    # Connecting line trace (hidden by default)
    LINE_IDX = 1
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines",
        line=dict(color=hex_to_rgba(SINGLE_COLOR, 0.35), width=1.5),
        showlegend=False, hoverinfo="skip", visible=False,
    ))

    # Polynomial fitted line
    _, x_fit, y_fit = poly2_fit(xs, ys)
    TREND_IDX = 2
    fig.add_trace(go.Scatter(
        x=x_fit or [], y=y_fit or [],
        name="Fitted Line (2nd order polynomial)",
        mode="lines", line=dict(color="#333", width=2, dash="dash"),
        hoverinfo="skip", showlegend=True, visible=True,
    ))

    ymin, ymax = min(years), max(years)

    fig.update_layout(base_layout(
        xaxis=dict(
            title="Real Capital per Worker (2021 USD)",
            gridcolor="#f0f0f0", zeroline=False,
            tickprefix="$", tickformat="~s",
        ),
        yaxis=dict(
            title="Real Wage per Worker (2021 USD)",
            gridcolor="#f0f0f0", zeroline=False,
            tickprefix="$", tickformat="~s",
        ),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0, font=dict(size=10),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#ddd", borderwidth=1,
        ),
    ))

    chart_js = (
        f"var fig={fig.to_json()};\n"
        f"Plotly.newPlot('chart',fig.data,fig.layout,{{responsive:true}});\n"
        f"var ALL_DATA={json.dumps(all_data)};\n"
        f"var TREND_IDX={TREND_IDX};\n"
        f"var LINE_IDX={LINE_IDX};\n"
        + EXPORT_JS
        + PRINT_PREVIEW_JS
    )

    sidebar = f"""\
    <div>
      <div class="ctrl-hd">Year Range</div>
      <div class="yr-row">
        <input type="number" id="yrMin" value="{ymin}" min="{ymin}" max="{ymax}">
        <span>-</span>
        <input type="number" id="yrMax" value="{ymax}" min="{ymin}" max="{ymax}">
      </div>
      <button class="apply-btn" onclick="applyFilter()">Apply</button>
      <div class="trend-row">
        <input type="checkbox" id="showTrend" checked>
        <label for="showTrend">Show fitted line</label>
      </div>
      <div class="trend-row">
        <input type="checkbox" id="showLabels">
        <label for="showLabels">Show year labels</label>
      </div>
      <div class="trend-row">
        <input type="checkbox" id="showConn">
        <label for="showConn">Connect by year</label>
      </div>
    </div>
    <div class="src-section">
      <div class="ctrl-hd">Data Source</div>
      <p>Penn World Tables 11.0<br>
      Feenstra, Inklaar &amp; Timmer (2015)<br>
      <em>American Economic Review</em><br>
      Coverage: United States, {ymin}&ndash;{ymax}</p>
      <p style="margin-top:.5rem">
      <b>x</b>: <code>rnna / emp</code><br>
      Capital stock / workers<br>
      <b>y</b>: <code>labsh &times; rgdpna / emp</code><br>
      Labour share &times; GDP / workers
      </p>
      <a href="https://www.rug.nl/ggdc/productivity/pwt/" target="_blank">PWT&nbsp;11.0 &rarr;</a>
    </div>"""

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Real Capital Stock vs. Real Wage (United States) | ECON 206 | Clark University</title>
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
.tbtn.preview{{border-color:#8b0000;color:#8b0000;font-weight:600}}
.tbtn.preview:hover{{background:#8b0000;color:#fff}}
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
.trend-row{{display:flex;align-items:center;gap:.35rem;margin-top:.5rem}}
.trend-row input{{accent-color:#8b0000;cursor:pointer}}
.trend-row label{{font-size:.76rem;cursor:pointer}}
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
  <h1>Real Capital Stock vs. Real Wage &mdash; United States</h1>
  <span class="sub">Penn World Tables 11.0 &nbsp;|&nbsp; {ymin}&ndash;{ymax}</span>
  <a class="back" href="../index.html">&larr; All Charts</a>
</header>
<div class="toolbar">
  <span>Export:</span>
  <button class="tbtn" onclick="dlPNG()">PNG</button>
  <button class="tbtn" onclick="dlSVG()">SVG</button>
  <button class="tbtn preview" onclick="openPrintPreview()">&#128438; Preview &amp; Print PDF</button>
</div>
<div class="layout">
  <aside class="sidebar">
{sidebar}
  </aside>
  <div class="chart-wrap"><div id="chart"></div></div>
</div>
<footer>
  Source: Penn World Tables 11.0 (Feenstra, Inklaar &amp; Timmer, 2015) &nbsp;|&nbsp;
  ECON 206 &ndash; Macroeconomic Theory &nbsp;|&nbsp;
  &copy; 2026 Kensuke Suzuki, Clark University
</footer>
<script>
{chart_js}
{CTRL_JS}
</script>
</body>
</html>"""

    out = DOCS_DIR / "chart_capital_wage_us.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Saved -> {out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    print("=" * 55)
    print("ECON 206 - Building capital stock vs. wage chart")
    print("=" * 55)
    print("\n[1/1] Capital per worker vs. real wage -- US (PWT 11.0)")
    build_capital_wage_us()
    print("\nDone.")
