# Cambridge Fresh Pond usership

Saved 2026-10-18 for Hackachusetts.

Hourly Fresh Pond Reservation usership from 2024 onward. Entrance counts use the city's sensor names: Black's Nook, Community Garden, Little Fresh Pond, Lusitania, and Pro Shop. The live call returns the 100 latest hours. data.csv is the saved window.

Rows in data.csv: 8784

Columns: when, season, month, hour, average_users, blacks_nook, community_garden, little_fresh_pond, lusitania, pro_shop

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://data.cambridgema.gov/resource/6xy8-cstb.json?$select=datetime,season,month,hour,fp_avg_hrly_use,bn,cg,lfp,lus,pro_shop&$where=year%20%3E=%20%272024%27&$order=datetime%20DESC&$limit=100

Check the source license before publishing a project.
