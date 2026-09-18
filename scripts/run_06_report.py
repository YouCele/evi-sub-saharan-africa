"""
Script 6 - build the final report from the files in outputs/, the same way
the NHANES project's report was generated: every number and every
interpretive sentence is read from what the pipeline actually produced,
so the report cannot say something the analysis did not.

Input  : outputs/*.csv, outputs/*.json
Output : reports/final_report.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import config
from src.utils import banner, note

OUT = config.OUTPUT_DIR


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / name)


def jload(name: str) -> dict:
    return json.loads((OUT / name).read_text())


def md(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except ImportError:
        return "```\n" + df.to_string(index=False) + "\n```"


def main() -> None:
    banner("STEP 6 - BUILDING THE FINAL REPORT")

    for required in ["evi_scores.csv", "missingness_by_country.csv",
                     "exclusion_decisions.csv", "robustness_jackknife.csv"]:
        if not (OUT / required).exists():
            note(f"{required} not found - run scripts 1 through 5 first")
            raise SystemExit(1)

    evi = load("evi_scores.csv")
    missing_country = load("missingness_by_country.csv")
    missing_indicator = load("missingness_by_indicator.csv")
    exclusions = load("exclusion_decisions.csv")
    jack = load("robustness_jackknife.csv")
    weight_movers = (load("robustness_biggest_rank_movers.csv")
                     if (OUT / "robustness_biggest_rank_movers.csv").exists() else None)
    threshold_sens = load("robustness_missingness_threshold.csv")
    ldc_test = jload("benchmark_ldc_comparison.json")
    income_corr = jload("benchmark_income_correlation.json")
    high_non_ldc = load("benchmark_high_scoring_non_ldc.csv")
    low_ldc = load("benchmark_low_scoring_ldc.csv")
    index_summary = jload("index_construction_summary.json")

    n_total = len(missing_country)
    n_excluded = int(exclusions["excluded"].sum())
    n_kept = n_total - n_excluded
    partial = evi[evi.get("partial_index", False) == True] if "partial_index" in evi.columns else evi.iloc[0:0]

    L: list[str] = []
    A = L.append

    A("# A reconstructed Economic Vulnerability Index for Sub-Saharan Africa")
    A("")
    A("*Generated from the saved pipeline outputs by `scripts/run_06_report.py`. "
      "Every number below comes from `outputs/`; nothing here was typed in "
      "separately from the analysis.*")
    A("")

    A("## 1. What this is, and what it is not")
    A("")
    A("This project reconstructs the structure of the UN Committee for "
      "Development Policy's Economic Vulnerability Index (EVI) - one of the "
      "three criteria used to classify Least Developed Countries, alongside "
      "income and a Human Assets Index - using World Bank Open Data instead "
      "of the UN's own underlying sources. It is a reconstruction, not the "
      "official index: several components are approximated with coarser "
      "proxies where the original UN data source (UN Comtrade for export "
      "concentration, EM-DAT for disaster impact) was not part of this "
      "project's data. Every substitution is documented in "
      "`reports/research_decision_log.md`.")
    A("")
    A(f"Scope: Sub-Saharan Africa, as the World Bank's own region "
      f"classification currently defines it. {n_total} countries were "
      f"assessed, {n_kept} retained in the final composite index, "
      f"{n_excluded} excluded for missing more than "
      f"{100*config.MAX_MISSING_SHARE:.0f}% of the required inputs.")
    A("")

    A("## 2. Methodology")
    A("")
    A("Two sub-indices, each the equal-weighted average of its available "
      "components (a country missing one component is not penalised twice "
      "by having the whole sub-index blank):")
    A("")
    A("**Exposure** - population size, agriculture's share of GDP, export "
      "concentration (a four-category Herfindahl index over food, fuel, ores "
      "and metals, and manufactured exports), and landlocked status.")
    A("")
    A("**Shock** - export revenue instability and agricultural production "
      "instability, both measured as the standard deviation of residuals "
      f"from a log-linear trend over {config.START_YEAR}-{config.END_YEAR}.")
    A("")
    A("The composite EVI is the average of the two sub-indices. All "
      "components are min-max normalised across the countries in this study "
      "(not against a fixed global scale), so the index describes relative "
      "standing within this group of countries.")
    A("")

    A("## 3. Missing data")
    A("")
    A(md(missing_indicator.round(4)))
    A("")
    A("Countries with the most missing inputs:")
    A("")
    A(md(missing_country.head(10)[["country", "n_missing", "n_required",
                                   "missing_share"]].round(3)))
    A("")
    if n_excluded:
        excl_rows = exclusions[exclusions["excluded"]]
        A(f"{n_excluded} countries were excluded from the composite index: "
          + ", ".join(excl_rows["country"]) + ".")
    else:
        A("No country crossed the exclusion threshold; every Sub-Saharan "
          "African economy in scope has a composite score.")
    A("")
    if len(partial):
        A(f"**{len(partial)} of the retained countries have every input for "
          f"one sub-index and none for the other** (" +
          ", ".join(partial["country"]) + "): their EVI is really an "
          "exposure-only or shock-only score wearing the composite's name, "
          "not a genuine average of both. They pass the overall missingness "
          "threshold because their missing inputs are concentrated in a "
          "single sub-index rather than spread across both.")
        A("")

    A("## 4. Results")
    A("")
    A("Most vulnerable, by the reconstructed EVI:")
    A("")
    A(md(evi.head(10)[["country", "evi", "exposure_index", "shock_index",
                       "is_ldc"]].round(3)))
    A("")
    A("Least vulnerable:")
    A("")
    A(md(evi.tail(10)[["country", "evi", "exposure_index", "shock_index",
                       "is_ldc"]].round(3)))
    A("")

    A("## 5. Benchmark validation against the UN LDC list")
    A("")
    if "median_ldc" in ldc_test:
        sig = ldc_test["p_value"] < 0.05
        A(f"UN-classified LDCs have a median reconstructed EVI of "
          f"{ldc_test['median_ldc']:.3f}, against {ldc_test['median_non_ldc']:.3f} "
          f"for non-LDCs (Mann-Whitney p = {ldc_test['p_value']:.4f}, "
          f"rank-biserial effect size {ldc_test['rank_biserial']:.3f}, "
          f"n = {ldc_test['n_ldc']} LDCs and {ldc_test['n_non_ldc']} non-LDCs). ")
        A(("This difference is unlikely to be chance, which is a reasonable "
           "sanity check that the reconstruction is measuring something real."
           if sig else
           "This difference did not reach conventional significance, which "
           "is worth investigating before treating the reconstructed index "
           "as informative.") + "")
    else:
        A(ldc_test.get("note", "the comparison could not be run"))
    A("")
    A("Cases worth looking at individually - non-LDCs the index scores as "
      "surprisingly vulnerable:")
    A("")
    A(md(high_non_ldc[["country", "evi", "exposure_index", "shock_index"]].round(3)))
    A("")
    A("LDCs the index scores as surprisingly low:")
    A("")
    A(md(low_ldc[["country", "evi", "exposure_index", "shock_index"]].round(3)))
    A("")
    if "spearman_rho" in income_corr:
        rho = income_corr["spearman_rho"]
        A(f"Correlation with log GNI per capita: Spearman rho = {rho:.3f} "
          f"(p = {income_corr['p_value']:.4f}). " +
          ("This is high enough that part of the story here may just be "
           "income, not a distinct vulnerability signal."
           if abs(rho) > 0.85 else
           "The index tracks income to some degree, as expected, without "
           "simply reproducing it."))
    A("")

    A("## 6. Robustness")
    A("")
    A("Removing each component in turn and checking how much the ranking "
      "moves (1.0 = no change, lower = the ranking depends heavily on that "
      "component):")
    A("")
    A(md(jack.round(3)))
    A("")
    if weight_movers is not None:
        A("Countries whose rank changes most between the equal-weight index "
          "and the PCA-weighted alternative:")
        A("")
        A(md(weight_movers.round(1)))
        A("")
    A("How many countries the index would cover under different missingness "
      "thresholds:")
    A("")
    A(md(threshold_sens))
    A("")

    A("## 7. Limitations")
    A("")
    A("- Export concentration is approximated from four broad World Bank "
      "categories, not the roughly 90-category UN Comtrade breakdown the "
      "official EVI uses. A country's true export concentration could be "
      "understated by this simplification.")
    A("- Remoteness is approximated with a landlocked/not-landlocked flag, "
      "not the UN's continuous, trade-weighted distance measure.")
    A("- The shock sub-index has no disaster-impact component (EM-DAT data "
      "was not part of this project), so a country's exposure to floods, "
      "drought or storms is not directly represented anywhere in this index.")
    A("- LDC status is not a direct label for the true EVI - it depends on "
      "income and human assets too - so agreement or disagreement with LDC "
      "status is suggestive, not a precise accuracy check.")
    A("- All normalisation is relative to the Sub-Saharan African countries "
      "in this study; the scores are not comparable to a global ranking.")
    A("")

    A("## 8. Conclusion")
    A("")
    A(f"Out of {n_total} Sub-Saharan African economies assessed, {n_kept} "
      f"have a composite score after excluding {n_excluded} for missing "
      f"data. [The concluding paragraph is left for you to write once "
      f"you've looked at the actual ranking and the benchmark results above "
      f"- in particular, whether the LDC comparison in section 5 came out "
      f"significant, and which specific countries in the misclassification "
      f"tables have a story worth telling.]")
    A("")

    path = config.REPORT_DIR / "final_report.md"
    path.write_text("\n".join(L))
    note(f"saved {path.relative_to(config.PROJECT_ROOT)}")

    banner("SCRIPT 6 FINISHED")


if __name__ == "__main__":
    main()
