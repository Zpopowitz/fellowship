# OpenAlex works at the nine campuses, 2024

Saved 2026-10-18 for Hackachusetts.

The 500 most-cited works published in 2024 with an author at MIT, Harvard, Boston College, Boston University, Northeastern, UMass Amherst, UMass Lowell, UMass Boston, or Babson. OpenAlex reports 73,349 works for that filter. The live call returns the first 25. data.csv is the top 500.

Rows in data.csv: 500

Columns: title, year, type, cited_by, source

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://api.openalex.org/works?filter=authorships.institutions.id:I63966007%7CI136199984%7CI103531236%7CI111088046%7CI12912129%7CI24603500%7CI133738476%7CI33434090%7CI96062909,publication_year:2024&sort=cited_by_count:desc&per_page=25&select=display_name,publication_year,cited_by_count,type,primary_location

Check the source license before publishing a project.
