#!/usr/bin/env python3
"""
build_charts_inflation_unemployment.py
────────────────────────────────────────
Build three interactive Plotly charts for ECON 10 (Inflation & Unemployment):

    1. chart_inflation.html      — line chart, inflation rate by country
    2. chart_unemployment.html   — line chart, unemployment rate by country
    3. chart_phillips.html       — scatter, unemployment × inflation (Phillips curve)

Each chart is a self-contained HTML file (Plotly via CDN, no server needed).
Interactive controls: country checkboxes; year-range filter on Phillips chart.

Prerequisites
    pip install pandas plotly requests
    python scripts/econ10/collect_data_wb.py   # download data first

Usage
    python scripts/econ10/build_charts_inflation_unemployment.py

Output
    docs/econ10/chart_inflation.html
    docs/econ10/chart_unemployment.html
    docs/econ10/chart_phillips.html
"""

import json
import sys
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / "data" / "econ10"
DOCS_DIR  = REPO_ROOT / "docs" / "econ10"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# ── Country display names (order sets legend order) ───────────────────────────
COUNTRY_ORDER = [
    "United States", "Germany", "Japan", "China", "Brazil",
    "India", "United Kingdom", "Mexico", "South Korea", "Turkey",
    "Argentina", "South Africa", "France", "Canada",
]

# Qualitative color palette (one color per country, colorblind-considerate)
PALETTE = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
    "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#636363",
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759",
]
COLOR = {name: PALETTE[i % len(PALETTE)] for i, name in enumerate(COUNTRY_ORDER)}

START_YEAR = 1990
END_YEAR   = 2023

