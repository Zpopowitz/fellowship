# MBTA subway routes

Saved 2026-10-18 for Hackachusetts.

Subway and light-rail routes only. Bus routes are a separate MBTA query.

Rows in data.csv: 8

Columns: id, name, mode, fare_class

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://api-v3.mbta.com/routes?filter%5Btype%5D=0,1

Check the source license before publishing a project.
