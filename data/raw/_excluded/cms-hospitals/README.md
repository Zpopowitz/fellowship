# CMS hospital ratings, Massachusetts

Saved 2026-10-18 for Hackachusetts.

CMS Hospital General Information for Massachusetts. Street address and telephone are left out. The live call returns the full CMS row, including address.

Rows in data.csv: 84

Columns: facility_id, facility_name, city, county, hospital_type, ownership, emergency, overall_rating

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0?limit=100&conditions[0][property]=state&conditions[0][value]=MA&conditions[0][operator]==

Check the source license before publishing a project.