# ── HTML page template ────────────────────────────────────────────────────────
# Uses %%PLACEHOLDER%% tokens — avoids f-string conflicts with CSS braces.

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
body{font-family:'Arial',sans-serif;background:#fafaf8;color:#1a1a1a;
     height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{background:#8b0000;color:#fff;padding:.85rem 1.3rem;
       border-bottom:3px solid #5a0000;display:flex;align-items:baseline;
       gap:.8rem;flex-shrink:0}
header h1{font-size:1rem;font-weight:bold;letter-spacing:.02em}
header .sub{font-size:.78rem;opacity:.78}
.back{font-size:.75rem;color:#ffd0d0;text-decoration:none;margin-left:auto}
.back:hover{color:#fff}
.layout{display:flex;flex:1;overflow:hidden}
.sidebar{width:185px;min-width:155px;background:#fff;border-right:1px solid #e0e0e0;
         padding:.9rem .85rem;overflow-y:auto;flex-shrink:0}
.ctrl-hd{font-size:.68rem;font-weight:bold;letter-spacing:.1em;text-transform:uppercase;
         color:#8b0000;margin-bottom:.45rem}
.btn-row{display:flex;gap:.35rem;margin-bottom:.55rem}
.btn-row button{font-size:.7rem;padding:.13rem .38rem;border:1px solid #ccc;
                border-radius:3px;background:#fff;cursor:pointer;color:#555}
.btn-row button:hover{border-color:#8b0000;color:#8b0000}
.cb-label{display:flex;align-items:center;gap:.3rem;font-size:.78rem;
          padding:.22rem 0;cursor:pointer;line-height:1.3}
.cb-label input{accent-color:#8b0000;flex-shrink:0}
.yr-section{margin-top:1rem;padding-top:.85rem;border-top:1px solid #eee}
.yr-row{display:flex;align-items:center;gap:.3rem;margin-top:.35rem}
.yr-row input{width:54px;font-size:.76rem;padding:.18rem .28rem;border:1px solid #ccc;
              border-radius:3px;text-align:center}
.yr-row span{font-size:.72rem;color:#666}
.apply-btn{margin-top:.45rem;font-size:.73rem;padding:.22rem .6rem;
           background:#8b0000;color:#fff;border:none;border-radius:3px;cursor:pointer}
.apply-btn:hover{background:#a00000}
.chart-wrap{flex:1;overflow:hidden;display:flex;flex-direction:column;padding:.4rem}
#chart{width:100%;flex:1}
footer{font-size:.7rem;color:#aaa;text-align:center;padding:.4rem;
       border-top:1px solid #eee;flex-shrink:0}
</style>
</head>
<body>
<header>
  <h1>%%TITLE%%</h1>
  <span class="sub">%%SUBTITLE%%</span>
  <a class="back" href="index.html">← ECON 10</a>
</header>
<div class="layout">
  <aside class="sidebar">
    <div class="ctrl-hd">Countries</div>
    <div class="btn-row">
      <button onclick="selAll()">All</button>
      <button onclick="selNone()">None</button>
    </div>
%%CHECKBOXES%%
%%YEAR_CONTROLS%%
  </aside>
  <div class="chart-wrap">
    <div id="chart"></div>
  </div>
</div>
<footer>
  Source: World Bank Open Data &nbsp;|&nbsp;
  ECON 10 – Introductory Economics &nbsp;|&nbsp;
  &copy; 2026 Kensuke Suzuki, Clark University
</footer>
<script>
%%CHART_JS%%
%%CTRL_JS%%
</script>
</body>
</html>
"""


def render_page(title, subtitle, fig, country_names,
                chart_type="line", all_data=None):
    """
    Render a full HTML page from a Plotly figure.

    chart_type : 'line' or 'phillips'
    all_data   : dict  {country_name: {x, y, years, text}}  — required for phillips
    """
    # Checkboxes
    checkboxes = "\n".join(
        f'    <label class="cb-label">'
        f'<input type="checkbox" class="ccb" value="{n}" checked> {n}'
        f'</label>'
        for n in country_names
    )

    # Year-range controls (Phillips only)
    year_controls = ""
    if chart_type == "phillips":
        year_controls = f"""\
    <div class="yr-section">
      <div class="ctrl-hd">Year Range</div>
      <div class="yr-row">
        <input type="number" id="yrMin" value="{START_YEAR}"
               min="{START_YEAR}" max="{END_YEAR}">
        <span>–</span>
        <input type="number" id="yrMax" value="{END_YEAR}"
               min="{START_YEAR}" max="{END_YEAR}">
      </div>
      <button class="apply-btn" onclick="applyFilter()">Apply</button>
    </div>"""

    # Embed figure + trace-name list
    trace_names_js = json.dumps(country_names)
    chart_js = (
        f"var fig = {fig.to_json()};\n"
        f"Plotly.newPlot('chart', fig.data, fig.layout, {{responsive: true}});\n"
        f"var TRACE_NAMES = {trace_names_js};\n"
    )
    if chart_type == "phillips" and all_data:
        chart_js += f"var ALL_DATA = {json.dumps(all_data)};\n"

    # Control JS
    if chart_type == "line":
        ctrl_js = """\
function onCbChange(cb) {
    var idx = TRACE_NAMES.indexOf(cb.value);
    if (idx === -1) return;
    Plotly.restyle('chart', {visible: cb.checked ? true : 'legendonly'}, [idx]);
}
function selAll() {
    var vis = TRACE_NAMES.map(function() { return true; });
    Plotly.restyle('chart', {visible: vis}, TRACE_NAMES.map(function(_, i) { return i; }));
    document.querySelectorAll('.ccb').forEach(function(c) { c.checked = true; });
}
function selNone() {
    var vis = TRACE_NAMES.map(function() { return 'legendonly'; });
    Plotly.restyle('chart', {visible: vis}, TRACE_NAMES.map(function(_, i) { return i; }));
    document.querySelectorAll('.ccb').forEach(function(c) { c.checked = false; });
}
document.querySelectorAll('.ccb').forEach(function(c) {
    c.addEventListener('change', function() { onCbChange(c); });
});"""
    else:  # phillips
        ctrl_js = """\
function applyFilter() {
    var yMin = parseInt(document.getElementById('yrMin').value);
    var yMax = parseInt(document.getElementById('yrMax').value);
    if (yMin > yMax) { alert('Min year must be \u2264 max year.'); return; }
    var updates = {x: [], y: [], text: []};
    TRACE_NAMES.forEach(function(name) {
        var d = ALL_DATA[name];
        var xs = [], ys = [], ts = [];
        d.years.forEach(function(yr, i) {
            if (yr >= yMin && yr <= yMax) {
                xs.push(d.x[i]); ys.push(d.y[i]); ts.push(d.text[i]);
            }
        });
        updates.x.push(xs); updates.y.push(ys); updates.text.push(ts);
    });
    Plotly.restyle('chart', updates, TRACE_NAMES.map(function(_, i) { return i; }));
    // Re-apply visibility
    TRACE_NAMES.forEach(function(name, i) {
        var cb = document.querySelector('.ccb[value="' + name + '"]');
        Plotly.restyle('chart', {visible: (cb && cb.checked) ? true : 'legendonly'}, [i]);
    });
}
function onCbChange(cb) {
    var idx = TRACE_NAMES.indexOf(cb.value);
    if (idx === -1) return;
    Plotly.restyle('chart', {visible: cb.checked ? true : 'legendonly'}, [idx]);
}
function selAll() {
    document.querySelectorAll('.ccb').forEach(function(c) { c.checked = true; });
    applyFilter();
}
function selNone() {
    document.querySelectorAll('.ccb').forEach(function(c) { c.checked = false; });
    var vis = TRACE_NAMES.map(function() { return 'legendonly'; });
    Plotly.restyle('chart', {visible: vis}, TRACE_NAMES.map(function(_, i) { return i; }));
}
document.querySelectorAll('.ccb').forEach(function(c) {
    c.addEventListener('change', function() { onCbChange(c); });
});"""

    html = PAGE_TEMPLATE
    html = html.replace("%%TITLE%%",         title)
    html = html.replace("%%SUBTITLE%%",      subtitle)
    html = html.replace("%%CHECKBOXES%%",    checkboxes)
    html = html.replace("%%YEAR_CONTROLS%%", year_controls)
    html = html.replace("%%CHART_JS%%",      chart_js)
    html = html.replace("%%CTRL_JS%%",       ctrl_js)
    return html


# ── Shared layout defaults ────────────────────────────────────────────────────
def base_layout(**kwargs):
    defaults = dict(
        margin=dict(l=55, r=20, t=40, b=70),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, font=dict(size=11)),
        font=dict(family="Arial", size=12),
    )
    defaults.update(kwargs)
    return go.Layout(**defaults)


# ── Chart 1 & 2: Line charts ──────────────────────────────────────────────────
def build_line_chart(csv_name: str, title: str, y_label: str, html_name: str):
    csv_path = DATA_DIR / csv_name
    if not csv_path.exists():
        sys.exit(f"  ERROR: {csv_path} not found. Run collect_data_wb.py first.")

    df = pd.read_csv(csv_path)
    fig = go.Figure()
    names = []

    for country in COUNTRY_ORDER:
        sub = df[df["country"] == country].sort_values("year")
        if sub.empty:
            continue
        names.append(country)
        fig.add_trace(go.Scatter(
            x=sub["year"].tolist(),
            y=sub["value"].round(2).tolist(),
            name=country,
            mode="lines+markers",
            line=dict(color=COLOR[country], width=2),
            marker=dict(size=5),
            hovertemplate=(
                f"<b>{country}</b><br>"
                "Year: %{x}<br>"
                f"{y_label}: %{{y:.1f}}%"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(base_layout(
        xaxis=dict(
            title="Year",
            tickformat="d",
            gridcolor="#f0f0f0",
            rangeslider=dict(visible=True, thickness=0.06),
        ),
        yaxis=dict(
            title=y_label,
            gridcolor="#f0f0f0",
            zeroline=True,
            zerolinecolor="#ccc",
            zerolinewidth=1,
        ),
    ))

    html  = render_page(title, f"{y_label} · 1990–2023 · World Bank", fig, names)
    out   = DOCS_DIR / html_name
    out.write_text(html, encoding="utf-8")
    print(f"  Saved → {out.relative_to(REPO_ROOT)}")


# ── Chart 3: Phillips curve scatter ──────────────────────────────────────────
def build_phillips_chart():
    inf_path   = DATA_DIR / "inflation_wb.csv"
    unemp_path = DATA_DIR / "unemployment_wb.csv"
    for p in (inf_path, unemp_path):
        if not p.exists():
            sys.exit(f"  ERROR: {p} not found. Run collect_data_wb.py first.")

    inf_df   = pd.read_csv(inf_path).rename(columns={"value": "inflation"})
    unemp_df = pd.read_csv(unemp_path).rename(columns={"value": "unemployment"})
    merged   = (pd.merge(inf_df, unemp_df, on=["country", "year"])
                  .dropna(subset=["inflation", "unemployment"]))

    fig      = go.Figure()
    names    = []
    all_data = {}

    for country in COUNTRY_ORDER:
        sub = merged[merged["country"] == country].sort_values("year")
        if sub.empty:
            continue
        names.append(country)

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
            hovertemplate="%{text}<extra></extra>",
            marker=dict(
                color=COLOR[country],
                size=7,
                line=dict(color="white", width=0.5),
            ),
        ))

    fig.update_layout(base_layout(
        xaxis=dict(
            title="Unemployment Rate (%)",
            gridcolor="#f0f0f0",
            zeroline=False,
        ),
        yaxis=dict(
            title="Inflation Rate (%)",
            gridcolor="#f0f0f0",
            zeroline=True,
            zerolinecolor="#ccc",
            zerolinewidth=1,
        ),
        shapes=[dict(
            type="line", x0=0, x1=1, xref="paper",
            y0=0, y1=0, yref="y",
            line=dict(color="#bbb", width=1, dash="dash"),
        )],
    ))

    html = render_page(
        "Unemployment vs. Inflation",
        "Phillips Curve · 1990–2023 · World Bank",
        fig, names,
        chart_type="phillips",
        all_data=all_data,
    )
    out = DOCS_DIR / "chart_phillips.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Saved → {out.relative_to(REPO_ROOT)}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("ECON 10 – Building inflation & unemployment charts")
    print("=" * 55)

    print("\n[1/3] Inflation rate — line chart")
    build_line_chart(
        "inflation_wb.csv",
        "Inflation Rate",
        "Inflation Rate (%)",
        "chart_inflation.html",
    )

    print("\n[2/3] Unemployment rate — line chart")
    build_line_chart(
        "unemployment_wb.csv",
        "Unemployment Rate",
        "Unemployment Rate (%)",
        "chart_unemployment.html",
    )

    print("\n[3/3] Phillips curve — scatter")
    build_phillips_chart()

    print("\nAll charts saved to docs/econ10/")
    print("Push with: git add docs/econ10/ data/econ10/ && git commit -m 'Add inflation/unemployment charts' && git push")


if __name__ == "__main__":
    main()
