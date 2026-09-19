# Research decision log

Every methodological choice that could have gone another way, and why it was
made this way. Numbers are not repeated here — they live in `outputs/` and
in `reports/final_report.md` once the pipeline has actually been run.

## Scope

| item | decision | reason |
|---|---|---|
| country set | Sub-Saharan Africa, as the World Bank's own region classification defines it *at run time* | avoids hardcoding a guess about edge cases like Djibouti or Sudan, which are classified differently by different organisations; the code asks the data source instead of assuming |
| study window | 2008-2023 | recent enough that most countries have real World Bank coverage, long enough for the instability measures to mean something |
| reference year | 2022, with a ±2 year fallback to the closest available year | a single up-to-date cross-section, without losing a country purely because of a one-year reporting lag |

## Indicator selection

The project reconstructs the *structure* of the UN CDP's Economic
Vulnerability Index, not the index itself. Every place a substitution was
made is listed here.

| official EVI component | this project's version | why the substitution |
|---|---|---|
| population size | World Bank `SP.POP.TOTL` | direct match, no substitution needed |
| share of agriculture, forestry, fishery in GDP | World Bank `NV.AGR.TOTL.ZS` | direct match |
| export concentration (≈90-category UN Comtrade HHI) | 4-category HHI (food, fuel, ores and metals, manufactures) from World Bank WDI | UN Comtrade's product-level detail is not part of this project's data source. A 4-category HHI has a practical floor of 0.25 rather than 0, but that floor is a constant shift and min-max normalisation removes it exactly - it does not affect the normalised values or the ranking. The real cost is resolution: two countries with genuinely different true diversification can land in the same broad category split and look identical here, where the 90-category version would distinguish them. Closing this gap needs finer trade data (UN Comtrade, free with registration), not a change to the normalisation step |
| remoteness (continuous, trade-weighted distance) | landlocked / not landlocked (binary) | the UN's distance measure needs bilateral trade-weighted data this project does not have; landlocked status is a real, well-documented geographic fact and a defensible coarse proxy |
| export instability | log-linear-detrended standard deviation of residuals, on `NE.EXP.GNFS.KD` | the UN CDP uses a centred-moving-average detrending method; log-linear is simpler to implement correctly and to audit, at the cost of not tracking short cyclical swings around a moving average as closely |
| agricultural production instability | same method, on `NV.AGR.TOTL.KD` (constant prices, to avoid mixing price and quantity effects) | as above |
| natural disaster component | **not included** | requires EM-DAT, which is a separate registration-gated data source outside this project's scope; it is renamed "economic instability" throughout the pipeline rather than left as a general-sounding "shock" sub-index it would not fully earn |

## Missing data

| item | decision | reason |
|---|---|---|
| exclusion rule | a country is dropped from the composite index if more than 40% of its five required inputs are missing | African country statistics genuinely have coverage gaps; the gaps are not random with respect to vulnerability (a fragile state is often also a state with weak statistical capacity), so silently dropping every country with any gap would bias the sample away from the most vulnerable cases |
| sub-index averaging | each sub-index is the mean of whichever of its components a country has, not a strict requirement for all of them | one missing component should not zero out an entire sub-index for an otherwise well-covered country |
| partial-index cases | a country whose entire exposure OR entire economic instability sub-index is missing (even if it clears the 40% overall threshold) is explicitly flagged, not silently averaged as if it were a real composite | such a country's "EVI" is actually just one sub-index under the composite's name; the report calls this out by name for every case, not as a footnote |
| threshold sensitivity | checked at 20/30/40/50/60% as a robustness step | shows how much the country list depends on exactly where this line was drawn |

## Index construction

| item | decision | reason |
|---|---|---|
| normalisation | min-max, computed within the Sub-Saharan Africa country set actually being compared | matches the UN CDP's own convention; means the index describes relative standing within this group, not an absolute world scale — stated explicitly rather than left ambiguous |
| aggregation | simple (unweighted) average, at both the sub-index and composite level | transparent, and does not let the analyst's own weighting preference quietly decide the ranking |
| alternative weighting | a PCA-weighted version built from all six normalised components together, reported as a comparison | shows how much the ranking would change under a data-driven weighting scheme instead of an assumed equal one; not treated as a replacement, since PCA weighting has its own hidden assumption (that the direction of greatest variance is the direction of greatest vulnerability) |

## Benchmark validation

| item | decision | reason |
|---|---|---|
| benchmark | the current UN list of Sub-Saharan African Least Developed Countries (UNCTAD, 2024/2025 review cycle) | a real, external, UN-published classification the index construction never saw — a genuine check rather than a comparison against numbers this project generated itself |
| test | Mann-Whitney U (LDC vs non-LDC reconstructed EVI), one-sided | no assumption of normally distributed scores, and modest sample sizes on both sides |
| interpretation | LDC status is treated as suggestive validation, not ground truth | LDC classification also depends on income and a Human Assets Index, which this project's EVI reconstruction does not include; a mismatch is not automatically an error in the index |
| income correlation | reported separately (Spearman rho against log GNI per capita) | checks whether the reconstructed EVI is adding anything beyond what income alone would already say |

## Things that stayed unresolved

* No disaster-impact data (EM-DAT) means the economic instability sub-index only captures
  economic instability, not physical exposure to floods, drought, or storms
  — a real gap for a region where climate shocks matter a great deal.
* Export concentration has less resolution than the official measure: two
  countries with genuinely different true diversification can land in the
  same broad category and score identically here, because of the
  4-category simplification described above.
* The reference-year fallback (closest year within 2 years) means not
  every country's cross-sectional values are from exactly the same year.
* Whether the reconstructed EVI is validated by the LDC comparison depends
  entirely on the actual numbers the pipeline produces when it is run
  against real data — this document records the method, not the result.
