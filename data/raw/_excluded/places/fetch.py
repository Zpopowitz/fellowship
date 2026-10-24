"""Save a fresh copy of this Hackachusetts starter source."""
import pathlib
import urllib.parse
import urllib.request

URL = "https://data.cdc.gov/resource/swc5-untb.json?$select=year,locationname,measure,data_value,low_confidence_limit,high_confidence_limit,totalpopulation&$where=stateabbr%3D%27MA%27%20AND%20measure%20in(%27Obesity%20among%20adults%27,%27Diagnosed%20diabetes%20among%20adults%27,%27Visits%20to%20doctor%20for%20routine%20checkup%20within%20the%20past%20year%20among%20adults%27,%27Frequent%20mental%20distress%20among%20adults%27,%27Current%20cigarette%20smoking%20among%20adults%27)%20AND%20data_value_type%3D%27Crude%20prevalence%27&$limit=500"
request = urllib.request.Request(URL, headers={"User-Agent": "HackachusettsKit"})
with urllib.request.urlopen(request, timeout=90) as response:
    payload = response.read()
suffix = pathlib.Path(urllib.parse.urlparse(URL).path).suffix
path = pathlib.Path("fresh" + suffix) if suffix in {".csv", ".txt", ".json"} else pathlib.Path("fresh.json")
path.write_bytes(payload)
print(f"wrote {path} ({len(payload)} bytes)")
