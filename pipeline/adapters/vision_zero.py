"""Boston Vision Zero crash records -> road.crash events."""

from __future__ import annotations

import pandas as pd

from pipeline.common import Result, iso_utc, read_raw, stable_id, to_float, to_utc

NAME = "vision-zero"
KIND = "events"

MODES = {"mv": "vehicle", "ped": "pedestrian", "bike": "bicycle"}
SEVERITY = {"ped": 4, "bike": 4, "mv": 3}
SEVERITY_RULE = ("No injury field is published. Crashes involving a pedestrian or cyclist = 4, "
                 "motor-vehicle only = 3.")


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df), severity_rule=SEVERITY_RULE)
    start = to_utc(df["when"])
    res.dropped["unparseable time"] += int(start.isna().sum())

    def details(r: pd.Series) -> dict:
        return {
            "mode": MODES.get(r["mode"], r["mode"]),
            "involves_pedestrian": r["mode"] == "ped",
            "involves_cyclist": r["mode"] == "bike",
            "street": r["street"], "cross_street": r["cross_street"],
            "location_type": r["where"],
            "collision_manner": None, "first_harmful_event": None, "light": None,
            "weather": None, "road_surface": None, "speed_limit_kmh": None,
            "location_method": "published_point", "location_precision_m": None,
        }

    # No record id in the table: id is a hash of the full row.
    ids = df.apply(lambda r: f"{NAME}_{stable_id(*r.values)}", axis=1)
    out = pd.DataFrame({
        "event_id": ids,
        "type": "road.crash",
        "start_time": iso_utc(start),
        "end_time": None,
        "duration_min": None,
        "lat": to_float(df["latitude"]),
        "lng": to_float(df["longitude"]),
        "severity": df["mode"].map(SEVERITY).fillna(3).astype(int),
        "source": NAME,
        "confidence": 0.9,
        "details": df.apply(details, axis=1),
        "raw": None,
    })
    res.frame = out[start.notna()]
    res.unmapped = ["cross_street_2 (second cross street; kept only in source)"]
    return res
