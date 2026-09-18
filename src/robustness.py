"""
Robustness checks. Each one answers a specific worry about whether the
index construction choices are actually driving the results:

    weighting scheme      does PCA weighting reorder countries much
                           compared with the equal-weight average?
    jackknife              how much does the ranking depend on any single
                           component - would dropping one change the story?
    missingness threshold  how sensitive is the excluded-country list to
                           where that 40% line was drawn?
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import config
from .index_construction import composite_index
from .missingness import apply_exclusion_rule


def weighting_scheme_comparison(evi_df: pd.DataFrame, pca_df: pd.DataFrame) -> dict:
    merged = evi_df.merge(pca_df, on="iso3", how="inner")
    if len(merged) < 10:
        return dict(n=len(merged), note="too few overlapping countries to compare")
    rho, p = stats.spearmanr(merged["evi_rank"], merged["pca_rank"])
    biggest_movers = merged.assign(
        rank_change=(merged["evi_rank"] - merged["pca_rank"]).abs()
    ).sort_values("rank_change", ascending=False).head(8)
    return dict(n=len(merged), spearman_rho=float(rho), p_value=float(p),
               biggest_movers=biggest_movers[["iso3", "country", "evi_rank",
                                              "pca_rank", "rank_change"]])


def jackknife_components(exposure: pd.DataFrame, shock: pd.DataFrame) -> pd.DataFrame:
    """
    Recompute the composite index with each component removed in turn, and
    correlate the resulting ranking against the full index. A component
    whose removal barely changes the ranking is not doing much independent
    work; a component whose removal changes the ranking a lot is carrying
    real weight, for better or worse.
    """
    full = composite_index(exposure, shock)
    exp_cols = [c for c in exposure.columns if c != "iso3"]
    shk_cols = [c for c in shock.columns if c != "iso3"]
    all_cols = [("exposure", c) for c in exp_cols] + [("shock", c) for c in shk_cols]

    rows = []
    for sub_index, col in all_cols:
        exp_drop = exposure.drop(columns=[col]) if sub_index == "exposure" else exposure
        shk_drop = shock.drop(columns=[col]) if sub_index == "shock" else shock
        reduced = composite_index(exp_drop, shk_drop)
        merged = full[["iso3", "evi_rank"]].merge(
            reduced[["iso3", "evi_rank"]], on="iso3", suffixes=("_full", "_reduced"))
        rho, _ = stats.spearmanr(merged["evi_rank_full"], merged["evi_rank_reduced"])
        rows.append(dict(component_removed=col, sub_index=sub_index,
                         spearman_rho_vs_full=float(rho)))
    return pd.DataFrame(rows).sort_values("spearman_rho_vs_full")


def missingness_threshold_sensitivity(missing_by_country: pd.DataFrame,
                                      thresholds=(0.2, 0.3, 0.4, 0.5, 0.6)) -> pd.DataFrame:
    rows = []
    for t in thresholds:
        kept, _ = apply_exclusion_rule(missing_by_country, max_missing_share=t)
        rows.append(dict(threshold=t, n_kept=len(kept),
                         n_excluded=len(missing_by_country) - len(kept)))
    return pd.DataFrame(rows)
