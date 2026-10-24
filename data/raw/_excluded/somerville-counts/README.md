# Somerville bicycle and pedestrian counts

Saved 2026-10-18 for Hackachusetts.

Somerville bicycle and pedestrian counts at named locations. The live call returns 100 rows. data.csv is the full saved table.

Rows in data.csv: 2532

Columns: year, location, latitude, longitude, period, mode, count

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://data.somervillema.gov/resource/qu9x-4xq5.json?$select=year,location_name,latitude,longitude,am_pm,mode,count&$order=year%20DESC&$limit=100

Check the source license before publishing a project.
