# MBTA rapid transit stations

Saved 2026-10-18 for Hackachusetts.

Station, line, and route text. Map geometry is omitted.

Rows in data.csv: 170

Columns: station, line, route

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/MBTA_Rapid_Transit/MapServer/0/query?where=1%3D1&outFields=STATION,LINE,ROUTE&returnGeometry=false&f=json

Check the source license before publishing a project.
