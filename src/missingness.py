"""
Missingness analysis and the decision about what to do with it.

African country statistics genuinely have coverage gaps - this is not a
data-cleaning inconvenience to paper over, it is itself part of what a
vulnerability index has to reckon with. A country too small or too fragile
to report full statistics to the World Bank is often, not coincidentally,
also a country you would expect to score as more vulnerable. Dropping it
silently for missing data would bias the whole exercise in one direction.

The policy adopted here: report missingness by country and by indicator
first, then exclude a country from the composite index only if it is
missing more than config.MAX_MISSING_SHARE of the required inputs. A
country that clears that bar keeps a per-component score computed on
whatever it does have; nothing is imputed from other countries' values.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .utils import note, step


def missingness_by_country(wide: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    present = wide[columns].notna()
    out = pd.DataFrame(dict(
        iso3=wide["iso3"], country=wide["country"],
        n_required=len(columns),
        n_present=present.sum(axis=1),
        n_missing=len(columns) - present.sum(axis=1),
        missing_share=1 - present.mean(axis=1),
    ))
    return out.sort_values("missing_share", ascending=False)


def missingness_by_indicator(wide: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = []
    for c in columns:
        if c not in wide.columns:
            rows.append(dict(indicator=c, missing_pct=np.nan,
                             note="column not found - check the fetch step"))
            continue
        rows.append(dict(indicator=c, n=len(wide),
                         n_missing=int(wide[c].isna().sum()),
                         missing_pct=float(wide[c].isna().mean())))
    return pd.DataFrame(rows).sort_values("missing_pct", ascending=False)


def apply_exclusion_rule(missing_by_country: pd.DataFrame,
                         max_missing_share: float | None = None) -> tuple[list[str], pd.DataFrame]:
    """
    Decide which countries are excluded from the composite index.

    Returns the list of ISO3 codes to KEEP, and a decision table recording
    the reason for every country, kept or excluded.
    """
    threshold = max_missing_share if max_missing_share is not None else config.MAX_MISSING_SHARE
    decisions = missing_by_country.copy()
    decisions["excluded"] = decisions["missing_share"] > threshold
    decisions["reason"] = np.where(
        decisions["excluded"],
        "missing more than " + f"{100*threshold:.0f}% of the required inputs "
        "(" + decisions["n_missing"].astype(str) + " of " +
        decisions["n_required"].astype(str) + ")",
        "retained; component scores computed on the inputs that are available")

    kept = decisions.loc[~decisions["excluded"], "iso3"].tolist()
    n_excluded = int(decisions["excluded"].sum())
    note(f"{n_excluded} of {len(decisions)} countries excluded from the composite "
         f"index at a {100*threshold:.0f}% missingness threshold")
    if n_excluded:
        for _, r in decisions[decisions["excluded"]].iterrows():
            note(f"  excluded: {r['country']} ({r['iso3']}) - {r['reason']}")
    return kept, decisions
