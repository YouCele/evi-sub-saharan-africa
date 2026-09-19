# How to run this, and where each result lands

## Execution order

| order | command | what it does | needs internet? |
|---|---|---|---|
| 1 | `python scripts/run_01_fetch_data.py` | pulls the country registry and every indicator from the World Bank API, caches to `data/raw/` | **yes** |
| 2 | `python scripts/run_02_build_indicators.py` | builds the cross-sectional table, computes export concentration and instability, handles missingness | no |
| 3 | `python scripts/run_03_build_index.py` | normalises everything, builds the composite EVI and the PCA-weighted alternative | no |
| 4 | `python scripts/run_04_benchmark_validate.py` | compares the reconstructed EVI against the real UN LDC list | no |
| 5 | `python scripts/run_05_robustness.py` | weighting comparison, jackknife, missingness-threshold sensitivity | no |
| 6 | `python scripts/run_06_report.py` | builds `reports/final_report.md` from the saved outputs | no |

Or all six in order:

```
python scripts/run_all.py
python scripts/run_all.py 3 4 5     # only a subset
```

Steps 2 through 6 are fast (seconds) and re-runnable without internet once
step 1's cache exists. If you want to force a fresh pull from the API
(say, after a World Bank data revision), delete `data/raw/*.csv` and
re-run step 1, or call the fetch functions with `refresh=True`.

## Where the results are

| file | what it holds |
|---|---|
| `data/raw/country_registry.csv` | every economy the World Bank tracks, with region classification |
| `data/raw/indicator_*.csv` | one file per indicator, full time series, all Sub-Saharan African countries |
| `data/processed/ssf_countries.csv` | the Sub-Saharan Africa country list actually used, as the API classified it |
| `data/processed/country_wide.csv` | one row per country, every raw and derived indicator, before the exclusion rule |
| `data/processed/country_wide_final.csv` | the same, after excluding countries with too much missing data |
| `outputs/missingness_by_indicator.csv`, `outputs/missingness_by_country.csv` | missingness, two ways |
| `outputs/exclusion_decisions.csv` | which countries were dropped from the composite index, and why |
| `outputs/exposure_components.csv`, `outputs/econ_instability_components.csv` | the normalised inputs to each sub-index |
| `outputs/evi_scores.csv` | the full ranking: EVI, both sub-indices, LDC status, and the partial-index flag |
| `outputs/pca_scores.csv` | the PCA-weighted alternative ranking |
| `outputs/benchmark_ldc_comparison.json` | the Mann-Whitney test of LDC vs non-LDC scores |
| `outputs/benchmark_high_scoring_non_ldc.csv`, `outputs/benchmark_low_scoring_ldc.csv` | the specific disagreements between the index and the LDC list |
| `outputs/benchmark_income_correlation.json` | how much the index just tracks income |
| `outputs/robustness_jackknife.csv` | which components the ranking depends on most |
| `outputs/robustness_biggest_rank_movers.csv` | which countries move most between weighting schemes |
| `outputs/robustness_missingness_threshold.csv` | how many countries would be covered at different missingness cut-offs |
| `reports/research_decision_log.md` | every methodological choice, written before running the numbers |
| `reports/final_report.md` | the full write-up, generated from the files above |

### Figures

`figures/01_evi_ranking.png`, `02_evi_by_ldc_status.png`,
`03_evi_vs_income.png`, `04_missingness_by_country.png`,
`05_jackknife_sensitivity.png`, `06_equal_weight_vs_pca.png`.

## After you run it

`outputs/`, `figures/`, and `reports/final_report.md` are empty in this
repository until you run the pipeline yourself (see the note in
`README.md` about why). Once you've run it and are happy with the
results, commit those three - they're the actual deliverable, the same
way the NHANES project's computed tables and figures were committed
rather than left for a reader to regenerate.
