#!/usr/bin/env python3
"""
export_capital_wage_pdf.py
---------------------------
Export a print-ready PDF of real capital per worker vs. real wage per worker (US)
using matplotlib.

Usage:
    python scripts/econ206/export_capital_wage_pdf.py
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parents[2]
DATA_DIR   = REPO_ROOT / "data"  / "econ206"
EXPORT_DIR = REPO_ROOT / "exports" / "econ206"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# ── Parameters ────────────────────────────────────────────────────────────────
YEAR_MIN     = 1960
YEAR_MAX     = 1980
LBL_INTERVAL = 5          # label every N years (also labels first & last)
SHOW_TREND   = False       # fitted polynomial line

# Figure sized for 1/4-page height on US letter (text area ≈ 6.5 × 9 in)
FIG_W, FIG_H = 6.5, 2.25

COLOR        = "black"     # black and white
OUT_FILE     = EXPORT_DIR / f"capital_wage_us_{YEAR_MIN}_{YEAR_MAX}.pdf"

# ── Load data ─────────────────────────────────────────────────────────────────
pwt_path = DATA_DIR / "pwt110.xlsx"
df = pd.read_excel(pwt_path, sheet_name="Data")
us = (df[df["countrycode"] == "USA"]
        [["year", "rnna", "emp", "labsh", "rgdpna"]]
        .dropna()
        .sort_values("year"))

us["k_per_worker"] = us["rnna"]  / us["emp"]
us["real_wage"]    = us["labsh"] * us["rgdpna"] / us["emp"]
us = us.dropna(subset=["k_per_worker", "real_wage"])
us = us[(us["year"] >= YEAR_MIN) & (us["year"] <= YEAR_MAX)]

xs    = us["k_per_worker"].values
ys    = us["real_wage"].values
years = us["year"].astype(int).values

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
fig.subplots_adjust(left=0.11, right=0.97, top=0.84, bottom=0.22)

ax.scatter(xs, ys, color=COLOR, s=18, zorder=3, linewidths=0,
           edgecolors="none")

# Year labels at every LBL_INTERVAL (always label first and last)
label_years = set(range(YEAR_MIN, YEAR_MAX + 1, LBL_INTERVAL))
label_years |= {years[0], years[-1]}

for x, y, yr in zip(xs, ys, years):
    if yr in label_years:
        ax.annotate(str(yr), (x, y),
                    textcoords="offset points", xytext=(0, 5),
                    ha="center", va="bottom",
                    fontsize=8, color=COLOR)

# Optional fitted line
if SHOW_TREND and len(xs) >= 5:
    coeffs  = np.polyfit(xs, ys, 2)
    x_range = np.linspace(xs.min(), xs.max(), 300)
    ax.plot(x_range, np.polyval(coeffs, x_range),
            color="black", linewidth=1.2, linestyle="--",
            label="Fitted line (2nd-order polynomial)", zorder=2)
    ax.legend(fontsize=6)

# Axes
def dollar_k(val, _):
    if val >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val/1_000:.0f}k"
    return f"${val:.0f}"

ax.xaxis.set_major_formatter(mticker.FuncFormatter(dollar_k))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(dollar_k))
ax.set_xlabel("Real Capital per Worker (2021 USD)", fontsize=7.5)
ax.set_ylabel("Real Wage per Worker (2021 USD)", fontsize=7.5)
ax.tick_params(labelsize=7, length=3, pad=2)
ax.grid(True, color="#dddddd", linewidth=0.6, zorder=0)
ax.set_axisbelow(True)
for spine in ax.spines.values():
    spine.set_color("#888888")
    spine.set_linewidth(0.6)

# Title & source note
fig.suptitle(
    f"Real Capital Stock vs. Real Wage \u2014 United States, {YEAR_MIN}\u2013{YEAR_MAX}",
    fontsize=8, fontweight="bold", x=0.0, ha="left",
    y=0.97, va="top"
)
fig.text(
    0.0, 0.0,
    "Source: Penn World Tables 11.0 (Feenstra, Inklaar & Timmer, 2015).  "
    "x = rnna / emp.  y = labsh \u00d7 rgdpna / emp.  All values in 2021 USD.",
    fontsize=6, color="#444", ha="left", va="bottom"
)

plt.savefig(OUT_FILE, format="pdf", bbox_inches="tight")
print(f"Saved -> {OUT_FILE}")
plt.close()
