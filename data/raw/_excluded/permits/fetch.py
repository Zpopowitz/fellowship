"""Save a fresh copy of this Hackachusetts starter source."""
import pathlib
import urllib.parse
import urllib.request

URL = "https://data.boston.gov/api/3/action/datastore_search_sql?sql=SELECT%20permitnumber%2Cworktype%2Cpermittypedescr%2Cdescription%2Cdeclared_valuation%2Ctotal_fees%2Cissued_date%2Cexpiration_date%2Cstatus%2Coccupancytype%2Csq_feet%2Czip%2Cward%20FROM%20%226ddcd912-32a0-43df-9908-63574f8c7e77%22%20WHERE%20issued_date%20%3E%3D%20%272024-01-01%27%20ORDER%20BY%20issued_date%20DESC%20LIMIT%20100"
request = urllib.request.Request(URL, headers={"User-Agent": "HackachusettsKit"})
with urllib.request.urlopen(request, timeout=90) as response:
    payload = response.read()
suffix = pathlib.Path(urllib.parse.urlparse(URL).path).suffix
path = pathlib.Path("fresh" + suffix) if suffix in {".csv", ".txt", ".json"} else pathlib.Path("fresh.json")
path.write_bytes(payload)
print(f"wrote {path} ({len(payload)} bytes)")
