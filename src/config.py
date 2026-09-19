"""
Central configuration for the Sub-Saharan Africa Economic Vulnerability Index
(EVI) project.

Design choice worth stating up front: the list of Sub-Saharan African
countries is NOT hardcoded here. It is derived at run time from the World
Bank's own country metadata endpoint, filtered on region.id == "SSF". A
couple of countries (Djibouti, Sudan) are geographically and politically
ambiguous between "Sub-Saharan Africa" and "Middle East & North Africa" in
different classification systems, and hardcoding a guess would be exactly
the kind of unstated assumption this project tries to avoid. Instead the
code asks the data source what it thinks, and records the answer.

What IS hardcoded here, and why, are the two things the World Bank country
API does not carry: which countries are UN-classified Least Developed
Countries (a UN designation, not a World Bank one) and which are landlocked
(a fixed geographic fact, not something an API needs to serve). Both lists
are static reference data with a citation, in the same spirit as the
plausibility ranges and label mappings in the NHANES project's config.py.
"""

from __future__ import annotations

import os
from pathlib import Path

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = Path(os.environ.get("EVI_RAW", PROJECT_ROOT / "data" / "raw"))
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURE_DIR = PROJECT_ROOT / "figures"
REPORT_DIR = PROJECT_ROOT / "reports"

