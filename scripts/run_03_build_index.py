"""
Script 3 - normalise the components, build the composite EVI, and build the
PCA-weighted alternative for comparison.

Input  : data/processed/country_wide_final.csv
Output : outputs/evi_scores.csv, outputs/pca_scores.csv, figures/01_evi_ranking.png
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from src import benchmark as bm, config, eda
from src.index_construction import (build_exposure_components, build_econ_instability_components,
                                    composite_index, pca_weighted_index)
from src.utils import banner, note, read_processed, save_json, save_table, step


def main() -> None:
    banner("STEP 3 - BUILDING THE COMPOSITE INDEX")

    wide = read_processed("country_wide_final.csv")

    exposure = build_exposure_components(wide)
    shock = build_econ_instability_components(wide)
    save_table(exposure, "exposure_components.csv")
    save_table(shock, "econ_instability_components.csv")

    evi = composite_index(exposure, shock)
    evi = evi.merge(wide[["iso3", "country", "gni_per_capita_atlas"]], on="iso3", how="left")
    evi = bm.attach_ldc_status(evi)
    save_table(evi, "evi_scores.csv")

    partial = evi[evi["partial_index"]]
    if len(partial):
        note(f"{len(partial)} countries have a composite score built from only "
             "one sub-index (the other has zero available components): " +
             ", ".join(partial["country"]) + " - treat their EVI as an "
             "exposure-only or economic-instability-only score, not a true composite")

    step("most vulnerable, by the reconstructed EVI")
    print(evi.head(10)[["country", "iso3", "evi", "exposure_index", "econ_instability_index",
                        "is_ldc"]].round(3).to_string(index=False))
    step("least vulnerable")
    print(evi.tail(10)[["country", "iso3", "evi", "exposure_index", "econ_instability_index",
                        "is_ldc"]].round(3).to_string(index=False))

    eda.fig_ranking(evi)
    eda.fig_ldc_comparison(evi)
    eda.fig_income_scatter(evi)

    step("PCA-weighted alternative")
    pca = pca_weighted_index(exposure, shock)
    save_table(pca, "pca_scores.csv")
    explained = pca.attrs.get("explained_variance_ratio")
    if explained:
        note(f"first principal component explains {100*explained:.1f}% of the "
             "variance across the six normalised components")
    eda.fig_weighting_comparison(evi, pca)

    save_json(dict(
        n_countries_in_index=len(evi),
        n_countries_with_pca_score=len(pca),
        pca_explained_variance_ratio=explained,
    ), "index_construction_summary.json")

    banner("SCRIPT 3 FINISHED")


if __name__ == "__main__":
    main()
