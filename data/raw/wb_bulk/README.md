# Manually downloaded World Bank bulk CSVs

These are the 10 indicator files downloaded by hand from
https://api.worldbank.org/v2/country/all/indicator/<CODE>?downloadformat=csv
(one per indicator in src/config.py's INDICATORS list), unzipped here, and
loaded by scripts/run_01b_load_bulk_csv.py.

This is an alternative to scripts/run_01_fetch_data.py (the live API
version) for use in an environment that cannot make outbound API calls
itself. Both paths produce identical data/processed/ output.
