"""Save a fresh copy of this Hackachusetts starter source."""
import pathlib
import urllib.parse
import urllib.request

URL = "https://data.boston.gov/api/3/action/datastore_search_sql?sql=SELECT%20name%2Cyear%2Carealand_sqmi%2Cpopulation_b01001_001e%2Ceducation_b15003_hsgrad_and_ged%2Ceducation_b15003_022e%2Ceducation_b15003_gradprofdegree%2Cincome_b17001_001e%2Cincome_b17001_002e%20FROM%20%22b0543358-d03f-4682-bf0c-658ea4573d6f%22"
request = urllib.request.Request(URL, headers={"User-Agent": "HackachusettsKit"})
with urllib.request.urlopen(request, timeout=90) as response:
    payload = response.read()
suffix = pathlib.Path(urllib.parse.urlparse(URL).path).suffix
path = pathlib.Path("fresh" + suffix) if suffix in {".csv", ".txt", ".json"} else pathlib.Path("fresh.json")
path.write_bytes(payload)
print(f"wrote {path} ({len(payload)} bytes)")
