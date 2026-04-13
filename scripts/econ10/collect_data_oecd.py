#!/usr/bin/env python3
"""
collect_data_oecd.py
────────────────────
Download OECD harmonized unemployment rates for OECD member countries.

Data source (unemployment)
    FRED (St. Louis Fed), series LRHUTTTT{ISO2}M156S per country
    These are OECD-standardized harmonized unemployment rates, monthly SA.
    No API key required — uses FRED public direct-CSV endpoint.
    Coverage: 32 of 38 OECD members (6 not published on FRED: COL, CRI,
    LVA, LTU, NZL, CHE). Earliest data: 1955 for USA, Canada, Japan.

Data source (inflation)
    Reuses data/econ10/inflation_wb.csv already downloaded by collect_data_wb.py.

Output
    data/econ10/unemployment_oecd.csv   (iso3, country, year, unemployment)
    data/econ10/phillips_oecd.csv       (iso3, country, year, unemployment, inflation)

Prerequisites
    python scripts/econ10/collect_data_wb.py  -- must run first for inflation

Usage
    python scripts/econ10/collect_data_oecd.py
"""

import requests
import pandas as pd
from io import StringIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR  = REPO_ROOT / "data" / "econ10"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# OECD members available on FRED via LRHUTTTT{ISO2}M156S
# iso3 -> (iso2_upper, display_name, wb_iso2)
# wb_iso2 is the 2-letter code used in WB inflation CSV for merging
OECD_FRED = {
    "AUS": ("AU", "Australia",      "AU"),
    "AUT": ("AT", "Austria",        "AT"),
    "BEL": ("BE", "Belgium",        "BE"),
    "CAN": ("CA", "Canada",         "CA"),
    "CHL": ("CL", "Chile",          "CL"),
    "CZE": ("CZ", "Czechia",        "CZ"),
    "DNK": ("DK", "Denmark",        "DK"),
    "EST": ("EE", "Estonia",        "EE"),
    "FIN": ("FI", "Finland",        "FI"),
    "FRA": ("FR", "France",         "FR"),
    "DEU": ("DE", "Germany",        "DE"),
    "GRC": ("GR", "Greece",         "GR"),
    "HUN": ("HU", "Hungary",        "HU"),
    "ISL": ("IS", "Iceland",        "IS"),
    "IRL": ("IE", "Ireland",        "IE"),
    "ISR": ("IL", "Israel",         "IL"),
    "ITA": ("IT", "Italy",          "IT"),
    "JPN": ("JP", "Japan",          "JP"),
    "KOR": ("KR", "Korea, Rep.",    "KR"),
    "LUX": ("LU", "Luxembourg",     "LU"),
    "MEX": ("MX", "Mexico",         "MX"),
    "NLD": ("NL", "Netherlands",    "NL"),
    "NOR": ("NO", "Norway",         "NO"),
    "POL": ("PL", "Poland",         "PL"),
    "PRT": ("PT", "Portugal",       "PT"),
    "SVK": ("SK", "Slovak Republic","SK"),
    "SVN": ("SI", "Slovenia",       "SI"),
    "ESP": ("ES", "Spain",          "ES"),
    "SWE": ("SE", "Sweden",         "SE"),
    "TUR": ("TR", "Turkiye",        "TR"),
    "GBR": ("GB", "United Kingdom", "GB"),
    "USA": ("US", "United States",  "US"),
}


def fetch_oecd_unemployment_fred() -> pd.DataFrame:
    """
    Download monthly OECD harmonized unemployment for each available country
    from FRED, convert to annual averages.
    """
    rows = []
    total = len(OECD_FRED)
    for i, (iso3, (iso2, name, _)) in enumerate(OECD_FRED.items(), 1):
        series_id = f"LRHUTTTT{iso2}M156S"
        url = f"{FRED_CSV}?id={series_id}"
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            df = pd.read_csv(
                StringIO(resp.text), parse_dates=["observation_date"]
            )
            df = df.rename(columns={"observation_date": "date", series_id: "value"})
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna(subset=["value"])
            df["year"] = df["date"].dt.year
            annual = df.groupby("year")["value"].mean().round(4)
            for yr, val in annual.items():
                rows.append({
                    "iso3":         iso3,
                    "country":      name,
                    "year":         yr,
                    "unemployment": round(val, 4),
                })
            start = int(df["year"].min())
            end   = int(df["year"].max())
            print(f"  [{i:2d}/{total}] {name:<22} {start}-{end}")
        except Exception as e:
            print(f"  [{i:2d}/{total}] {name:<22} FAILED: {e}")

    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["iso3", "year"])
            .sort_values(["country", "year"])
            .reset_index(drop=True))
    return df


def merge_with_wb_inflation(unemp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join OECD unemployment with WB CPI inflation, matching on WB iso2 code.
    """
    inf_path = DATA_DIR / "inflation_wb.csv"
    if not inf_path.exists():
        raise FileNotFoundError(
            f"{inf_path} not found. Run collect_data_wb.py first."
        )
    inf_df = pd.read_csv(inf_path)[["iso2", "year", "value"]].rename(
        columns={"value": "inflation"}
    )

    # Map iso3 -> wb_iso2 for the join
    iso3_to_wb_iso2 = {iso3: vals[2] for iso3, vals in OECD_FRED.items()}
    unemp_df = unemp_df.copy()
    unemp_df["wb_iso2"] = unemp_df["iso3"].map(iso3_to_wb_iso2)

    merged = pd.merge(
        unemp_df,
        inf_df,
        left_on=["wb_iso2", "year"],
        right_on=["iso2", "year"],
    ).drop(columns=["wb_iso2", "iso2"])

    merged = (merged
              .dropna(subset=["unemployment", "inflation"])
              .sort_values(["country", "year"])
              .reset_index(drop=True))
    return merged


def main():
    print("=" * 55)
    print("OECD data collection - OECD Phillips curve")
    print(f"Source: FRED OECD harmonized unemployment series")
    print(f"        ({len(OECD_FRED)} of 38 OECD members available)")
    print("=" * 55)
    print()

    unemp_df = fetch_oecd_unemployment_fred()
    out_u = DATA_DIR / "unemployment_oecd.csv"
    unemp_df.to_csv(out_u, index=False)
    print(f"\n  Saved -> {out_u.relative_to(REPO_ROOT)}")
    print(f"  {len(unemp_df)} obs, {unemp_df['country'].nunique()} countries, "
          f"{int(unemp_df['year'].min())}-{int(unemp_df['year'].max())}")

    print()
    phillips_df = merge_with_wb_inflation(unemp_df)
    out_p = DATA_DIR / "phillips_oecd.csv"
    phillips_df.to_csv(out_p, index=False)
    print(f"  Saved -> {out_p.relative_to(REPO_ROOT)}")
    print(f"  {len(phillips_df)} obs, {phillips_df['country'].nunique()} countries, "
          f"{int(phillips_df['year'].min())}-{int(phillips_df['year'].max())}")

    print("\nDone.")


if __name__ == "__main__":
    main()
