# A reconstructed Economic Vulnerability Index for Sub-Saharan Africa

*Generated from the saved pipeline outputs by `scripts/run_06_report.py`. Every number below comes from `outputs/`; nothing here was typed in separately from the analysis.*

## 1. What this is, and what it is not

This project reconstructs the structure of the UN Committee for Development Policy's Economic Vulnerability Index (EVI) - one of the three criteria used to classify Least Developed Countries, alongside income and a Human Assets Index - using World Bank Open Data instead of the UN's own underlying sources. It is a reconstruction, not the official index: several components are approximated with coarser proxies where the original UN data source (UN Comtrade for export concentration, EM-DAT for disaster impact) was not part of this project's data. Every substitution is documented in `reports/research_decision_log.md`.

Scope: Sub-Saharan Africa, as the World Bank's own region classification currently defines it. 48 countries were assessed, 46 retained in the final composite index, 2 excluded for missing more than 40% of the required inputs.

## 2. Methodology

Two sub-indices, each the equal-weighted average of its available components (a country missing one component is not penalised twice by having the whole sub-index blank):

**Exposure** - population size, agriculture's share of GDP, export concentration (a four-category Herfindahl index over food, fuel, ores and metals, and manufactured exports), and landlocked status.

**Economic instability** - export revenue instability and agricultural production instability, both measured as the standard deviation of residuals from a log-linear trend over 2008-2023. This sub-index is named for what it actually measures: pure economic volatility, with no direct physical shock component (drought, flood, storm) in it at all - see the limitations below.

The composite EVI is the average of the two sub-indices. All components are min-max normalised across the countries in this study (not against a fixed global scale), so the index describes relative standing within this group of countries.

## 3. Missing data

| indicator                           |   n |   n_missing |   missing_pct |
|:------------------------------------|----:|------------:|--------------:|
| export_concentration                |  48 |           9 |        0.1875 |
| exports_constant_usd_instability    |  48 |           6 |        0.125  |
| agri_share_gdp                      |  48 |           3 |        0.0625 |
| agri_value_constant_usd_instability |  48 |           2 |        0.0417 |
| population                          |  48 |           0 |        0      |

Countries with the most missing inputs:

| country            |   n_missing |   n_required |   missing_share |
|:-------------------|------------:|-------------:|----------------:|
| Eritrea            |           4 |            5 |             0.8 |
| Somalia, Fed. Rep. |           3 |            5 |             0.6 |
| South Sudan        |           2 |            5 |             0.4 |
| Burundi            |           1 |            5 |             0.2 |
| Zambia             |           1 |            5 |             0.2 |
| Chad               |           1 |            5 |             0.2 |
| Nigeria            |           1 |            5 |             0.2 |
| Malawi             |           1 |            5 |             0.2 |
| Liberia            |           1 |            5 |             0.2 |
| Equatorial Guinea  |           1 |            5 |             0.2 |

2 countries were excluded from the composite index: Eritrea, Somalia, Fed. Rep..

## 4. Results

Most vulnerable, by the reconstructed EVI:

| country                  |   evi |   exposure_index |   econ_instability_index | is_ldc   |
|:-------------------------|------:|-----------------:|-------------------------:|:---------|
| Central African Republic | 0.722 |            0.837 |                    0.607 | True     |
| South Sudan              | 0.709 |            0.976 |                    0.443 | True     |
| Sudan                    | 0.503 |            0.467 |                    0.538 | True     |
| Chad                     | 0.488 |            0.921 |                    0.055 | True     |
| Burundi                  | 0.445 |            0.822 |                    0.068 | True     |
| Malawi                   | 0.429 |            0.818 |                    0.04  | True     |
| Lesotho                  | 0.416 |            0.694 |                    0.138 | True     |
| Liberia                  | 0.409 |            0.527 |                    0.29  | True     |
| Gambia, The              | 0.408 |            0.572 |                    0.245 | True     |
| Ethiopia                 | 0.407 |            0.778 |                    0.035 | True     |

