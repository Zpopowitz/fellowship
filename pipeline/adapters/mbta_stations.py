"""MBTA rapid transit stations -> base/transit_stations.geojson.

The kit has station names and lines only; coordinates come from the MBTA v3
stops of the rapid transit and Silver Line routes, joined on normalized station
name: exact match first, then the shortest MBTA stop name that contains the kit
name or is contained in it (e.g. "Herald Street" -> "Washington St @ Herald St").
"""

from __future__ import annotations

import re

from pipeline import external
from pipeline.common import Result, read_raw

NAME = "mbta-stations"
KIND = "base"
RAPID_ROUTES = ["Red", "Mattapan", "Orange", "Green-B", "Green-C", "Green-D", "Green-E", "Blue",
                "741", "742", "743", "746", "749", "751"]  # 74x/75x = Silver Line
LINE_OF_ROUTE = {r: "SILVER" for r in ("741", "742", "743", "746", "749", "751")} | {
    "Mattapan": "RED"}

_WORDS = {"street": "st", "avenue": "ave", "square": "sq", "east": "e", "west": "w",
          "airport": "", "&": "and"}


def _key(name: str) -> str:
    n = name.lower()
    for long, short in _WORDS.items():
        n = re.sub(rf"\b{re.escape(long)}\b" if long.isalpha() else re.escape(long), short, n)
    return re.sub(r"[^a-z0-9]", "", n)


def _match(key: str, stops: dict[str, dict]) -> dict | None:
    if key in stops:
        return stops[key]
    hits = [k for k in stops if len(key) >= 4 and (key in k or (len(k) >= 4 and k in key))]
    return stops[min(hits, key=len)] if hits else None


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df))
    # Stops per kit line label, so a Silver Line "Massachusetts Ave" matches the
    # Silver Line stop rather than the Orange Line station of the same name.
    by_line: dict[str, dict[str, dict]] = {}
    for route in RAPID_ROUTES:
        line = LINE_OF_ROUTE.get(route, route.split("-")[0].upper())
        for s in external.mbta_route_stops(route):
            by_line.setdefault(line, {}).setdefault(_key(s["name"]), s)
    all_stops = {k: s for stops in by_line.values() for k, s in stops.items()}

    features, seen = [], set()
    for _, r in df.iterrows():
        key = _key(r["station"])
        line_stops = {k: s for line in r["line"].split("/")
                      for k, s in by_line.get(line.strip(), {}).items()}
        s = _match(key, line_stops) or _match(key, all_stops)
        if s is None:
            res.dropped["station name not matched to an MBTA stop"] += 1
            res.notes.append(f"unmatched station: {r['station']}")
            continue
        if s["id"] in seen:
            res.dropped["duplicate station row"] += 1
            continue
        seen.add(s["id"])
        features.append({
            "geometry": {"type": "Point", "coordinates": [s["lng"], s["lat"]]},
            "properties": {"name": s["name"], "type": "transit_station", "stop_id": s["id"],
                           "lines": [x.strip() for x in r["line"].split("/")],
                           "route_text": r["route"]},
        })
    res.layers["transit_stations"] = features
    return res
