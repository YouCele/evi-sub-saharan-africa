"""
World Bank Open Data API client.

No API key is needed; this is a fully public API. Two things this module
does deliberately, both learned from testing the API directly while building
this project:

1. format=json must be requested explicitly - the default response is XML.
2. The API paginates. A single call returns a `page`/`pages` header
   alongside the data; a naive single fetch silently truncates anything
   past the first page instead of raising an error, so every fetch here
   loops until it has collected every page.

Everything fetched is cached to data/raw/ as CSV. Re-running the pipeline
does not re-hit the API unless the cache is deleted or refresh=True is
passed - useful given how many indicator series this project needs, and
considerate of a public, rate-limited service.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

from . import config
from .utils import fail, note, step

BASE = config.WB_BASE
TIMEOUT = 30
PAUSE_BETWEEN_CALLS = 0.3   # seconds; polite spacing, not required by the API


def _get_all_pages(url: str, params: dict) -> list[dict]:
    """Fetch every page of a World Bank endpoint and return the combined data."""
    params = dict(params)
    params.setdefault("format", "json")
    params.setdefault("per_page", 1000)

    all_rows: list[dict] = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()

        if not isinstance(payload, list) or len(payload) < 2:
            # the API returns an error object (not the usual [header, data]
            # pair) when a parameter is invalid or the query matches nothing
            fail(f"unexpected response from {resp.url}: {payload}")

        header, data = payload[0], payload[1]
        if data is None:
            break
        all_rows.extend(data)

        total_pages = header.get("pages", 1)
        if page >= total_pages:
            break
        page += 1
        time.sleep(PAUSE_BETWEEN_CALLS)

    return all_rows


def fetch_country_registry(refresh: bool = False) -> pd.DataFrame:
    """
    Every economy the World Bank tracks, with its region classification.

    The Sub-Saharan Africa membership used throughout this project comes
    from filtering this table on region_id == "SSF" - not from a hardcoded
    list - so edge cases (Djibouti, Sudan, whichever way the API currently
    classifies them) are resolved by the data source, not by an assumption
    baked into this code.
    """
    cache = config.RAW_DIR / "country_registry.csv"
    if cache.exists() and not refresh:
        note(f"using cached {cache.name}")
        return pd.read_csv(cache)

    step("fetching the World Bank country registry")
    rows = _get_all_pages(f"{BASE}/country", {})
    records = []
    for r in rows:
        records.append(dict(
            iso3=r["id"],
            iso2=r.get("iso2Code"),
            name=r["name"],
            region_id=r["region"]["id"],
            region_value=r["region"]["value"],
            income_level=r.get("incomeLevel", {}).get("value"),
            capital_city=r.get("capitalCity"),
            longitude=r.get("longitude"),
            latitude=r.get("latitude"),
        ))
    df = pd.DataFrame(records)
    # aggregate entries (regions, income groups, the world) carry region_id "NA"
    df = df[df["region_id"] != "NA"].reset_index(drop=True)
    df.to_csv(cache, index=False)
    note(f"{len(df)} real economies found, saved to {cache.relative_to(config.PROJECT_ROOT)}")
    return df


def ssf_country_list(refresh: bool = False) -> pd.DataFrame:
    """Sub-Saharan Africa members, as the World Bank currently classifies them."""
    reg = fetch_country_registry(refresh=refresh)
    ssf = reg[reg["region_id"] == config.WB_REGION_SSF].reset_index(drop=True)
    if len(ssf) < 40:
        note(f"warning: only {len(ssf)} SSF countries found - check the API "
             "response, this looks low")
    return ssf


def _chunk(items: list[str], size: int = 20) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def fetch_indicator(indicator_code: str, iso3_codes: list[str],
                    date_range: str | None = None,
                    refresh: bool = False) -> pd.DataFrame:
    """
    One indicator's full time series for a list of countries.

    Country codes are sent in batches (World Bank's own examples use
    semicolon-joined lists; batching keeps individual request URLs modest
    in size and makes a single bad country code easier to isolate).
    """
    date_range = date_range or config.DATE_RANGE
    safe_name = indicator_code.replace(".", "_")
    cache = config.RAW_DIR / f"indicator_{safe_name}.csv"
    if cache.exists() and not refresh:
        note(f"using cached {cache.name}")
        return pd.read_csv(cache)

    step(f"fetching {indicator_code} for {len(iso3_codes)} countries, {date_range}")
    all_rows = []
    for batch in _chunk(iso3_codes):
        url = f"{BASE}/country/{';'.join(batch)}/indicator/{indicator_code}"
        rows = _get_all_pages(url, {"date": date_range})
        all_rows.extend(rows)
        time.sleep(PAUSE_BETWEEN_CALLS)

    records = [dict(iso3=r["countryiso3code"], country=r["country"]["value"],
                    year=int(r["date"]), value=r["value"])
              for r in all_rows if r.get("countryiso3code")]
    df = pd.DataFrame(records).sort_values(["iso3", "year"]).reset_index(drop=True)
    df.to_csv(cache, index=False)
    n_missing = df["value"].isna().mean()
    note(f"{len(df)} country-year rows, {100*n_missing:.1f}% missing, "
         f"saved to {cache.relative_to(config.PROJECT_ROOT)}")
    return df


def fetch_all_indicators(iso3_codes: list[str], refresh: bool = False) -> dict[str, pd.DataFrame]:
    """Fetch every indicator in the registry, one call per indicator."""
    out = {}
    for meta in config.INDICATORS:
        out[meta["name"]] = fetch_indicator(meta["code"], iso3_codes, refresh=refresh)
    return out
