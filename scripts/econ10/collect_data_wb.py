#!/usr/bin/env python3
"""
collect_data_wb.py
──────────────────
Download inflation and unemployment data from the World Bank Open Data API
and save as CSV files to data/econ10/.

Data source : World Bank Open Data  https://data.worldbank.org/
API docs    : https://datahelpdesk.worldbank.org/knowledgebase/topics/125589
No API key required.

Indicators
    FP.CPI.TOTL.ZG  Inflation, consumer prices (annual %)
    SL.UEM.TOTL.ZS  Unemployment, total (% of total labor force, ILO estimate)

Usage
    python scripts/econ10/collect_data_wb.py

Output
    data/econ10/inflation_wb.csv
    data/econ10/unemployment_wb.csv
"""

import sys
import requests
import pandas as pd
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / "data" / "econ10"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Country list ──────────────────────────────────────────────────────────────
# ISO 2-letter codes → display names
# Add or remove countries here to change what gets downloaded.
COUNTRIES = {
    "US": "United States",
    "DE": "Germany",
    "JP": "Japan",
    "CN": "China",
    "BR": "Brazil",
    "IN": "India",
    "GB": "United Kingdom",
    "MX": "Mexico",
    "KR": "South Korea",
    "TR": "Turkey",
    "AR": "Argentina",
    "ZA": "South Africa",
    "FR": "France",
    "CA": "Canada",
}

# ── Time range ────────────────────────────────────────────────────────────────
START_YEAR = 1990
END_YEAR   = 2023

# ── World Bank API ────────────────────────────────────────────────────────────
WB_BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    "FP.CPI.TOTL.ZG": ("inflation_wb.csv",    "Inflation Rate (%)"),
    "SL.UEM.TOTL.ZS": ("unemployment_wb.csv", "Unemployment Rate (%)"),
}


def fetch_indicator(indicator: str, label: str) -> pd.DataFrame:
    """
    Fetch annual observations for all countries in COUNTRIES from the World Bank API.
    Returns a DataFrame with columns: country, iso2, year, value.
    """
    iso_str = ";".join(COUNTRIES.keys())
    url     = f"{WB_BASE}/country/{iso_str}/indicator/{indicator}"
    params  = {
        "format":   "json",
        "per_page": 20000,
        "date":     f"{START_YEAR}:{END_YEAR}",
    }

    print(f"  Fetching {label} ({indicator}) ...", end=" ", flush=True)
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        sys.exit(f"\n  ERROR: {e}")

    payload = resp.json()
    if len(payload) < 2 or payload[1] is None:
        sys.exit(f"\n  ERROR: Empty response for {indicator}")

    # Build reverse map: WB country name → ISO2 code
    name_to_iso2 = {v: k for k, v in COUNTRIES.items()}

    rows = []
    for item in payload[1]:
        if item["value"] is None:
            continue
        wb_name = item["country"]["value"]
        # Try to match WB name to our COUNTRIES dict
        iso2 = name_to_iso2.get(wb_name)
        rows.append({
            "country": wb_name,
            "iso2":    iso2 or "",
            "year":    int(item["date"]),
            "value":   round(float(item["value"]), 4),
        })

    df = (pd.DataFrame(rows)
            .sort_values(["country", "year"])
            .reset_index(drop=True))
    print(f"{len(df)} obs, {df['country'].nunique()} countries")
    return df


def main():
    print("=" * 50)
    print("World Bank data collection — ECON 10")
    print("=" * 50)

    for indicator, (filename, label) in INDICATORS.items():
        df  = fetch_indicator(indicator, label)
        out = DATA_DIR / filename
        df.to_csv(out, index=False)
        print(f"  Saved → {out.relative_to(REPO_ROOT)}\n")

    print("Done.")


if __name__ == "__main__":
    main()
