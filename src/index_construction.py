"""
Index construction: normalise every component to a common 0-1 scale,
average into two sub-indices, average those into the composite EVI.

The UN CDP's own EVI uses min-max normalisation and simple (unweighted)
averaging at every level - not because that is the only defensible choice,
but because it is transparent and does not quietly let the analyst's
weighting preferences decide the answer. This project follows the same
convention for the main index, and builds a PCA-weighted alternative
separately so the two can be compared rather than picking one silently.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from . import config


def min_max_normalise(s: pd.Series, higher_is_worse: bool = True) -> pd.Series:
    """
    Scale to 0-1 across the countries actually being compared, with 1
    always meaning "more vulnerable on this component".

    Normalising within this specific set of countries, rather than against
    a fixed global scale, means the index describes relative standing
    within Sub-Saharan Africa - it does not claim to place these countries
    on an absolute world scale, and the report says so.
    """
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(np.nan, index=s.index)
    scaled = (s - lo) / (hi - lo)
    return scaled if higher_is_worse else 1 - scaled


def build_exposure_components(wide: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=wide.index)
    out["iso3"] = wide["iso3"]
    out["population_norm"] = min_max_normalise(wide["population"], higher_is_worse=False)
    out["agri_share_gdp_norm"] = min_max_normalise(wide["agri_share_gdp"], higher_is_worse=True)
    out["export_concentration_norm"] = min_max_normalise(wide["export_concentration"],
                                                          higher_is_worse=True)
    out["landlocked_norm"] = wide["landlocked"].astype(float)   # already 0/1
    return out


def build_shock_components(wide: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=wide.index)
    out["iso3"] = wide["iso3"]
    out["export_instability_norm"] = min_max_normalise(
        wide["exports_constant_usd_instability"], higher_is_worse=True)
    out["agri_instability_norm"] = min_max_normalise(
        wide["agri_value_constant_usd_instability"], higher_is_worse=True)
    return out


def composite_index(exposure: pd.DataFrame, shock: pd.DataFrame) -> pd.DataFrame:
    """
    Average within each sub-index (ignoring a country's missing components,
    so one gap does not zero out the whole sub-index), then average the two
    sub-indices into the composite EVI.
    """
    exp_cols = [c for c in exposure.columns if c != "iso3"]
    shk_cols = [c for c in shock.columns if c != "iso3"]

    out = exposure[["iso3"]].merge(shock[["iso3"]], on="iso3", how="outer")
    out = out.merge(exposure, on="iso3", how="left").merge(shock, on="iso3", how="left")

    out["exposure_index"] = out[exp_cols].mean(axis=1, skipna=True)
    out["exposure_n_components"] = out[exp_cols].notna().sum(axis=1)
    out["shock_index"] = out[shk_cols].mean(axis=1, skipna=True)
    out["shock_n_components"] = out[shk_cols].notna().sum(axis=1)

    out["evi"] = out[["exposure_index", "shock_index"]].mean(axis=1, skipna=True)
    out["evi_rank"] = out["evi"].rank(ascending=False, method="min")

    # a country can clear the overall missingness threshold with every
    # exposure input present and every shock input absent (or the reverse);
    # its "composite" score is then really just one sub-index wearing the
    # composite's name, which is worth knowing rather than discovering later
    out["partial_index"] = (out["exposure_n_components"] == 0) | (out["shock_n_components"] == 0)
    return out.sort_values("evi", ascending=False).reset_index(drop=True)


def pca_weighted_index(exposure: pd.DataFrame, shock: pd.DataFrame) -> pd.DataFrame:
    """
    An alternative composite built from the first principal component of all
    six normalised components together, instead of the two-stage equal-
    weight average above.

    PCA weighting lets the data decide which components move together and
    weights accordingly, rather than treating all six as equally important
    by assumption. It has its own assumption baked in - that the direction
    of greatest variance is the direction of greatest vulnerability - which
    will not always be true, so this is reported as a comparison, not a
    replacement for the main index.
    """
    merged = exposure.merge(shock, on="iso3", how="inner")
    cols = [c for c in merged.columns if c != "iso3"]
    complete = merged.dropna(subset=cols)
    if len(complete) < 10:
        return pd.DataFrame(columns=["iso3", "pca_score", "pca_rank"])

    X = StandardScaler().fit_transform(complete[cols])
    pca = PCA(n_components=1, random_state=config.RANDOM_SEED)
    score = pca.fit_transform(X).ravel()

    # PCA's sign is arbitrary; orient it so higher = more vulnerable by
    # checking correlation with the equal-weight EVI on the same countries
    reference = complete[cols].mean(axis=1)
    if np.corrcoef(score, reference)[0, 1] < 0:
        score = -score

    out = pd.DataFrame(dict(iso3=complete["iso3"], pca_score=score))
    out["pca_rank"] = out["pca_score"].rank(ascending=False, method="min")
    explained = float(pca.explained_variance_ratio_[0])
    out.attrs["explained_variance_ratio"] = explained
    return out.sort_values("pca_score", ascending=False).reset_index(drop=True)
