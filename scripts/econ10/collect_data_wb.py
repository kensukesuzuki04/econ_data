#!/usr/bin/env python3
"""
collect_data_wb.py
──────────────────
Download inflation and unemployment data for ALL World Bank countries
and save as CSV files to data/econ10/.

Data source : World Bank Open Data  https://data.worldbank.org/
API docs    : https://datahelpdesk.worldbank.org/knowledgebase/topics/125589
No API key required.

Indicators
    FP.CPI.TOTL.ZG  Inflation, consumer prices (annual %)
    SL.UEM.TOTL.ZS  Unemployment, total (% of total labor force, ILO estimate)

Coverage
    All World Bank countries (aggregates excluded).
    Earliest available year through latest available year.

Usage
    python scripts/econ10/collect_data_wb.py

Output
    data/econ10/inflation_wb.csv
    data/econ10/unemployment_wb.csv
"""

import requests
import pandas as pd
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / "data" / "econ10"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Time range ────────────────────────────────────────────────────────────────
# WB inflation data goes back to ~1960; unemployment ILO estimates from ~1991.
# Set wide range and let the API return whatever is available.
START_YEAR = 1960
END_YEAR   = 2024

# ── World Bank API ────────────────────────────────────────────────────────────
WB_BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    "FP.CPI.TOTL.ZG": ("inflation_wb.csv",    "Inflation, consumer prices (annual %)"),
    "SL.UEM.TOTL.ZS": ("unemployment_wb.csv", "Unemployment, total (% of labor force, ILO)"),
}


def fetch_country_list() -> set:
    """
    Return the set of ISO2 country codes for actual countries
    (World Bank aggregates and regional groups excluded).
    """
    url    = f"{WB_BASE}/country"
    params = {"format": "json", "per_page": 500}
    print("  Fetching WB country list ...", end=" ", flush=True)
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    entries = payload[1] if len(payload) > 1 else []
    # Aggregates have region.value == "Aggregates"
    actual = {
        c["id"]
        for c in entries
        if c.get("region", {}).get("value") != "Aggregates"
    }
    print(f"{len(actual)} countries")
    return actual


def fetch_indicator(indicator: str, label: str,
                    country_codes: set) -> pd.DataFrame:
    """
    Fetch annual observations for all countries from the World Bank API
    by batching country codes (50 per request) and paginating each batch.
    Returns DataFrame with columns: country, iso2, year, value.
    """
    codes = sorted(country_codes)
    batch_size = 50
    rows = []

    print(f"  Fetching {label} ({len(codes)} countries, batched) ...", flush=True)

    for i in range(0, len(codes), batch_size):
        batch = codes[i : i + batch_size]
        iso_str = ";".join(batch)
        url     = f"{WB_BASE}/country/{iso_str}/indicator/{indicator}"
        page    = 1
        while True:
            params = {
                "format":   "json",
                "per_page": 1000,
                "date":     f"{START_YEAR}:{END_YEAR}",
                "page":     page,
            }
            try:
                resp = requests.get(url, params=params, timeout=60)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"\n  WARNING: batch {i//batch_size+1} page {page} failed: {e}")
                break

            payload = resp.json()
            if len(payload) < 2 or payload[1] is None:
                break

            meta  = payload[0]
            items = payload[1]
            for item in items:
                if item["value"] is None:
                    continue
                rows.append({
                    "country": item["country"]["value"],
                    "iso2":    item["country"]["id"],
                    "year":    int(item["date"]),
                    "value":   round(float(item["value"]), 4),
                })

            if page >= meta.get("pages", 1):
                break
            page += 1

        batch_num = i // batch_size + 1
        total_batches = (len(codes) - 1) // batch_size + 1
        print(f"    batch {batch_num}/{total_batches} done", flush=True)

    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["country", "year"])
            .sort_values(["country", "year"])
            .reset_index(drop=True))
    print(f"  Total: {len(df)} obs, {df['country'].nunique()} countries")
    return df


def main():
    print("=" * 55)
    print("World Bank data collection - ECON 10")
    print(f"Coverage: {START_YEAR}-{END_YEAR}, all WB countries")
    print("=" * 55)

    country_codes = fetch_country_list()

    for indicator, (filename, label) in INDICATORS.items():
        print()
        df  = fetch_indicator(indicator, label, country_codes)
        out = DATA_DIR / filename
        df.to_csv(out, index=False)
        years = f"{int(df['year'].min())}-{int(df['year'].max())}"
        print(f"  Saved → {out.relative_to(REPO_ROOT)}  ({years})")

    print("\nDone.")


if __name__ == "__main__":
    main()