for _d in (RAW_DIR, PROCESSED_DIR, OUTPUT_DIR, FIGURE_DIR, REPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Reproducibility and study window
# ----------------------------------------------------------------------

RANDOM_SEED = 2026

# World Bank data for African countries gets noticeably sparser before the
# mid-2000s. 16 years is long enough to compute a meaningful instability
# measure and recent enough that most countries have real coverage.
START_YEAR = 2008
END_YEAR = 2023
REFERENCE_YEAR = 2022          # the single most-recent-with-good-coverage
                                # year used for the cross-sectional index
DATE_RANGE = f"{START_YEAR}:{END_YEAR}"

WB_BASE = "https://api.worldbank.org/v2"
WB_REGION_SSF = "SSF"          # World Bank's own code for Sub-Saharan Africa

# ----------------------------------------------------------------------
# Indicator registry
# ----------------------------------------------------------------------
# role:
#   "exposure"  - structural exposure sub-index component
#   "economic_instability"     - instability sub-index component (needs the full time series)
#   "context"   - not part of the index; used for validation and the write-up
#   "derived"   - built from other indicators, not fetched directly

INDICATORS: list[dict] = [
    dict(code="SP.POP.TOTL", name="population", role="exposure",
         meaning="Population, total",
         direction="lower_is_worse",
         note="small economies are structurally more exposed to shocks"),
    dict(code="NV.AGR.TOTL.ZS", name="agri_share_gdp", role="exposure",
         meaning="Agriculture, forestry, and fishing, value added (% of GDP)",
         direction="higher_is_worse",
         note="a heavier reliance on agriculture means more exposure to "
              "weather and commodity-price shocks"),
    dict(code="TX.VAL.FOOD.ZS.UN", name="export_share_food", role="derived_input",
         meaning="Food exports (% of merchandise exports)"),
    dict(code="TX.VAL.FUEL.ZS.UN", name="export_share_fuel", role="derived_input",
         meaning="Fuel exports (% of merchandise exports)"),
    dict(code="TX.VAL.MMTL.ZS.UN", name="export_share_ores_metals", role="derived_input",
         meaning="Ores and metals exports (% of merchandise exports)"),
    dict(code="TX.VAL.MANF.ZS.UN", name="export_share_manuf", role="derived_input",
         meaning="Manufactures exports (% of merchandise exports)"),
    dict(code="NE.EXP.GNFS.KD", name="exports_constant_usd", role="econ_instability_input",
         meaning="Exports of goods and services (constant 2015 US$)",
         note="time series used to compute export revenue instability"),
    dict(code="NV.AGR.TOTL.KD", name="agri_value_constant_usd", role="econ_instability_input",
         meaning="Agriculture, forestry, and fishing, value added (constant 2015 US$)",
         note="time series used to compute agricultural production instability"),
    dict(code="NY.GDP.PCAP.CD", name="gdp_per_capita", role="context",
         meaning="GDP per capita (current US$)"),
    dict(code="NY.GNP.PCAP.CD", name="gni_per_capita_atlas", role="context",
         meaning="GNI per capita, Atlas method (current US$)",
         note="one of the three official UN LDC criteria, alongside the Human "
              "Assets Index and the EVI itself; included so the write-up does "
              "not confuse EVI with the full LDC classification"),
]

FETCHED_CODES = [i["code"] for i in INDICATORS if i["role"] != "derived"]


def indicator_meta(name: str) -> dict:
    for i in INDICATORS:
        if i["name"] == name:
            return i
    raise KeyError(name)


# ----------------------------------------------------------------------
# Export concentration (derived indicator)
# ----------------------------------------------------------------------
# The UN CDP's own export concentration measure is a Herfindahl-Hirschman
# index computed over roughly 90 product categories from UN Comtrade, which
# needs a data source this project does not use. The four broad categories
# below (food, fuel, ores and metals, manufactures) are standard World Bank
# WDI series that between them cover most of merchandise exports. Squaring
# and summing their shares gives a real, calculable HHI - a coarser version
# of the same idea, not an equivalent one. This simplification is written
# down here, not discovered by the reader from a mismatch later.

EXPORT_SHARE_COLUMNS = ["export_share_food", "export_share_fuel",
                        "export_share_ores_metals", "export_share_manuf"]

# ----------------------------------------------------------------------
# UN Least Developed Countries list (African members)
# ----------------------------------------------------------------------
# Source: UNCTAD, current LDC list as of the 2024/2025 review cycle
# (https://unctad.org/topic/least-developed-countries/list). This is UN
# reference data, not World Bank data, and not something the World Bank
# country API carries - hence hardcoded, with this citation, rather than
# fetched. If the list changes at a future review, update it here; the rest
# of the pipeline reads from this single place.

LDC_ISO3: set[str] = {
    "AGO", "BEN", "BFA", "BDI", "CAF", "TCD", "COM", "COD", "DJI", "ERI",
    "ETH", "GMB", "GIN", "GNB", "LSO", "LBR", "MDG", "MWI", "MLI", "MRT",
    "MOZ", "NER", "RWA", "SEN", "SLE", "SOM", "SSD", "SDN", "TGO", "UGA",
    "TZA", "ZMB",
}

# ----------------------------------------------------------------------
# Landlocked African countries
# ----------------------------------------------------------------------
# Source: UN-OHRLLS list of landlocked developing countries, African
# members. This is a fixed geographic fact, included as a simple proxy for
# the UN CDP's remoteness component, which is otherwise a continuous,
# trade-weighted distance measure this project does not attempt to
# reconstruct.

LANDLOCKED_ISO3: set[str] = {
    "BWA", "BFA", "BDI", "CAF", "TCD", "SWZ", "ETH", "LSO", "MWI", "MLI",
    "NER", "RWA", "SSD", "UGA", "ZMB", "ZWE",
}

# ----------------------------------------------------------------------
# Index construction
# ----------------------------------------------------------------------

EXPOSURE_COMPONENTS = ["population_inv_norm", "agri_share_gdp_norm",
                       "export_concentration_norm", "landlocked"]
ECON_INSTABILITY_COMPONENTS = ["export_instability_norm", "agri_instability_norm"]

# Minimum number of years of non-missing data required inside the study
# window for a country's instability measure to be computed at all. Fewer
# than this and the coefficient of variation is not meaningful.
MIN_YEARS_FOR_INSTABILITY = 8

# A country missing more than this share of the exposure or economic instability inputs is
# excluded from the composite index rather than imputed - see
# reports/research_decision_log.md for the reasoning.
MAX_MISSING_SHARE = 0.40
