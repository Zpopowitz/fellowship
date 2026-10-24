"""MassGIS colleges and universities -> base/colleges.geojson."""

from __future__ import annotations

import pandas as pd

from pipeline.common import Result, read_raw, to_float

NAME = "colleges"
KIND = "base"


def _clean(v: object) -> object:
    return None if pd.isna(v) else v


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df))
    lat, lng = to_float(df["latitude"]), to_float(df["longitude"])
    features = []
    for i, r in df.iterrows():
        if pd.isna(lat[i]) or pd.isna(lng[i]):
            res.dropped["no coordinates"] += 1
            continue
        name = r["college"] + (f" ({r['campus']})" if pd.notna(r["campus"]) else "")
        features.append({
            "geometry": {"type": "Point", "coordinates": [lng[i], lat[i]]},
            "properties": {"name": name, "type": "college", "category": _clean(r["category"]),
                           "level": _clean(r["level"]), "control": _clean(r["type"]),
                           "has_housing": r["housing"] == "Yes", "city": _clean(r["city"])},
        })
    res.layers["colleges"] = features
    res.unmapped = ["zip, town (redundant with city / coordinates)"]
    return res
