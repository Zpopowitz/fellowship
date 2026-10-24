# OpenFEMA disaster declarations, Massachusetts

Saved 2026-10-18 for Hackachusetts.

Massachusetts declarations only. The live call returns the 100 most recent rows.

Rows in data.csv: 415

Columns: declarationDate, disasterNumber, incidentType, declarationTitle, designatedArea, declarationType

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$filter=state%20eq%20%27MA%27&$top=100&$select=disasterNumber,declarationTitle,declarationDate,incidentType,designatedArea,declarationType&$orderby=declarationDate%20desc

Check the source license before publishing a project.
