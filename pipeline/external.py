"""Fetch and cache the outside data the kits leave out (mostly coordinates).

Everything lands in data/raw/_external/ and is only downloaded when missing,
so a rebuild works offline. ``python pipeline/build.py --refresh-external``
forces a fresh copy.

Sources:
  - MBTA v3 API: stops per route, canonical route shapes
  - City of Boston ArcGIS: ZIP code polygons (Planning/OpenData layer 1)
  - MassGIS: hospital points
  - FHWA National Bridge Inventory 2022, Massachusetts (has lat/long)
  - NOAA CO-OPS: station 8443970 metadata, datums, flood levels
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from pipeline.common import EXTERNAL

TIMEOUT = 120
MBTA = "https://api-v3.mbta.com"
MBTA_DELAY = 3.2  # keyless MBTA API allows ~20 requests/minute

session = requests.Session()
session.headers.update({"User-Agent": "hackachusetts-student-project/1.0"})


def _get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    for attempt in range(4):
        r = session.get(url, params=params, timeout=TIMEOUT)
        if r.status_code == 429:  # rate limited: back off and retry
            time.sleep(15 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return r.json()


def _cached_json(path: Path, refresh: bool, fetch: Any) -> Any:
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    data = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def mbta_route_stops(route_id: str, refresh: bool = False) -> list[dict[str, Any]]:
    """Stops served by one MBTA route: id, name, lat, lng (stations for rail)."""

    def fetch() -> list[dict[str, Any]]:
        time.sleep(MBTA_DELAY)
        data = _get_json(f"{MBTA}/stops", {"filter[route]": route_id,
                                           "fields[stop]": "name,latitude,longitude"})
        return [{"id": s["id"], "name": s["attributes"]["name"],
                 "lat": s["attributes"]["latitude"], "lng": s["attributes"]["longitude"]}
                for s in data["data"]]

    return _cached_json(EXTERNAL / "mbta" / f"stops_{route_id}.json", refresh, fetch)


def mbta_route_shapes(route_id: str, refresh: bool = False) -> list[str]:
    """Encoded polylines of a route's canonical (typicality 1) patterns."""

    def fetch() -> list[str]:
        time.sleep(MBTA_DELAY)
        data = _get_json(f"{MBTA}/route_patterns", {
            "filter[route]": route_id, "filter[canonical]": "true",
            "include": "representative_trip.shape"})
        shapes = [i for i in data.get("included", []) if i["type"] == "shape"]
        if not shapes:  # some routes have no canonical flag: fall back to typical ones
            time.sleep(MBTA_DELAY)
            data = _get_json(f"{MBTA}/route_patterns", {
                "filter[route]": route_id, "include": "representative_trip.shape"})
            shapes = [i for i in data.get("included", []) if i["type"] == "shape"]
        return sorted({s["attributes"]["polyline"] for s in shapes})

    return _cached_json(EXTERNAL / "mbta" / f"shapes_{route_id}.json", refresh, fetch)


def boston_zip_polygons(refresh: bool = False) -> list[dict[str, Any]]:
    """City of Boston ZIP code polygons in WGS84: [{zip, rings}]."""

    def fetch() -> list[dict[str, Any]]:
        data = _get_json(
            "https://gisportal.boston.gov/arcgis/rest/services/Planning/OpenData/MapServer/1/query",
            {"where": "1=1", "outFields": "ZIP5", "returnGeometry": "true",
             "outSR": 4326, "f": "json"})
        return [{"zip": f["attributes"]["ZIP5"], "rings": f["geometry"]["rings"]}
                for f in data["features"]]

    return _cached_json(EXTERNAL / "boston_zip_polygons.json", refresh, fetch)


def massgis_hospitals(refresh: bool = False) -> list[dict[str, Any]]:
    """MassGIS hospital points: [{name, municipality, lat, lng}]."""

    def fetch() -> list[dict[str, Any]]:
        data = _get_json(
            "https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/Hospitals/MapServer/0/query",
            {"where": "1=1", "outFields": "FACILITY_NAME,MUNICIPALITY", "returnGeometry": "true",
             "outSR": 4326, "f": "json"})
        return [{"name": f["attributes"]["FACILITY_NAME"],
                 "municipality": f["attributes"]["MUNICIPALITY"],
                 "lat": f["geometry"]["y"], "lng": f["geometry"]["x"]}
                for f in data["features"] if f.get("geometry")]

    return _cached_json(EXTERNAL / "massgis_hospitals.json", refresh, fetch)


def nbi_massachusetts(refresh: bool = False) -> Path:
    """FHWA NBI 2022 delimited file for Massachusetts (all items, incl. LAT_016/LONG_017)."""
    path = EXTERNAL / "nbi_MA22.txt"
    if path.exists() and not refresh:
        return path
    r = session.get("https://www.fhwa.dot.gov/bridge/nbi/2022/delimited/MA22.txt",
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=TIMEOUT)
    r.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return path


def noaa_station(station: str = "8443970", refresh: bool = False) -> dict[str, Any]:
    """NOAA CO-OPS station position, datums (m, above station datum), flood levels (ft)."""

    def fetch() -> dict[str, Any]:
        base = f"https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{station}"
        meta = _get_json(f"{base}.json")["stations"][0]
        datums = _get_json(f"{base}/datums.json", {"units": "metric"})["datums"]
        flood = _get_json(f"{base}/floodlevels.json")
        return {"name": meta["name"], "lat": meta["lat"], "lng": meta["lng"],
                "datums_m": {d["name"]: d["value"] for d in datums},
                "flood_levels_ft_stnd": {k: v for k, v in flood.items() if k != "self"}}

    return _cached_json(EXTERNAL / f"noaa_{station}.json", refresh, fetch)
