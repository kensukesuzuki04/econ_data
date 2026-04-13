#!/usr/bin/env python3
"""
collect_data_historical_us.py
─────────────────────────────
Assembles a long-run US Phillips curve dataset combining:

  Pre-1948  (annual estimates)
    Unemployment : Lebergott (1964) Table A-3, annual.
                   Alternative: Romer (1986) is generally lower —
                   see note below.
    CPI          : Robert Shiller, Yale University.
                   http://www.econ.yale.edu/~shiller/data/ie_data.xls
                   Monthly values averaged to annual; YoY % change computed.

  Post-1947  (official, from FRED)
    Reuses data/econ10/phillips_fred_us.csv produced by collect_data_fred.py.

Output
    data/econ10/phillips_us_historical.csv
    columns: year, unemployment, inflation, era
        era = "estimate"  for pre-1948 (Lebergott + Shiller)
            = "official"  for 1948+ (BLS / FRED)

Notes
  ─ Lebergott vs. Romer: Lebergott (1964) counts workers on government
    emergency relief programs as unemployed; Romer (1986) counts them as
    employed, producing lower Depression-era figures (~20% vs ~25% peak).
    Both series are widely used; Lebergott remains the most reproduced in
    textbooks and is used here.
  ─ CPI series: Shiller's monthly CPI series is derived from BLS historical
    data and Warren-Pearson price indices for the pre-1913 period.  Annual
    averages are used here; YoY inflation = (CPI_t / CPI_{t-1} - 1) * 100.

Prerequisites
    pip install xlrd
    python scripts/econ10/collect_data_fred.py

Usage
    python scripts/econ10/collect_data_historical_us.py
"""

import requests
import pandas as pd
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / "data" / "econ10"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SHILLER_URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"

# ── Lebergott (1964) annual unemployment rates, percent ──────────────────────
# Source: Lebergott, S. (1964). Manpower in Economic Growth. McGraw-Hill.
#         Table A-3. Reproduced in Historical Statistics of the United States.
# Coverage: 1890-1947 (post-1947 replaced by BLS / FRED UNRATE).
LEBERGOTT = {
    1890: 4.0,  1891: 5.4,  1892: 3.0,  1893: 11.7, 1894: 18.4,
    1895: 13.7, 1896: 14.5, 1897: 12.4, 1898: 12.4, 1899: 6.5,
    1900: 5.0,  1901: 4.0,  1902: 3.7,  1903: 3.9,  1904: 5.4,
    1905: 4.3,  1906: 1.7,  1907: 2.8,  1908: 8.0,  1909: 5.1,
    1910: 5.9,  1911: 6.7,  1912: 4.6,  1913: 4.3,  1914: 7.9,
    1915: 8.5,  1916: 5.1,  1917: 4.6,  1918: 1.4,  1919: 1.4,
    1920: 5.2,  1921: 11.7, 1922: 6.7,  1923: 2.4,  1924: 5.0,
    1925: 3.2,  1926: 1.8,  1927: 3.3,  1928: 4.2,  1929: 3.2,
    1930: 8.7,  1931: 15.9, 1932: 23.6, 1933: 24.9, 1934: 21.7,
    1935: 20.1, 1936: 16.9, 1937: 14.3, 1938: 19.0, 1939: 17.2,
    1940: 14.6, 1941: 9.9,  1942: 4.7,  1943: 1.9,  1944: 1.2,
    1945: 1.9,  1946: 3.9,  1947: 3.6,
}


def fetch_shiller_cpi_annual() -> pd.Series:
    """
    Download Shiller's ie_data.xls and return annual average CPI indexed by year.
    """
    print(f"  Fetching Shiller CPI from {SHILLER_URL} ...", end=" ", flush=True)
    resp = requests.get(SHILLER_URL, timeout=30)
    resp.raise_for_status()
    df = pd.read_excel(
        BytesIO(resp.content),
        sheet_name="Data",
        header=7,
        engine="xlrd",
        usecols=["Date", "CPI"],
    )
    df = df.dropna(subset=["Date", "CPI"])
    df = df[pd.to_numeric(df["Date"], errors="coerce").notna()].copy()
    df["Date"] = pd.to_numeric(df["Date"])
    df["year"] = df["Date"].astype(int)
    df["CPI"]  = pd.to_numeric(df["CPI"], errors="coerce")
    annual_cpi = df.groupby("year")["CPI"].mean()
    print(f"ok ({int(annual_cpi.index.min())}-{int(annual_cpi.index.max())})")
    return annual_cpi


def main():
    print("=" * 55)
    print("Historical US data collection")
    print("  Unemployment : Lebergott (1964), 1890-1947")
    print("  CPI          : Shiller / Yale, 1871-present")
    print("  Post-1947    : FRED UNRATE + CPIAUCSL")
    print("=" * 55)
    print()

    # ── Shiller CPI → annual inflation ───────────────────────────────────────
    annual_cpi = fetch_shiller_cpi_annual()
    inf_shiller = (annual_cpi.pct_change() * 100).rename("inflation").round(4)

    # ── Build pre-1948 panel ─────────────────────────────────────────────────
    unemp_hist = pd.Series(LEBERGOTT, name="unemployment")
    pre = pd.DataFrame({
        "year":         unemp_hist.index,
        "unemployment": unemp_hist.values,
        "inflation":    inf_shiller.reindex(unemp_hist.index).values,
        "era":          "estimate",
    }).dropna()
    print(f"\n  Pre-1948 panel : {len(pre)} obs  "
          f"({int(pre['year'].min())}-{int(pre['year'].max())})")

    # ── Load post-1947 FRED panel ─────────────────────────────────────────────
    fred_path = DATA_DIR / "phillips_fred_us.csv"
    if not fred_path.exists():
        raise FileNotFoundError(
            f"{fred_path} not found. Run collect_data_fred.py first."
        )
    post = pd.read_csv(fred_path)
    post["era"] = "official"
    print(f"  Post-1947 panel: {len(post)} obs  "
          f"({int(post['year'].min())}-{int(post['year'].max())})")

    # ── Combine, deduplicate (prefer official for overlap years) ─────────────
    combined = (
        pd.concat([pre, post], ignore_index=True)
        .sort_values(["year", "era"])          # "estimate" < "official" → drop estimate when both exist
        .drop_duplicates(subset=["year"], keep="last")
        .sort_values("year")
        .reset_index(drop=True)
    )
    combined = combined.dropna(subset=["unemployment", "inflation"])

    out = DATA_DIR / "phillips_us_historical.csv"
    combined.to_csv(out, index=False)
    print(f"\n  Saved -> {out.relative_to(REPO_ROOT)}")
    print(f"  {len(combined)} obs, {int(combined['year'].min())}-"
          f"{int(combined['year'].max())}")
    print(f"  {(combined['era']=='estimate').sum()} estimated, "
          f"{(combined['era']=='official').sum()} official")
    print("\nDone.")


if __name__ == "__main__":
    main()
