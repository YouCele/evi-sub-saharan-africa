"""
Script 4 - does the reconstructed EVI actually track something real?

Compares against the current UN LDC classification (a real, external label
this project's construction did not see) and against income, to check the
index is not simply re-deriving GNI per capita under a different name.

Input  : outputs/evi_scores.csv
Output : outputs/benchmark_ldc_comparison.json, outputs/benchmark_misclassified.csv,
         outputs/benchmark_income_correlation.json
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import benchmark as bm
from src.utils import banner, note, read_processed, save_json, save_table, step

OUT_NAME = "evi_scores.csv"


def main() -> None:
    banner("STEP 4 - BENCHMARK VALIDATION AGAINST THE UN LDC LIST")

    from src import config
    evi = pd.read_csv(config.OUTPUT_DIR / OUT_NAME)

    step("LDC vs non-LDC comparison")
    ldc_test = bm.compare_ldc_vs_non_ldc(evi)
    save_json(ldc_test, "benchmark_ldc_comparison.json")
    if "median_ldc" in ldc_test:
        note(f"median EVI: LDCs {ldc_test['median_ldc']:.3f}, "
             f"non-LDCs {ldc_test['median_non_ldc']:.3f}")
        note(f"Mann-Whitney p = {ldc_test['p_value']:.4f}, "
             f"rank-biserial effect size {ldc_test['rank_biserial']:.3f}")
        if ldc_test["p_value"] < 0.05:
            note("LDCs score significantly higher on the reconstructed EVI - "
                 "consistent with, though not proof of, the index capturing "
                 "something real about structural vulnerability")
        else:
            note("no significant difference was found - worth investigating "
                 "before claiming the index tracks vulnerability at all")
    else:
        note(ldc_test.get("note", "test could not be run"))

    step("the disagreements: where the index and the LDC list see things differently")
    cases = bm.misclassified_cases(evi)
    save_table(cases["high_scoring_non_ldc"], "benchmark_high_scoring_non_ldc.csv")
    save_table(cases["low_scoring_ldc"], "benchmark_low_scoring_ldc.csv")
    print("Non-LDCs with a surprisingly high reconstructed EVI:")
    print(cases["high_scoring_non_ldc"][["country", "evi", "exposure_index",
                                         "shock_index"]].round(3).to_string(index=False))
    print("\nLDCs with a surprisingly low reconstructed EVI:")
    print(cases["low_scoring_ldc"][["country", "evi", "exposure_index",
                                    "shock_index"]].round(3).to_string(index=False))

    step("correlation with income")
    income_corr = bm.correlation_with_income(evi)
    save_json(income_corr, "benchmark_income_correlation.json")
    if "spearman_rho" in income_corr:
        note(f"Spearman rho against log GNI per capita: "
             f"{income_corr['spearman_rho']:.3f} (p = {income_corr['p_value']:.4f})")
        if abs(income_corr["spearman_rho"]) > 0.85:
            note("this is a strong correlation - worth checking in the write-up "
                 "whether the index is adding anything beyond what income "
                 "alone would already tell you")

    banner("SCRIPT 4 FINISHED")


if __name__ == "__main__":
    main()
