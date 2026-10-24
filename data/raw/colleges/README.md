# MassGIS colleges and universities

Saved 2026-10-18 for Hackachusetts.

All 206 colleges and universities in the MassGIS HigherEd layer, updated from NCES as of the state's May 2026 edition. Street address and telephone are left out. Latitude and longitude are the campus point. The live call is the same layer as GeoJSON.

Rows in data.csv: 206

Columns: college, campus, city, zip, town, type, level, category, housing, latitude, longitude

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/HigherEd/MapServer/0/query?where=1%3D1&outFields=COLLEGE,CAMPUS,CITY,ZIPCODE,GEOG_TOWN,TYPE,NCES_TYPE,CATEGORY,CAMPUSHOUS&returnGeometry=true&outSR=4326&f=json

Check the source license before publishing a project.
