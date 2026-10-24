"""Save a fresh copy of this Hackachusetts starter source."""
import pathlib
import urllib.parse
import urllib.request

URL = "https://api.openalex.org/works?filter=authorships.institutions.id:I63966007%7CI136199984%7CI103531236%7CI111088046%7CI12912129%7CI24603500%7CI133738476%7CI33434090%7CI96062909,publication_year:2024&sort=cited_by_count:desc&per_page=25&select=display_name,publication_year,cited_by_count,type,primary_location"
request = urllib.request.Request(URL, headers={"User-Agent": "HackachusettsKit"})
with urllib.request.urlopen(request, timeout=90) as response:
    payload = response.read()
suffix = pathlib.Path(urllib.parse.urlparse(URL).path).suffix
path = pathlib.Path("fresh" + suffix) if suffix in {".csv", ".txt", ".json", ".jsonl", ".parquet"} else pathlib.Path("fresh.json")
path.write_bytes(payload)
print(f"wrote {path} ({len(payload)} bytes)")
