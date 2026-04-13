# Economics Data Visualizations

**Kensuke Suzuki** | Department of Economics | Clark University

Interactive visualizations to accompany undergraduate economics courses.
Charts are self-contained HTML files built with Python and Plotly — open in any browser, no installation required.

**Live site:** https://kensukesuzuki04.github.io/econ_data/

---

## Courses

| Course | Title | Level | Visualizations |
|--------|-------|-------|----------------|
| [ECON 10](docs/econ10/) | Introductory Economics | Undergraduate | Inflation, Unemployment, 3× Phillips Curve |
| [ECON 206](docs/econ206/) | Intermediate Macroeconomics | Undergraduate | *(coming soon)* |

---

## Repository Structure

```
econ_data/
│
├── data/                                Raw CSV data, organized by course
│   ├── econ10/
│   │   ├── inflation_wb.csv             Inflation rate, all countries (World Bank)
│   │   ├── unemployment_wb.csv          Unemployment rate, all countries (World Bank / ILO)
│   │   ├── phillips_fred_us.csv         US unemployment + CPI inflation (FRED, 1948–present)
│   │   ├── unemployment_oecd.csv        OECD harmonized unemployment, 32 countries (FRED)
│   │   └── phillips_oecd.csv            OECD unemployment + WB CPI merged (1960–2024)
│   └── econ206/
│
├── scripts/
│   ├── econ10/
│   │   ├── collect_data_wb.py
│   │   │     Downloads inflation + unemployment from World Bank API.
│   │   │     Output → data/econ10/inflation_wb.csv
│   │   │              data/econ10/unemployment_wb.csv
│   │   │
│   │   ├── collect_data_fred.py
│   │   │     Downloads UNRATE + CPIAUCSL from FRED (no API key needed).
│   │   │     Converts monthly series to annual averages; computes YoY CPI inflation.
│   │   │     Output → data/econ10/phillips_fred_us.csv
│   │   │
│   │   ├── collect_data_oecd.py
│   │   │     Downloads OECD harmonized unemployment from FRED per country.
│   │   │     Merges with World Bank CPI inflation.
│   │   │     Must run collect_data_wb.py first (needs inflation_wb.csv).
│   │   │     Output → data/econ10/unemployment_oecd.csv
│   │   │              data/econ10/phillips_oecd.csv
│   │   │
│   │   └── build_charts_inflation_unemployment.py
│   │         Reads all CSVs, builds 5 interactive Plotly charts.
│   │         Output → docs/econ10/chart_inflation.html
│   │                  docs/econ10/chart_unemployment.html
│   │                  docs/econ10/chart_phillips_wb.html
│   │                  docs/econ10/chart_phillips_us.html
│   │                  docs/econ10/chart_phillips_oecd.html
│   │
│   └── econ206/
│
├── docs/                                GitHub Pages root
│   ├── index.html                       Landing page — all courses
│   ├── econ10/
│   │   ├── chart_inflation.html         Line chart — CPI inflation, 175 countries
│   │   ├── chart_unemployment.html      Line chart — unemployment, 141 countries
│   │   ├── chart_phillips_wb.html       Scatter — Phillips curve, World Bank, 1991+
│   │   ├── chart_phillips_us.html       Scatter — Phillips curve, US only, 1948+
│   │   └── chart_phillips_oecd.html     Scatter — Phillips curve, OECD, 1960+
│   └── econ206/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## File Naming Conventions

Scripts use a two-part pattern:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `collect_data_<source>.py` | Download raw data from an API | `collect_data_wb.py` |
| `build_chart_<topic>.py` | Read CSVs, produce HTML charts | `build_charts_inflation_unemployment.py` |

Output HTML files:

| Pattern | Example |
|---------|---------|
| `chart_<topic>.html` | `chart_inflation.html` |
| `chart_<topic>_<variant>.html` | `chart_phillips_wb.html`, `chart_phillips_us.html` |

Data CSV files:

| Pattern | Example |
|---------|---------|
| `<topic>_<source>.csv` | `inflation_wb.csv` (`wb` = World Bank) |
| `<topic>_<source>_<region>.csv` | `phillips_fred_us.csv` |

---

## Workflow: Adding a New Visualization

1. **Collect data** — add `collect_data_<source>.py` under `scripts/<course>/`.
   Save output CSV to `data/<course>/`.

2. **Build chart** — add or update `build_chart_<topic>.py` to read the CSV
   and write a self-contained HTML file to `docs/<course>/`.

3. **Register the chart** — add a card to `docs/index.html` following the
   existing card structure (`.chart-card` with `.tags` and `.src` divs).

4. **Commit and push** — live at
   `https://kensukesuzuki04.github.io/econ_data/<course>/chart_<topic>.html`.

