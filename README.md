# Economics Data Visualizations

**Kensuke Suzuki** | Department of Economics | Clark University

Interactive visualizations to accompany undergraduate economics courses.
Charts are self-contained HTML files built with Python and Plotly — open in any browser, no installation required.

**Live site:** https://kensukesuzuki04.github.io/econ_data/

---

## Courses

| Course | Title | Level | Visualizations |
|--------|-------|-------|----------------|
| [ECON 10](docs/econ10/) | Introductory Economics | Undergraduate | Inflation, Unemployment, Phillips Curve |
| [ECON 206](docs/econ206/) | Intermediate Macroeconomics | Undergraduate | *(coming soon)* |

---

## Repository Structure

```
econ_data/
│
├── data/                          Raw CSV data, organized by course
│   ├── econ10/
│   │   ├── inflation_wb.csv       Inflation rate by country (World Bank)
│   │   └── unemployment_wb.csv   Unemployment rate by country (World Bank)
│   └── econ206/
│
├── scripts/                       Python scripts that generate charts
│   ├── econ10/
│   │   ├── collect_data_wb.py
│   │   │     Downloads inflation + unemployment from World Bank API.
│   │   │     Output → data/econ10/inflation_wb.csv
│   │   │              data/econ10/unemployment_wb.csv
│   │   │
│   │   └── build_charts_inflation_unemployment.py
│   │         Reads CSVs, builds 3 interactive Plotly charts.
│   │         Output → docs/econ10/chart_inflation.html
│   │                  docs/econ10/chart_unemployment.html
│   │                  docs/econ10/chart_phillips.html
│   │
│   └── econ206/                   (scripts added as topics are built)
│
├── docs/                          GitHub Pages root (served as website)
│   ├── index.html                 Landing page — links to all courses
│   ├── econ10/
│   │   ├── index.html             ECON 10 chart listing page
│   │   ├── chart_inflation.html   Interactive line chart — inflation rate
│   │   ├── chart_unemployment.html Interactive line chart — unemployment rate
│   │   └── chart_phillips.html   Interactive scatter — Phillips curve
│   └── econ206/
│       └── index.html             ECON 206 chart listing page
│
├── requirements.txt               Python dependencies
├── .gitignore
└── README.md
```

---

## File Naming Conventions

Scripts follow a two-part naming pattern:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `collect_data_<source>.py` | Download raw data from an API or external source | `collect_data_wb.py` |
| `build_chart_<topic>.py` | Read data, build HTML chart(s) | `build_charts_inflation_unemployment.py` |

Output HTML files follow:

| Pattern | Example |
|---------|---------|
| `chart_<topic>.html` | `chart_inflation.html`, `chart_phillips.html` |

Data files follow:

| Pattern | Example |
|---------|---------|
| `<topic>_<source>.csv` | `inflation_wb.csv` (`wb` = World Bank) |

---

## Workflow: Adding a New Visualization

1. **Collect data** — add a `collect_data_<source>.py` script under `scripts/<course>/`.
   Save output CSV to `data/<course>/`.

2. **Build chart** — add a `build_chart_<topic>.py` script that reads the CSV
   and writes a self-contained HTML file to `docs/<course>/`.

3. **Register the chart** — add a card to `docs/<course>/index.html`
   and (if a new course) link it from `docs/index.html`.

4. **Commit and push** — the chart is live at
   `https://kensukesuzuki04.github.io/econ_data/<course>/chart_<topic>.html`.

---

## Running the Scripts

```bash
# Install dependencies
pip install -r requirements.txt

# ECON 10 — Inflation & Unemployment
python scripts/econ10/collect_data_wb.py                       # download data
python scripts/econ10/build_charts_inflation_unemployment.py   # build charts
```

---

## Data Sources

| Source | Access | Used for |
|--------|--------|---------|
| [World Bank Open Data](https://data.worldbank.org/) | Free API, no key | Inflation (CPI), Unemployment |

Indicators used:
- `FP.CPI.TOTL.ZG` — Inflation, consumer prices (annual %)
- `SL.UEM.TOTL.ZS` — Unemployment, total (% of labor force, ILO estimate)

---

## Tech Stack

| Tool | Role |
|------|------|
| Python 3 | Data collection and chart generation |
| [pandas](https://pandas.pydata.org/) | Data processing |
| [Plotly](https://plotly.com/python/) | Interactive charts |
| [requests](https://requests.readthedocs.io/) | API data fetching |
| GitHub Pages (`/docs` folder) | Hosting |

Charts embed Plotly via CDN — no server required, files open offline.

---

## GitHub Pages Setup

Pages are served from the `docs/` folder on the `main` branch.
To enable: **Settings → Pages → Branch: main, Folder: /docs**.

---

*&copy; 2026, Kensuke Suzuki, Clark University. All Rights Reserved.*
