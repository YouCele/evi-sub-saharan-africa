"""
Derived indicators that are not fetched directly from the World Bank, but
built from the raw series in data_loading.py.

Two things are built here:

1. Export concentration (a Herfindahl-Hirschman index over four broad
   merchandise export categories). See the note in config.py about how this
   differs from the UN CDP's own ~90-category version.

2. Instability indices for exports and agricultural production. The UN CDP's
   own method detrends each country's series with a centred moving average
   and measures deviations from it. This project uses a log-linear trend
   instead - simpler to implement correctly and easier to audit - and says
   so here rather than presenting the number as if it were the official one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def export_concentration(wide: pd.DataFrame) -> pd.Series:
    """
    Herfindahl-Hirschman index over four broad export categories.

    Each row should have the four config.EXPORT_SHARE_COLUMNS as percentages
    of merchandise exports (0-100, not necessarily summing to exactly 100,
    since re-exports and unclassified goods are not in any of the four
    categories). HHI = sum of squared shares expressed as fractions, so the
    theoretical range is 0 (perfectly diversified across many categories) to
    1 (all exports in one category). With only four categories the practical
    floor is 0.25, not 0 - this is the cost of the simplification and is
    noted in the report rather than hidden.
    """
    shares = wide[config.EXPORT_SHARE_COLUMNS].copy()
    total = shares.sum(axis=1)
    # renormalise so the four categories sum to 1 before squaring, otherwise
    # a country with a lot of exports outside these four categories would
    # look artificially diversified just because the shares do not add up
    normalised = shares.div(total.replace(0, np.nan), axis=0)
    hhi = (normalised ** 2).sum(axis=1)
    hhi[total.isna() | (total == 0)] = np.nan
    return hhi


def instability_index(series: pd.DataFrame, value_col: str,
                      min_years: int | None = None) -> pd.Series:
    """
    Log-linear detrended instability, per country.

    series must have columns iso3, year, value_col. For each country: fit
    log(value) ~ year by ordinary least squares, take the residuals, and
    report 100 * the standard deviation of the residuals. Because the
    regression is in log space, this is approximately a percentage
    deviation from trend - a country whose exports bounce between plus and
    minus 15% of their long-run trend gets a score near 15, a country on a
    smooth trend gets a score near 0.

    Countries with fewer than min_years of usable data return NaN rather
    than an instability estimate built on too little history.
    """
    min_years = min_years or config.MIN_YEARS_FOR_INSTABILITY
    out = {}
    for iso3, g in series.groupby("iso3"):
        g = g.dropna(subset=[value_col])
        g = g[g[value_col] > 0]        # log is undefined at 0 or below
        if len(g) < min_years:
            out[iso3] = np.nan
            continue
        x = g["year"].to_numpy(dtype=float)
        y = np.log(g[value_col].to_numpy(dtype=float))
        x_centered = x - x.mean()
        slope = np.sum(x_centered * (y - y.mean())) / np.sum(x_centered ** 2)
        intercept = y.mean() - slope * x.mean()
        resid = y - (intercept + slope * x)
        out[iso3] = 100 * float(np.std(resid, ddof=1))
    return pd.Series(out, name=f"{value_col}_instability")


def years_of_coverage(series: pd.DataFrame, value_col: str) -> pd.Series:
    """How many non-missing years each country has for one indicator - used
    by the missingness analysis to explain why an instability score is or
    is not available."""
    return series.dropna(subset=[value_col]).groupby("iso3").size().rename(
        f"{value_col}_n_years")


def attach_reference_year(long_df: pd.DataFrame, value_col: str,
                          year: int | None = None) -> pd.Series:
    """
    The value for the single reference year, with a documented fallback:
    if the exact reference year is missing for a country, use the closest
    available year within two years either side rather than leaving it
    blank purely because of a one-year reporting lag, which is common in
    African country submissions to the World Bank.
    """
    year = year or config.REFERENCE_YEAR
    out = {}
    for iso3, g in long_df.groupby("iso3"):
        g = g.dropna(subset=[value_col])
        if g.empty:
            out[iso3] = np.nan
            continue
        g = g.assign(_gap=(g["year"] - year).abs())
        best = g.sort_values("_gap").iloc[0]
        out[iso3] = best[value_col] if best["_gap"] <= 2 else np.nan
    return pd.Series(out, name=value_col)
