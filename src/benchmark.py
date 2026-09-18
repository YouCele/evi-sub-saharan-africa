"""
Benchmark validation.

The UN classifies a country as a Least Developed Country using three
criteria together - income (GNI per capita), human assets, and economic
and environmental vulnerability (the actual, official EVI, computed by
UNCTAD with data this project does not have access to). This project's
reconstructed EVI is being compared against LDC status as a sanity check,
not treated as if it alone determines that status - a country can be a
non-LDC with a high reconstructed EVI (small vulnerable island or mineral-
dependent economy that graduated on income) and the report says so rather
than treating every mismatch as a modelling error.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import config


def attach_ldc_status(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["is_ldc"] = out["iso3"].isin(config.LDC_ISO3)
    return out


def compare_ldc_vs_non_ldc(df: pd.DataFrame, score_col: str = "evi") -> dict:
    """
    Is the reconstructed EVI significantly higher among LDCs?

    Mann-Whitney U rather than a t-test, since there is no reason to expect
    the score to be normally distributed in either group and the sample on
    each side is modest (roughly 30 LDCs against 15-20 non-LDCs).
    """
    d = df.dropna(subset=[score_col])
    ldc = d.loc[d["is_ldc"], score_col]
    non_ldc = d.loc[~d["is_ldc"], score_col]
    if len(ldc) < 5 or len(non_ldc) < 5:
        return dict(n_ldc=len(ldc), n_non_ldc=len(non_ldc),
                   note="too few countries on one side for a meaningful test")

    u = stats.mannwhitneyu(ldc, non_ldc, alternative="greater")
    # rank-biserial effect size, consistent with how the NHANES project
    # reported the same test
    effect = 2 * u.statistic / (len(ldc) * len(non_ldc)) - 1

    return dict(
        n_ldc=len(ldc), n_non_ldc=len(non_ldc),
        median_ldc=float(ldc.median()), median_non_ldc=float(non_ldc.median()),
        mean_ldc=float(ldc.mean()), mean_non_ldc=float(non_ldc.mean()),
        mannwhitney_u=float(u.statistic), p_value=float(u.pvalue),
        rank_biserial=float(effect),
    )


def misclassified_cases(df: pd.DataFrame, score_col: str = "evi",
                        n: int = 8) -> dict[str, pd.DataFrame]:
    """
    The countries the reconstructed index disagrees with LDC status about
    most: non-LDCs that score surprisingly high, and LDCs that score
    surprisingly low. These are the cases worth discussing individually in
    the write-up, not the aggregate statistic alone.
    """
    d = df.dropna(subset=[score_col]).sort_values(score_col, ascending=False)
    high_scoring_non_ldc = d[~d["is_ldc"]].head(n)
    low_scoring_ldc = d[d["is_ldc"]].tail(n)
    return dict(high_scoring_non_ldc=high_scoring_non_ldc,
               low_scoring_ldc=low_scoring_ldc)


def correlation_with_income(df: pd.DataFrame, score_col: str = "evi",
                            income_col: str = "gni_per_capita_atlas") -> dict:
    """
    How much does the reconstructed EVI just track income? Some overlap is
    expected - poorer countries are often also more exposed - but the EVI
    is supposed to capture something structural beyond income alone. A
    correlation near 1 would suggest the index is mostly re-deriving income.
    """
    d = df.dropna(subset=[score_col, income_col])
    if len(d) < 10:
        return dict(n=len(d), note="too few countries with both values")
    rho, p = stats.spearmanr(d[score_col], np.log(d[income_col]))
    return dict(n=len(d), spearman_rho=float(rho), p_value=float(p),
               note="correlated against log income, since income is heavily "
                    "right-skewed across this set of countries")
