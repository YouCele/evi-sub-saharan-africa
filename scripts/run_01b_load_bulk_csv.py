"""
Script 1b - load real World Bank data from manually downloaded bulk CSV
files, instead of calling the live API.

This is an alternative to scripts/run_01_fetch_data.py for exactly one
situation: an environment (like this one) that cannot make outbound API
calls itself. The person downloads the 10 CSV.zip files from
https://api.worldbank.org/v2/country/all/indicator/<CODE>?downloadformat=csv
for each indicator in config.INDICATORS, unzips them all into one folder,
and this script does the rest - including deriving the Sub-Saharan Africa
country list from the real Metadata_Country file rather than trusting a
hardcoded guess, exactly as run_01_fetch_data.py does from the live API.

Input  : data/raw/wb_bulk/*.csv (the unzipped bulk downloads)
Output : data/processed/ssf_countries.csv, data/processed/long_*.csv
         - the same files run_01_fetch_data.py would have produced, so
         every script after this one runs unmodified.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import glob

import pandas as pd

from src import config
from src.utils import banner, fail, note, step, write_processed

BULK_DIR = config.RAW_DIR / "wb_bulk"


def find_indicator_file(code: str) -> Path:
    matches = glob.glob(str(BULK_DIR / f"API_{code}_*.csv"))
    matches = [m for m in matches if "Metadata" not in m]
    if not matches:
        fail(f"no bulk CSV found for {code} under {BULK_DIR} - "
             f"expected a file named API_{code}_*.csv")
    return Path(matches[0])


def find_metadata_file() -> Path:
    matches = glob.glob(str(BULK_DIR / "Metadata_Country_API_*.csv"))
    if not matches:
        fail(f"no Metadata_Country_API_*.csv found under {BULK_DIR} - "
             "every World Bank bulk download includes one, any single one is enough")
    return Path(matches[0])


def load_ssf_countries() -> pd.DataFrame:
    """
    The Sub-Saharan Africa country list, derived from the real metadata
    file that ships inside every World Bank bulk download - not a
    hardcoded guess. Any one of the ten metadata files carries the same
    country classification, so the first one found is used.
    """
    path = find_metadata_file()
    meta = pd.read_csv(path, encoding="utf-8-sig")
    meta.columns = [c.strip() for c in meta.columns]
    ssf = meta[meta["Region"] == "Sub-Saharan Africa"].copy()
    out = pd.DataFrame(dict(
        iso3=ssf["Country Code"],
        name=ssf["TableName"],
        income_level=ssf["IncomeGroup"],
    )).reset_index(drop=True)
    note(f"{len(out)} Sub-Saharan African economies found in {path.name}")
    return out


def load_indicator_long(code: str, iso3_codes: list[str]) -> pd.DataFrame:
    """Melt one wide bulk CSV (one column per year) into long format,
    filtered to the Sub-Saharan Africa country list."""
    path = find_indicator_file(code)
    wide = pd.read_csv(path, skiprows=4, encoding="utf-8-sig")
    wide = wide[wide["Country Code"].isin(iso3_codes)]

    year_cols = [c for c in wide.columns if c.strip().isdigit()]
    long_df = wide.melt(id_vars=["Country Name", "Country Code"],
                        value_vars=year_cols, var_name="year", value_name="value")
    long_df = long_df.rename(columns={"Country Code": "iso3", "Country Name": "country"})
    long_df["year"] = long_df["year"].astype(int)
    long_df = long_df[(long_df["year"] >= config.START_YEAR) &
                      (long_df["year"] <= config.END_YEAR)]
    long_df = long_df.dropna(subset=["value"]).sort_values(["iso3", "year"]).reset_index(drop=True)
    return long_df[["iso3", "country", "year", "value"]]


def main() -> None:
    banner("STEP 1b - LOADING REAL DATA FROM DOWNLOADED WORLD BANK CSVs")

    if not BULK_DIR.exists() or not list(BULK_DIR.glob("*.csv")):
        fail(f"{BULK_DIR} has no CSV files - unzip the 10 downloaded "
             f"World Bank ZIPs into that folder first")

    ssf = load_ssf_countries()
    print(ssf.to_string(index=False))
    write_processed(ssf, "ssf_countries.csv")

    iso3_codes = ssf["iso3"].tolist()

    for meta in config.INDICATORS:
        step(f"{meta['code']} -> {meta['name']}")
        long_df = load_indicator_long(meta["code"], iso3_codes)
        n_countries = long_df["iso3"].nunique()
        n_missing_countries = len(iso3_codes) - n_countries
        note(f"{len(long_df)} country-year rows, {n_countries} of {len(iso3_codes)} "
             f"countries have at least one non-missing value in "
             f"{config.START_YEAR}-{config.END_YEAR}")
        if n_missing_countries:
            missing = sorted(set(iso3_codes) - set(long_df["iso3"]))
            note(f"no data at all in this window for: {', '.join(missing)}")
        write_processed(long_df, f"long_{meta['name']}.csv")

    banner("SCRIPT 1b FINISHED - real data loaded, scripts 2 through 6 "
          "run exactly as they would after the live API fetch")


if __name__ == "__main__":
    main()
