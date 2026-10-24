"""Save a fresh copy of this Hackachusetts starter source."""
import pathlib
import urllib.parse
import urllib.request

URL = "https://data.boston.gov/api/3/action/datastore_search_sql?sql=SELECT%20case_no%2Cstatus_dttm%2Cstatus%2Ccode%2Cvalue%2Cdescription%2Cviolation_city%2Cviolation_zip%2Cward%20FROM%20%22800a2663-1d6a-46e7-9356-bedb70f5332c%22%20WHERE%20status_dttm%20%3E%3D%20%272024-01-01%27%20ORDER%20BY%20status_dttm%20DESC%20LIMIT%20100"
request = urllib.request.Request(URL, headers={"User-Agent": "HackachusettsKit"})
with urllib.request.urlopen(request, timeout=90) as response:
    payload = response.read()
suffix = pathlib.Path(urllib.parse.urlparse(URL).path).suffix
path = pathlib.Path("fresh" + suffix) if suffix in {".csv", ".txt", ".json"} else pathlib.Path("fresh.json")
path.write_bytes(payload)
print(f"wrote {path} ({len(payload)} bytes)")
