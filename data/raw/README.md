# Raw data

This folder is where `scripts/run_01_fetch_data.py` caches what it pulls
from the World Bank Open Data API (https://api.worldbank.org/v2/) — the
country registry and one CSV per indicator. Nothing needs to be manually
downloaded first; the script fetches everything itself.

The API is fully public: no key, no registration, no rate limit that a
single run of this pipeline will come close to hitting.

World Bank data is released under CC-BY 4.0, so there is no restriction on
redistributing the cached CSVs either — they are left out of version
control here purely to keep the repository small and because they are
trivially reproducible by re-running the script, not because of any usage
restriction (unlike, say, restricted-access microdata).

If you want to skip re-fetching on a second machine, just copy this
folder's contents over; `data_loading.py` will use the cache instead of
calling the API again.
