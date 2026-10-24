"""Massachusetts hospitals -> base/hospitals.geojson.

The kit drops coordinates; points come from the same MassGIS layer, joined on
facility name.
"""

from __future__ import annotations

import pandas as pd

from pipeline import external
from pipeline.common import Result, read_raw, to_float

NAME = "hospitals"
KIND = "base"


def _key(name: str) -> str:
    return " ".join(name.upper().split())


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df))
    points = {_key(p["name"]): p for p in external.massgis_hospitals()}
    beds = {c: to_float(df[c]) for c in ("icu_beds", "med_surg_beds", "pediatric_beds")}
    features = []
    for i, r in df.iterrows():
        p = points.get(_key(r["name"]))
        if p is None:
            res.dropped["name not found in MassGIS points"] += 1
            continue
        features.append({
            "geometry": {"type": "Point", "coordinates": [p["lng"], p["lat"]]},
            "properties": {
                "name": r["name"], "type": "hospital", "facility_type": r["facility_type"],
                "municipality": r["municipality"],
                **{c: (int(v[i]) if pd.notna(v[i]) else None) for c, v in beds.items()},
            },
        })
    res.layers["hospitals"] = features
    res.unmapped = ["county (redundant with coordinates)"]
    return res
