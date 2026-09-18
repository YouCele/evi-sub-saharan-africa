"""
Script 1 - fetch every input this project needs from the World Bank API.

This is the one script in the whole project that needs internet access.
Everything after it works from the cached CSVs in data/raw/.

Run this on a machine with a normal internet connection - the World Bank
API is public and needs no key or registration.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import config, data_loading as dl
from src.utils import banner, note, write_processed


def main() -> None:
    banner("STEP 1 - FETCHING DATA FROM THE WORLD BANK API")

    ssf = dl.ssf_country_list()
    note(f"{len(ssf)} Sub-Saharan African economies, per the World Bank's own "
         "region classification (region_id == 'SSF')")
    print(ssf[["iso3", "name", "income_level"]].to_string(index=False))

    edge_cases = ["DJI", "SDN", "SSD", "SOM"]
    present = [c for c in edge_cases if c in ssf["iso3"].values]
    absent = [c for c in edge_cases if c not in ssf["iso3"].values]
    if absent:
        note(f"note: {absent} are NOT classified as SSF by the World Bank "
             "right now (likely grouped under Middle East & North Africa "
             "instead) - excluded from this analysis as a result, since the "
             "scope is defined by the live API response, not a fixed guess")
    if present:
        note(f"confirmed as SSF: {present}")

    iso3_codes = ssf["iso3"].tolist()
    indicators = dl.fetch_all_indicators(iso3_codes)

    for name, df in indicators.items():
        note(f"{name}: {df['iso3'].nunique()} countries, "
             f"{df['year'].min()}-{df['year'].max()}, "
             f"{100*df['value'].isna().mean():.1f}% missing")

    write_processed(ssf, "ssf_countries.csv")
    for name, df in indicators.items():
        write_processed(df, f"long_{name}.csv")

    banner("SCRIPT 1 FINISHED - raw data cached under data/raw/, "
          "long-format series under data/processed/")


if __name__ == "__main__":
    main()
