"""National Bridge Inventory (MA, 2022) -> base/bridges.geojson.

The kit drops coordinates; LAT_016 / LONG_017 come from the full FHWA file,
joined on structure number. NBI encodes them as DDMMSSss / DDDMMSSss (west).
"""

from __future__ import annotations

import pandas as pd

from pipeline import external
from pipeline.common import Result, read_raw

NAME = "bridges"
KIND = "base"


def _dms(value: str, deg_digits: int) -> float | None:
    v = value.strip().strip("'")
    if not v.isdigit() or int(v) == 0:
        return None
    v = v.zfill(deg_digits + 6)
    d, m, s = int(v[:deg_digits]), int(v[deg_digits:deg_digits + 2]), int(v[deg_digits + 2:])
    return d + m / 60 + s / 100 / 3600


def _condition(v: object) -> int | None:
    """NBI condition rating 0-9 (9 = excellent); 'N' = not applicable."""
    return int(v) if isinstance(v, str) and v.isdigit() else None


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df))
    nbi = pd.read_csv(external.nbi_massachusetts(), dtype=str, quotechar="'",
                      usecols=["STRUCTURE_NUMBER_008", "LAT_016", "LONG_017"])
    coords = {}
    for sid, la, lo in nbi.itertuples(index=False):
        lat, lng = _dms(la or "", 2), _dms(lo or "", 3)
        if lat and lng:
            coords[sid.strip()] = (lat, -lng)

    features = []
    for _, r in df.iterrows():
        c = coords.get(r["structure_id"].strip())
        if c is None:
            res.dropped["no NBI coordinates for structure"] += 1
            continue
        carries, crosses = r["carries"], r["crosses"]
        features.append({
            "geometry": {"type": "Point", "coordinates": [c[1], c[0]]},
            "properties": {
                "name": f"{carries} over {crosses}" if crosses else carries,
                "type": "bridge", "structure_id": r["structure_id"],
                "carries": carries, "crosses": crosses,
                "year_built": int(r["year_built"]) if str(r["year_built"]).isdigit() else None,
                "material": r["kind"],
                "deck_condition": _condition(r["deck_condition"]),
                "superstructure_condition": _condition(r["superstructure_condition"]),
                "substructure_condition": _condition(r["substructure_condition"]),
            },
        })
    res.layers["bridges"] = features
    res.unmapped = ["county (redundant with coordinates)"]
    return res