---

## Running the Scripts

```bash
# Install dependencies (Python 3, pinned Plotly < 6.0)
pip install -r requirements.txt

# ECON 10 — step 1: collect data (run in order)
python scripts/econ10/collect_data_wb.py       # World Bank inflation + unemployment
python scripts/econ10/collect_data_fred.py     # FRED US unemployment + CPI
python scripts/econ10/collect_data_oecd.py     # OECD harmonized unemployment (needs WB first)

# ECON 10 — step 2: build all 5 charts
python scripts/econ10/build_charts_inflation_unemployment.py
```

On Windows, `python` may resolve to the Windows Store stub. Use the full path if needed:

```bash
C:/Users/KensukeSuzuki/AppData/Local/Python/bin/python.exe scripts/econ10/...
```

---

## Data Sources

| Source | Access | Used for |
|--------|--------|---------|
| [World Bank Open Data](https://data.worldbank.org/) | Free REST API, no key | Inflation (CPI), Unemployment (ILO) |
| [FRED (St. Louis Fed)](https://fred.stlouisfed.org/) | Free direct-CSV endpoint, no key | US unemployment + CPI; OECD harmonized unemployment |

### World Bank indicators

| Indicator | Description | Coverage |
|-----------|-------------|---------|
| `FP.CPI.TOTL.ZG` | Inflation, consumer prices (annual %) | 175 countries, 1960–2024 |
| `SL.UEM.TOTL.ZS` | Unemployment, total (% of labor force, ILO modeled estimate) | 141 countries, **1991–2024** |

> **Note:** The World Bank ILO-modeled unemployment estimates begin in 1991.
> There is no global cross-country unemployment series before that year.
> For longer historical coverage, use FRED data (US) or OECD harmonized series.

### FRED series

| Series | Description | Coverage |
|--------|-------------|---------|
| `UNRATE` | Civilian unemployment rate, monthly SA | US, 1948–present |
| `CPIAUCSL` | CPI for All Urban Consumers, monthly | US, 1947–present |
| `LRHUTTTT{ISO2}M156S` | OECD harmonized unemployment, monthly SA | 32 of 38 OECD members |

OECD members **not available** on FRED: COL, CRI, LVA, LTU, NZL, CHE.

FRED direct-CSV endpoint (no API key required):
```
https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}
```
Column header in the downloaded CSV is `observation_date` (not `DATE`).

---

## Design Preferences

These apply to all chart HTML files and the index page.

### Typography
- **Font family:** `'Helvetica Neue', Helvetica, Arial, sans-serif` — used for all body text, labels, axes, tooltips, and UI controls. Applied in both the HTML/CSS (`font-family`) and the Plotly layout (`font=dict(family=...)`). Do not use serif fonts.
- **Font size:** 12px base for chart axis labels (`font=dict(family=..., size=12)` in Plotly layout). UI controls use `0.72rem`–`0.78rem`. Footer uses `0.68rem`.

### Color palette
- **Header / brand color:** `#8b0000` (dark red — Clark University).
- **Header border:** `#5a0000`.
- **Link color in header nav:** `#ffd0d0` (hover → `#fff`).
- **Background:** `#fafaf8` (off-white).
- **Chart background:** `#fff`.
- **Accent (checkboxes, buttons):** `#8b0000`.
- **Trace palette** (20-color cycle): `["#1f77b4","#d62728","#2ca02c","#ff7f0e","#9467bd", "#8c564b","#e377c2","#17becf","#bcbd22","#636363", "#4e79a7","#f28e2b","#59a14f","#e15759","#76b7b2", "#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ac"]`

### Chart style
- **Line width:** 2.5px for country traces.
- **Scatter marker size:** 9px (WB/OECD Phillips), 11px (US Phillips with year labels).
- Scatter dots show **year labels** in the same color as the dot, `size=7`, `textposition="top center"`.
- **Fitted line label:** "Fitted Line (2nd order polynomial)" — do not use "trend line" (misleading for a cross-sectional scatter).
- Sidebar checkbox "Show fitted line" (not "Show trend line").
- **Legend:** hidden for all country/region traces (`showlegend=False`). Only the fitted line appears in the legend. For the US Phillips chart, decades appear in a vertical legend inside the plot area (useful because there are only ~9 entries).
- **Grid:** `#f0f0f0`. Zero line: `#ddd`, width 1.

### Sidebar / layout
- Sidebar width: 200px, min 170px.
- Sections: Countries/Decades (with search), Year Range filter, Show fitted line toggle, Data Source (always last, `margin-top: auto`).
- Export buttons: PNG, SVG, Print/PDF in toolbar above chart.

---

## Known Issues and Data Notes

### OECD SDMX API — do not use

The official OECD SDMX-JSON API at `stats.oecd.org` is **unreliable and not recommended**.

Endpoints tested and their outcomes:

| Endpoint | Result |
|----------|--------|
| `stats.oecd.org/SDMX-JSON/data/MEI/{countries}.LRHUTTFE.ST.A/all` | 404 |
| `stats.oecd.org/SDMX-JSON/data/LRHU/...` | 404 |
| `sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DF_DP_LIVE,...` | Returns MEI_BTS_COS (business surveys), not unemployment levels |
| `stats.oecd.org/SDMX-JSON/data/ALFS_SUMTAB/...` | 200 OK, but `UNE_LF` measure only has growth-rate (`G1`) transformation — no unemployment rate levels |
| `stats.oecd.org/SDMX-JSON/data/KEI/...` | 200 OK, 500k+ obs, but data structure difficult to parse; wrong measure codes returned |
| `stats.oecd.org/SDMX-JSON/data/STLABOUR/...` | 200 OK, 1.1M+ obs; not reliably filterable by country/measure |

**Solution:** Use FRED, which hosts OECD harmonized unemployment (`LRHUTTTT{ISO2}M156S`) for 32 of 38 OECD members. This is simpler, more reliable, and has better historical coverage (back to 1955 for major economies).

### Plotly version

Pin Plotly to `< 6.0`. Plotly 6 changed the `to_json()` output format in ways that break the inline `var fig = ...` pattern used in these charts.

```
plotly>=5.0,<6.0
```

### Python on Windows

The `python` command on Windows may resolve to the Microsoft Store stub (returns nothing). Use the full path:

```
C:/Users/KensukeSuzuki/AppData/Local/Python/bin/python.exe
```

---

## Tech Stack

| Tool | Role |
|------|------|
| Python 3.14 | Data collection and chart generation |
| pandas | Data processing |
| Plotly (pinned `<6.0`) | Interactive charts |
| requests | HTTP data fetching |
| NumPy | Polynomial fitting |
| GitHub Pages (`/docs` folder, `main` branch) | Hosting |

Charts embed Plotly via CDN (`plotly-2.27.0.min.js`) — no server required, files open offline.

---

## GitHub Pages Setup

Pages are served from the `docs/` folder on the `main` branch.
To enable: **Settings → Pages → Branch: main, Folder: /docs**.

---

*&copy; 2026, Kensuke Suzuki, Clark University. All Rights Reserved.*
