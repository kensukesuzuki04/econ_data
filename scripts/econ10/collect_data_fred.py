#!/usr/bin/env python3
"""
collect_data_fred.py
────────────────────
Download US unemployment (UNRATE) and CPI (CPIAUCSL) from FRED using
the public direct-CSV endpoint (no API key required).

Converts monthly series to annual averages; computes year-over-year
CPI inflation.  Saves a single merged file used by the US Phillips chart.

Data sources (FRED / St. Louis Fed)
    UNRATE    Civilian Unemployment Rate, monthly SA, 1948-01 to present
    CPIAUCSL  CPI for All Urban Consumers: All Items, monthly NSA, 1947-01

Usage
    python scripts/econ10/collect_data_fred.py

Output
    data/econ10/phillips_fred_us.csv  (columns: year, unemployment, inflation)
"""

import requests
import pandas as pd
from io import StringIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / "data" / "econ10"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def fetch_fred_monthly(series_id: str) -> pd.DataFrame:
    """Download a FRED series as a monthly DataFrame with columns [date, value]."""
    url  = f"{FRED_CSV}?id={series_id}"
    print(f"  Fetching {series_id} from FRED ...", end=" ", flush=True)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text), parse_dates=["observation_date"])
    df = df.rename(columns={"observation_date": "date", series_id: "value"})
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    print(f"{len(df)} monthly obs ({df['date'].dt.year.min()}-{df['date'].dt.year.max()})")
    return df


def to_annual_mean(df: pd.DataFrame) -> pd.Series:
    """Average monthly values to annual.  Returns Series indexed by year."""
    df = df.copy()
    df["year"] = df["date"].dt.year
    return df.groupby("year")["value"].mean()


def annual_yoy_pct(annual_cpi: pd.Series) -> pd.Series:
    """Year-over-year % change from annual-average CPI."""
    return annual_cpi.pct_change() * 100


def main():
    print("=" * 55)
    print("FRED data collection - US Phillips curve")
    print("=" * 55)
    print()

    # --- Unemployment ---
    unemp_monthly = fetch_fred_monthly("UNRATE")
    unemp_annual  = to_annual_mean(unemp_monthly).rename("unemployment")

    # --- CPI → annual % inflation ---
    cpi_monthly = fetch_fred_monthly("CPIAUCSL")
    cpi_annual  = to_annual_mean(cpi_monthly)
    inf_annual  = annual_yoy_pct(cpi_annual).rename("inflation")

    # --- Merge ---
    df = pd.merge(
        unemp_annual.reset_index(),
        inf_annual.reset_index(),
        on="year",
    ).dropna()
    df["unemployment"] = df["unemployment"].round(4)
    df["inflation"]    = df["inflation"].round(4)
    df = df.sort_values("year").reset_index(drop=True)

    out = DATA_DIR / "phillips_fred_us.csv"
    df.to_csv(out, index=False)
    print(f"\n  Saved -> {out.relative_to(REPO_ROOT)}")
    print(f"  {len(df)} obs, {int(df['year'].min())}-{int(df['year'].max())}")
    print("\nDone.")


if __name__ == "__main__":
    main()
