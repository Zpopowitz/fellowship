# CDC PLACES, Massachusetts counties

Saved 2026-10-18 for Hackachusetts.

CDC PLACES 2023 county estimates for Massachusetts. Crude prevalence from BRFSS for five adult measures. County name only; coordinates are left out.

Rows in data.csv: 70

Columns: year, county, measure, prevalence, low, high, population

How to use it

- Spreadsheets: open data.csv in Excel or Google Sheets.
- Fresh copy: run `python fetch.py` or `node fetch.js`. Both call the URL below and save the response.
- The preview on the Hackachusetts site is a few rows of this same table.

Direct request

https://data.cdc.gov/resource/swc5-untb.json?$select=year,locationname,measure,data_value,low_confidence_limit,high_confidence_limit,totalpopulation&$where=stateabbr%3D%27MA%27%20AND%20measure%20in(%27Obesity%20among%20adults%27,%27Diagnosed%20diabetes%20among%20adults%27,%27Visits%20to%20doctor%20for%20routine%20checkup%20within%20the%20past%20year%20among%20adults%27,%27Frequent%20mental%20distress%20among%20adults%27,%27Current%20cigarette%20smoking%20among%20adults%27)%20AND%20data_value_type%3D%27Crude%20prevalence%27&$limit=500

Check the source license before publishing a project.
