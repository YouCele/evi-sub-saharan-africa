"""Figures. Each one answers one question, saved to figures/ as PNG."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .utils import save_fig

plt.rcParams.update({
    "figure.dpi": 110, "font.size": 9, "axes.grid": True,
    "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False,
})

LDC_COLOUR, NON_LDC_COLOUR = "#D1495B", "#5B8FF9"


def fig_ranking(evi_df: pd.DataFrame, name: str = "01_evi_ranking.png") -> None:
    d = evi_df.dropna(subset=["evi"]).sort_values("evi")
    colours = [LDC_COLOUR if x else NON_LDC_COLOUR for x in d["is_ldc"]]
    fig, ax = plt.subplots(figsize=(7, 0.28 * len(d) + 1.5))
    ax.barh(d["country"], d["evi"], color=colours)
    ax.set_xlabel("composite EVI (0 = least vulnerable, 1 = most vulnerable)")
    ax.set_title("Reconstructed Economic Vulnerability Index, Sub-Saharan Africa")
    handles = [plt.Rectangle((0, 0), 1, 1, color=LDC_COLOUR),
              plt.Rectangle((0, 0), 1, 1, color=NON_LDC_COLOUR)]
    ax.legend(handles, ["UN-classified LDC", "not classified as an LDC"],
             loc="lower right", fontsize=8)
    save_fig(fig, name)


def fig_ldc_comparison(evi_df: pd.DataFrame, name: str = "02_evi_by_ldc_status.png") -> None:
    d = evi_df.dropna(subset=["evi"])
    fig, ax = plt.subplots(figsize=(5, 4))
    data = [d.loc[~d["is_ldc"], "evi"], d.loc[d["is_ldc"], "evi"]]
    bp = ax.boxplot(data, labels=["not an LDC", "LDC"], showfliers=False, patch_artist=True)
    for patch, colour in zip(bp["boxes"], [NON_LDC_COLOUR, LDC_COLOUR]):
        patch.set_facecolor(colour)
        patch.set_alpha(0.6)
    for i, grp in enumerate(data, start=1):
        jitter = np.random.default_rng(0).normal(i, 0.04, size=len(grp))
        ax.scatter(jitter, grp, s=14, color="black", alpha=0.5, zorder=3)
    ax.set_ylabel("composite EVI")
    ax.set_title("EVI by UN LDC classification")
    save_fig(fig, name)


def fig_income_scatter(evi_df: pd.DataFrame,
                       name: str = "03_evi_vs_income.png") -> None:
    d = evi_df.dropna(subset=["evi", "gni_per_capita_atlas"])
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for is_ldc, colour, label in [(True, LDC_COLOUR, "LDC"),
                                  (False, NON_LDC_COLOUR, "not an LDC")]:
        sub = d[d["is_ldc"] == is_ldc]
        ax.scatter(sub["gni_per_capita_atlas"], sub["evi"], color=colour,
                  label=label, alpha=0.75, s=30)
    ax.set_xscale("log")
    ax.set_xlabel("GNI per capita, Atlas method (current US$, log scale)")
    ax.set_ylabel("composite EVI")
    ax.set_title("Vulnerability is not just a restatement of income")
    ax.legend(fontsize=8)
    save_fig(fig, name)


def fig_missingness(missing_by_country: pd.DataFrame,
                    name: str = "04_missingness_by_country.png") -> None:
    d = missing_by_country.sort_values("missing_share")
    fig, ax = plt.subplots(figsize=(7, 0.28 * len(d) + 1.5))
    ax.barh(d["country"], 100 * d["missing_share"], color="#8C8C8C")
    ax.set_xlabel("share of required inputs missing (%)")
    ax.set_title("Data completeness by country")
    save_fig(fig, name)


def fig_jackknife(jack: pd.DataFrame, name: str = "05_jackknife_sensitivity.png") -> None:
    d = jack.sort_values("spearman_rho_vs_full")
    fig, ax = plt.subplots(figsize=(6.5, 0.4 * len(d) + 1.5))
    ax.barh(d["component_removed"], d["spearman_rho_vs_full"], color="#5B8FF9")
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("rank correlation with the full index after removing this component")
    ax.set_title("How much does the ranking depend on any single component?")
    save_fig(fig, name)


def fig_weighting_comparison(evi_df: pd.DataFrame, pca_df: pd.DataFrame,
                             name: str = "06_equal_weight_vs_pca.png") -> None:
    merged = evi_df.merge(pca_df, on="iso3", how="inner")
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.scatter(merged["evi_rank"], merged["pca_rank"], color="#5B8FF9", alpha=0.75)
    lim = [merged[["evi_rank", "pca_rank"]].min().min() - 1,
          merged[["evi_rank", "pca_rank"]].max().max() + 1]
    ax.plot(lim, lim, "--", color="grey", lw=1)
    ax.set_xlabel("rank, equal-weight EVI")
    ax.set_ylabel("rank, PCA-weighted alternative")
    ax.set_title("Do the two weighting schemes agree on the ranking?")
    save_fig(fig, name)
