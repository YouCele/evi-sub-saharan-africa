# A reconstructed Economic Vulnerability Index for Sub-Saharan Africa

A portfolio project: rebuild the *structure* of the UN Committee for
Development Policy's Economic Vulnerability Index (EVI) — one of the three
criteria behind the UN's Least Developed Country classification — using
only free, public World Bank Open Data, and check whether the reconstruction
actually tracks the real UN classification it never saw during construction.

**This is a reconstruction, not the official index.** Several components are
approximated with coarser proxies where the real UN data sources (UN
Comtrade, EM-DAT) are outside this project's scope. Every substitution is
listed in `reports/research_decision_log.md`, with the reasoning, not
discovered later by a reader comparing numbers.

## Real results

This repository now contains a real, executed run — 48 Sub-Saharan African
economies pulled from actual World Bank data, 46 retained after the
missingness rule (Eritrea and Somalia excluded for insufficient coverage).

| | |
|---|---|
| Most vulnerable | Central African Republic (0.72), South Sudan (0.71), Sudan (0.50) |
| Least vulnerable | South Africa (0.12), Tanzania (0.19), Namibia (0.19) |
| UN LDC benchmark | LDCs score significantly higher than non-LDCs (Mann-Whitney p = 0.0022, rank-biserial effect size 0.51, n = 29 vs 17) |
| Correlation with income | Spearman rho = -0.47 against log GNI per capita — related to income, not a restatement of it |

Full numbers in `outputs/evi_scores.csv`, full write-up in
`reports/final_report.md`, ranking chart in `figures/01_evi_ranking.png`.

## Two ways to get the data in

**`scripts/run_01_fetch_data.py`** — calls the live World Bank API directly.
Works on any machine with a normal internet connection.

**`scripts/run_01b_load_bulk_csv.py`** — used for this repository's actual
run, because the environment it was built in could not make outbound API
calls. Download the 10 indicator files by hand from
`https://api.worldbank.org/v2/country/all/indicator/<CODE>?downloadformat=csv`
(the codes are in `src/config.py`'s `INDICATORS` list), unzip them into
`data/raw/wb_bulk/`, and run this script instead of script 1. It derives the
Sub-Saharan Africa country list from the real `Metadata_Country` file that
ships in every bulk download, not a hardcoded guess — same principle as the
live-API path, different data source. Both paths produce identical
`data/processed/` output, so scripts 2 through 6 run unmodified either way.

## What makes this more than "download some CSVs and average them"

- **The country list isn't hardcoded.** A couple of countries (Djibouti,
  Sudan) are classified inconsistently as "Sub-Saharan Africa" across
  different organisations. Instead of guessing, the code asks the World
  Bank's own country metadata endpoint at run time and uses whatever it
  says — the ambiguity is resolved by the data source, not by an assumption
  baked into `config.py`.
- **A real external benchmark.** The reconstructed index is tested against
  the current UN list of African Least Developed Countries — a
  classification this project's index construction never had access to —
  with a Mann-Whitney test, not eyeballed for plausibility.
- **Partial composites are flagged, not hidden.** A country can pass the
  overall missingness threshold while having its entire economic instability sub-index
  missing, in which case its "EVI" is really just the exposure score wearing
  the composite's name. The pipeline names these countries explicitly rather
  than quietly averaging over the gap.
- **Two weighting schemes, compared, not one weighting scheme presented as
  the answer.** The main index uses simple averaging, matching the UN's own
  convention; a PCA-weighted alternative is built separately and the two
  rankings are compared for how much they actually agree.
- **A jackknife sensitivity check** on every component, and a missingness-
  threshold sensitivity check, so the write-up can say which components the
  ranking actually depends on instead of asserting it's robust.

## An honest note on how this was built

The World Bank API needs a live internet connection to call, which this
project's own execution environment did not have. Rather than leave the
repository with empty output folders, the 10 indicator files were
downloaded by hand and loaded through `scripts/run_01b_load_bulk_csv.py`
(see above) — the results in `outputs/`, `figures/`, and
`reports/final_report.md` are real, not synthetic. `scripts/run_01_fetch_data.py`
remains the normal path for anyone running this on a machine with internet
access; both produce identical downstream data.

## Project structure

```
.
├── data/
│   ├── raw/            World Bank API cache, built by script 1 (gitignored)
│   └── processed/      intermediate cross-sectional tables (gitignored)
├── src/                the analysis code, one module per concern
├── scripts/            six numbered scripts plus run_all.py
├── notebooks/          three thin notebooks that run the scripts and display results
├── outputs/            every table the pipeline produces, as CSV or JSON
├── figures/            every plot, as PNG
├── reports/            research_decision_log.md (written) and
│                       final_report.md (generated by script 6)
└── requirements.txt
```

## Running it

```
pip install -r requirements.txt
python scripts/run_all.py
```

Only step 1 needs internet access; everything after it reads from the
cached files step 1 writes. See `HOW_TO_RUN.md` for the full breakdown and
what each output file contains.

## Data source

World Bank Open Data (<https://data.worldbank.org/>), fetched via the
public API — no key needed. UN LDC classification from UNCTAD
(<https://unctad.org/topic/least-developed-countries/list>).

## License

Code is MIT licensed (see `LICENSE`). World Bank data is CC-BY 4.0.
