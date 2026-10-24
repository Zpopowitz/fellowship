# Boston neighborhood estimates, 2025

Saved 2026-10-18 for Hackachusetts.

City of Boston 2025 neighborhood estimates. population is ACS B01001_001E, hs_or_ged is B15003 high school or GED, bachelors is B15003_022E, graduate_degree is the city's graduate-or-professional field, poverty_count and poverty_universe are B17001. These are the city's published estimates, not a new Census tabulation.

Rows in data.csv: 24

Columns: neighborhood, year, land_sqmi, population, hs_or_ged, bachelors, graduate_degree, poverty_universe, poverty_count

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://data.boston.gov/api/3/action/datastore_search_sql?sql=SELECT%20name%2Cyear%2Carealand_sqmi%2Cpopulation_b01001_001e%2Ceducation_b15003_hsgrad_and_ged%2Ceducation_b15003_022e%2Ceducation_b15003_gradprofdegree%2Cincome_b17001_001e%2Cincome_b17001_002e%20FROM%20%22b0543358-d03f-4682-bf0c-658ea4573d6f%22

Check the source license before publishing a project.
