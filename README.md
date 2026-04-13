# Economics Data Visualizations

**Kensuke Suzuki** | Department of Economics | Clark University

Interactive visualizations to accompany undergraduate economics courses. Charts are built with Python and Plotly and published as self-contained HTML files — no installation required.

---

## Courses

| Course | Title | Level |
|--------|-------|-------|
| [ECON 10](docs/econ10/) | Introductory Economics | Undergraduate |
| [ECON 206](docs/econ206/) | Intermediate Macroeconomics | Undergraduate |

---

## Live Site

Visualizations are hosted at: **https://kensukesuzuki04.github.io/econ_data/**

---

## Repository Structure

```
data/          Raw data files, organized by course
scripts/       Python scripts that generate each chart
docs/          Published HTML charts (served via GitHub Pages)
```

---

## Tools

- [Python](https://www.python.org/) with [Plotly](https://plotly.com/python/) for interactive charts
- [pandas](https://pandas.pydata.org/) for data processing
- Charts export as standalone `.html` files — open in any browser, no dependencies

---

## Running the Scripts

```bash
pip install -r requirements.txt
python scripts/econ10/supply_demand.py   # example
```

Each script reads from `data/` and writes a chart to `docs/`.

---

*© 2026, Kensuke Suzuki, Clark University. All Rights Reserved.*
