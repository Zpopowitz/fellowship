"""Boston street centerlines -> base/streets.geojson (and the occupancy grid)."""

from __future__ import annotations

import re

import pandas as pd

from pipeline.common import MPH_TO_KMH, Result, haversine_m, read_raw, to_float

NAME = "boston-streets"
KIND = "base"

_PART = re.compile(r"\(([^()]+)\)")


def parse_multilinestring(wkt: str) -> list[list[list[float]]]:
    """WKT MULTILINESTRING / LINESTRING -> list of [lng, lat] lines."""
    return [[[float(v) for v in pt.split()] for pt in part.split(",")]
            for part in _PART.findall(wkt)]


def line_length_m(lines: list[list[list[float]]]) -> float:
    return sum(haversine_m(a[1], a[0], b[1], b[0])
               for line in lines for a, b in zip(line[:-1], line[1:], strict=False))


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df))
    no_geom = df["geometry"].isna()
    res.dropped["no geometry in source"] += int(no_geom.sum())
    df = df[~no_geom]

    speed = to_float(df["speed_mph"])
    fwd, back = to_float(df["cost_forward"]), to_float(df["cost_back"])
    features = []
    for i, r in df.iterrows():
        lines = parse_multilinestring(r["geometry"])
        name = " ".join(x for x in (r["street"], r["type"]) if pd.notna(x)) or None
        features.append({
            "geometry": {"type": "MultiLineString", "coordinates": lines},
            "properties": {
                "name": name,
                "type": "street",
                "speed_limit_kmh": round(speed[i] * MPH_TO_KMH, 1) if pd.notna(speed[i]) else None,
                "oneway": r["oneway"] if pd.notna(r["oneway"]) else None,
                # SAM marks a direction that cannot be driven with cost -1.
                "traversable_forward": bool(fwd[i] != -1) if pd.notna(fwd[i]) else None,
                "traversable_back": bool(back[i] != -1) if pd.notna(back[i]) else None,
                "neighborhood": r["neighborhood"] if pd.notna(r["neighborhood"]) else None,
                "zip": r["zip"] if pd.notna(r["zip"]) else None,
                "length_m": round(line_length_m(lines), 1),
            },
        })
    res.layers["streets"] = features
    res.unmapped = ["cost_forward, cost_back (unitless SAM travel cost; only -1 = "
                    "not traversable is kept)", "shape_length (degrees; replaced by length_m)"]
    return res