Least vulnerable:

| country      |   evi |   exposure_index |   econ_instability_index | is_ldc   |
|:-------------|------:|-----------------:|-------------------------:|:---------|
| Togo         | 0.216 |            0.38  |                    0.052 | True     |
| Madagascar   | 0.214 |            0.357 |                    0.072 | True     |
| Mozambique   | 0.213 |            0.397 |                    0.029 | True     |
| Kenya        | 0.208 |            0.367 |                    0.048 | False    |
| Senegal      | 0.2   |            0.323 |                    0.077 | True     |
| Nigeria      | 0.199 |            0.371 |                    0.026 | False    |
| Mauritius    | 0.194 |            0.33  |                    0.058 | False    |
| Namibia      | 0.194 |            0.303 |                    0.085 | False    |
| Tanzania     | 0.19  |            0.361 |                    0.02  | True     |
| South Africa | 0.124 |            0.195 |                    0.053 | False    |

## 5. Benchmark validation against the UN LDC list

UN-classified LDCs have a median reconstructed EVI of 0.366, against 0.230 for non-LDCs (Mann-Whitney p = 0.0022, rank-biserial effect size 0.509, n = 29 LDCs and 17 non-LDCs). 
This difference is unlikely to be chance, which is a reasonable sanity check that the reconstruction is measuring something real.

Cases worth looking at individually - non-LDCs the index scores as surprisingly vulnerable:

| country               |   evi |   exposure_index |   econ_instability_index |
|:----------------------|------:|-----------------:|-------------------------:|
| São Tomé and Principe | 0.402 |            0.577 |                    0.226 |
| Botswana              | 0.4   |            0.709 |                    0.091 |
| Zimbabwe              | 0.399 |            0.63  |                    0.167 |
| Eswatini              | 0.356 |            0.632 |                    0.08  |
| Cabo Verde            | 0.322 |            0.465 |                    0.18  |
| Seychelles            | 0.302 |            0.46  |                    0.144 |
| Congo, Rep.           | 0.267 |            0.486 |                    0.049 |
| Gabon                 | 0.248 |            0.377 |                    0.119 |

LDCs the index scores as surprisingly low:

| country          |   evi |   exposure_index |   econ_instability_index |
|:-----------------|------:|-----------------:|-------------------------:|
| Benin            | 0.298 |            0.537 |                    0.059 |
| Congo, Dem. Rep. | 0.281 |            0.351 |                    0.211 |
| Mauritania       | 0.243 |            0.445 |                    0.041 |
| Togo             | 0.216 |            0.38  |                    0.052 |
| Madagascar       | 0.214 |            0.357 |                    0.072 |
| Mozambique       | 0.213 |            0.397 |                    0.029 |
| Senegal          | 0.2   |            0.323 |                    0.077 |
| Tanzania         | 0.19  |            0.361 |                    0.02  |

Correlation with log GNI per capita: Spearman rho = -0.472 (p = 0.0011). The index tracks income to some degree, as expected, without simply reproducing it.

## 6. Robustness

Removing each component in turn and checking how much the ranking moves (1.0 = no change, lower = the ranking depends heavily on that component):

| component_removed         | sub_index            |   spearman_rho_vs_full |
|:--------------------------|:---------------------|-----------------------:|
| landlocked_norm           | exposure             |                  0.82  |
| export_concentration_norm | exposure             |                  0.903 |
| export_instability_norm   | economic_instability |                  0.91  |
| agri_share_gdp_norm       | exposure             |                  0.911 |
| agri_instability_norm     | economic_instability |                  0.915 |
| population_norm           | exposure             |                  0.943 |

Countries whose rank changes most between the equal-weight index and the PCA-weighted alternative:

