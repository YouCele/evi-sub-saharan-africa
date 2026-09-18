"""
Script 2 - turn the long-format time series into one row per country,
build the derived indicators, and decide what to do about missing data.

Input  : data/processed/long_*.csv, data/processed/ssf_countries.csv
Output : data/processed/country_wide.csv, outputs/missingness_*.csv,
         outputs/exclusion_decisions.csv, figures/04_missingness_by_country.png
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import config, eda, indicators as ind, missingness as ms
from src.utils import banner, note, read_processed, save_table, step, write_processed


def main() -> None:
    banner("STEP 2 - BUILDING THE CROSS-SECTIONAL TABLE")

    ssf = read_processed("ssf_countries.csv")[["iso3", "name"]].rename(columns={"name": "country"})
    ssf["landlocked"] = ssf["iso3"].isin(config.LANDLOCKED_ISO3)

    wide = ssf.copy()

    step("reference-year values for the exposure and context indicators")
    for meta in config.INDICATORS:
        if meta["role"] not in ("exposure", "context"):
            continue
        long_df = read_processed(f"long_{meta['name']}.csv")
        ref_val = ind.attach_reference_year(long_df, "value").rename(meta["name"])
        wide = wide.merge(ref_val.reset_index().rename(columns={"index": "iso3"}),
                          on="iso3", how="left")

    step("the four export-share inputs, for the concentration index")
    for name in config.EXPORT_SHARE_COLUMNS:
        long_df = read_processed(f"long_{name}.csv")
        ref_val = ind.attach_reference_year(long_df, "value").rename(name)
        wide = wide.merge(ref_val.reset_index().rename(columns={"index": "iso3"}),
                          on="iso3", how="left")
    wide["export_concentration"] = ind.export_concentration(wide)

    step("instability indices from the full time series")
    for name in ["exports_constant_usd", "agri_value_constant_usd"]:
        long_df = read_processed(f"long_{name}.csv").rename(columns={"value": name})
        instab = ind.instability_index(long_df, name).reset_index().rename(
            columns={"index": "iso3"})
        n_years = ind.years_of_coverage(long_df, name).reset_index().rename(
            columns={"index": "iso3"})
        wide = wide.merge(instab, on="iso3", how="left")
        wide = wide.merge(n_years, on="iso3", how="left")

    write_processed(wide, "country_wide.csv")
    step("cross-sectional table, first few rows")
    print(wide.head(8).to_string(index=False))

    banner("MISSINGNESS")
    required_cols = ["population", "agri_share_gdp", "export_concentration",
                     "exports_constant_usd_instability", "agri_value_constant_usd_instability"]

    by_indicator = ms.missingness_by_indicator(wide, required_cols)
    save_table(by_indicator, "missingness_by_indicator.csv")
    print(by_indicator.to_string(index=False))

    by_country = ms.missingness_by_country(wide, required_cols)
    save_table(by_country, "missingness_by_country.csv")
    step("countries with the most missing inputs")
    print(by_country.head(10).to_string(index=False))
    eda.fig_missingness(by_country)

    kept, decisions = ms.apply_exclusion_rule(by_country)
    save_table(decisions, "exclusion_decisions.csv")

    wide_final = wide[wide["iso3"].isin(kept)].reset_index(drop=True)
    write_processed(wide_final, "country_wide_final.csv")
    note(f"{len(wide_final)} of {len(wide)} countries retained for index construction")

    banner("SCRIPT 2 FINISHED")


if __name__ == "__main__":
    main()
