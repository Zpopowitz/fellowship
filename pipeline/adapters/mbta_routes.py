"""MBTA subway routes -> base/transit_routes.geojson (canonical shapes from the MBTA API)."""

from __future__ import annotations

from pipeline import external
from pipeline.common import Result, read_raw

NAME = "mbta-routes"
KIND = "base"


def decode_polyline(encoded: str) -> list[list[float]]:
    """Google encoded polyline -> [[lng, lat], ...]."""
    coords, i, lat, lng = [], 0, 0, 0
    while i < len(encoded):
        for axis in (0, 1):
            shift = result = 0
            while True:
                b = ord(encoded[i]) - 63
                i += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if axis == 0:
                lat += delta
            else:
                lng += delta
        coords.append([lng / 1e5, lat / 1e5])
    return coords


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df))
    features = []
    for _, r in df.iterrows():
        shapes = external.mbta_route_shapes(r["id"])
        if not shapes:
            res.dropped["no shape returned by MBTA API"] += 1
            continue
        features.append({
            "geometry": {"type": "MultiLineString",
                         "coordinates": [decode_polyline(p) for p in shapes]},
            "properties": {"name": r["name"], "type": "transit_route", "route_id": r["id"],
                           "mode": r["mode"], "fare_class": r["fare_class"]},
        })
    res.layers["transit_routes"] = features
    return res