| iso3   | country     |   evi_rank |   pca_rank |   rank_change |
|:-------|:------------|-----------:|-----------:|--------------:|
| MUS    | Mauritius   |         43 |         17 |            26 |
| NAM    | Namibia     |         44 |         22 |            22 |
| CPV    | Cabo Verde  |         25 |          4 |            21 |
| COG    | Congo, Rep. |         30 |         10 |            20 |
| GAB    | Gabon       |         31 |         11 |            20 |
| SYC    | Seychelles  |         27 |          7 |            20 |
| ETH    | Ethiopia    |         10 |         29 |            19 |
| AGO    | Angola      |         26 |          9 |            17 |

How many countries the index would cover under different missingness thresholds:

|   threshold |   n_kept |   n_excluded |
|------------:|---------:|-------------:|
|         0.2 |       45 |            3 |
|         0.3 |       45 |            3 |
|         0.4 |       46 |            2 |
|         0.5 |       46 |            2 |
|         0.6 |       47 |            1 |

## 7. Limitations

- Export concentration is approximated from four broad World Bank categories, not the roughly 90-category UN Comtrade breakdown the official EVI uses. This does not distort the normalised scores or the ranking (a coarser measure still normalises correctly) - the real cost is resolution: two countries with genuinely different true diversification can land in the same broad category split and come out looking identical here, where the finer breakdown would tell them apart. Fixing this needs UN Comtrade data, not a change to the normalisation step.
- Remoteness is approximated with a landlocked/not-landlocked flag, not the UN's continuous, trade-weighted distance measure. The jackknife check in section 6 shows this is the single component the ranking depends on most, which makes it the clearest concrete target for improvement.
- The economic instability sub-index has no disaster-impact component (EM-DAT data was not part of this project), so a country's physical exposure to floods, drought or storms is not directly represented anywhere in this index - only economic volatility is. The sub-index is named for what it actually measures, rather than called a general 'shock' index it would not fully earn.
- LDC status is not a direct label for the true EVI - it depends on income and human assets too - so agreement or disagreement with LDC status is suggestive, not a precise accuracy check.
- All normalisation is relative to the Sub-Saharan African countries in this study; the scores are not comparable to a global ranking.

## 8. Conclusion

Out of 48 Sub-Saharan African economies assessed, 46 have a composite score after excluding 2 for missing data (Eritrea, Somalia, Fed. Rep.).

The ranking itself passes a basic sanity check before any formal validation: Central African Republic (0.72), South Sudan (0.71) and Sudan (0.50) sit at the top - three states widely described elsewhere as fragile - while South Africa (0.12), the region's largest and most diversified economy, sits at the very bottom.

The formal benchmark backs this up: UN-classified LDCs score significantly higher on the reconstructed EVI than non-LDCs (p = 0.0022). That is not guaranteed to happen just because an index has vaguely sensible-looking components - it is a real check the reconstruction could have failed, and did not.

The more interesting cases are the disagreements. São Tomé and Principe and Botswana score as vulnerable as many LDCs despite not being classified as one - both are small, trade-exposed economies where a narrow export base and limited economic size outweigh a comparatively higher income, which is exactly the kind of case the EVI is supposed to catch separately from income. In the other direction, Tanzania is a UN-classified LDC that scores among the least vulnerable in this reconstruction - a reasonable next question, not addressed by this data, is whether that reflects real structural resilience or a component this reconstruction is simply not capturing well.

Income explains part of the picture (rho = -0.47 against log GNI per capita) but far from all of it, which is the result you would want to see - an index that is supposed to measure something beyond income should not correlate with income at 0.9 or above.

The jackknife check has a clear practical implication: removing landlocked moves the ranking more than removing any other single component (correlation with the full index drops to 0.82). Landlocked status is a crude, binary stand-in for the UN's continuous remoteness measure, and it is doing more work in this reconstruction than a single binary flag probably should - the clearest concrete target for improving this project, ahead of chasing the export-concentration or disaster-data gaps described above.
