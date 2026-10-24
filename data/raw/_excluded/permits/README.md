# Boston approved building permits

Saved 2026-10-18 for Hackachusetts.

Approved Boston permits issued on or after 1 Jan 2024. Street address, coordinates, applicant, and comments are left out. The live call returns 100 rows. data.csv has the full saved slice.

Rows in data.csv: 8240

Columns: permitnumber, worktype, permittypedescr, description, declared_valuation, total_fees, issued_date, expiration_date, status, occupancytype, sq_feet, zip, ward

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://data.boston.gov/api/3/action/datastore_search_sql?sql=SELECT%20permitnumber%2Cworktype%2Cpermittypedescr%2Cdescription%2Cdeclared_valuation%2Ctotal_fees%2Cissued_date%2Cexpiration_date%2Cstatus%2Coccupancytype%2Csq_feet%2Czip%2Cward%20FROM%20%226ddcd912-32a0-43df-9908-63574f8c7e77%22%20WHERE%20issued_date%20%3E%3D%20%272024-01-01%27%20ORDER%20BY%20issued_date%20DESC%20LIMIT%20100

Check the source license before publishing a project.
