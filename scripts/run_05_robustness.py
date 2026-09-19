"""
Script 5 - robustness checks on the index construction itself.

Input  : outputs/exposure_components.csv, outputs/econ_instability_components.csv,
         outputs/evi_scores.csv, outputs/pca_scores.csv,
         outputs/missingness_by_country.csv
Output : outputs/robustness_*.csv, figures/05_jackknife_sensitivity.png,
         figures/06_equal_weight_vs_pca.png
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import config, eda, robustness as rb
from src.utils import banner, note, save_json, save_table, step


def main() -> None:
    banner("STEP 5 - ROBUSTNESS CHECKS")

    exposure = pd.read_csv(config.OUTPUT_DIR / "exposure_components.csv")
    econ_instability = pd.read_csv(config.OUTPUT_DIR / "econ_instability_components.csv")
    evi = pd.read_csv(config.OUTPUT_DIR / "evi_scores.csv")
    pca = pd.read_csv(config.OUTPUT_DIR / "pca_scores.csv")
    missing = pd.read_csv(config.OUTPUT_DIR / "missingness_by_country.csv")

    step("1. equal-weight EVI against the PCA-weighted alternative")
    weight_cmp = rb.weighting_scheme_comparison(evi, pca)
    if "spearman_rho" in weight_cmp:
        note(f"rank correlation between the two schemes: "
             f"{weight_cmp['spearman_rho']:.3f} (p = {weight_cmp['p_value']:.4f})")
        save_table(weight_cmp["biggest_movers"], "robustness_biggest_rank_movers.csv")
        print(weight_cmp["biggest_movers"].round(1).to_string(index=False))
    else:
        note(weight_cmp.get("note", "comparison could not be run"))
    eda.fig_weighting_comparison(evi, pca)

    step("2. jackknife - does the ranking depend heavily on any one component")
    jack = rb.jackknife_components(exposure, econ_instability)
    save_table(jack, "robustness_jackknife.csv")
    print(jack.round(3).to_string(index=False))
    eda.fig_jackknife(jack)
    weakest = jack.iloc[0]
    note(f"removing '{weakest['component_removed']}' moves the ranking the most "
         f"(correlation with the full index: {weakest['spearman_rho_vs_full']:.3f}) "
         "- this is the component the composite score leans on hardest")

    step("3. missingness threshold sensitivity")
    thresh = rb.missingness_threshold_sensitivity(missing)
    save_table(thresh, "robustness_missingness_threshold.csv")
    print(thresh.to_string(index=False))
    note("this shows how many countries the index would cover under stricter "
         "or looser missing-data rules than the 40% cut-off actually used")

    banner("SCRIPT 5 FINISHED")


if __name__ == "__main__":
    main()
