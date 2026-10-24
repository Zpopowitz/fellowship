"""Cambridge police crash records -> road.crash events."""

from __future__ import annotations

import pandas as pd

from pipeline.common import MPH_TO_KMH, Result, iso_utc, read_raw, stable_id, to_float, to_utc

NAME = "cambridge-crashes"
KIND = "events"

SEVERITY_RULE = ("No injury field is published. Base 3; 4 when a pedestrian or cyclist is "
                 "involved.")


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df), severity_rule=SEVERITY_RULE)

    # Times are wall-clock without an offset: Cambridge local time.
    start = to_utc(df["when"])
    lat, lng = to_float(df["latitude"]), to_float(df["longitude"])
    no_coords = lat.isna() | lng.isna()
    res.dropped["no coordinates in source"] += int(no_coords.sum())
    bad_time = start.isna() & ~no_coords
    res.dropped["unparseable or ambiguous (DST) time"] += int(bad_time.sum())
    keep = ~no_coords & ~bad_time

    ped = df["pedestrian"].fillna("") == "1"
    cyc = df["cyclist"].fillna("") == "1"
    speed = to_float(df["speed_limit"])

    def details(i: int) -> dict:
        r = df.loc[i]
        cross = r["cross_street"] if pd.notna(r["cross_street"]) else r["near_street"]
        return {
            "mode": "pedestrian" if ped[i] else "bicycle" if cyc[i] else "vehicle",
            "involves_pedestrian": bool(ped[i]), "involves_cyclist": bool(cyc[i]),
            "street": r["street"], "cross_street": cross,
            "location_type": r["at"],
            "collision_manner": r["manner"], "first_harmful_event": r["first_event"],
            "light": r["light"], "weather": r["weather"], "road_surface": r["road"],
            "speed_limit_kmh": round(speed[i] * MPH_TO_KMH, 1) if pd.notna(speed[i]) else None,
            "location_method": "published_point", "location_precision_m": None,
        }

    out = pd.DataFrame({
        "event_id": df.apply(lambda r: f"{NAME}_{stable_id(*r.values)}", axis=1),
        "type": "road.crash",
        "start_time": iso_utc(start),
        "end_time": None,
        "duration_min": None,
        "lat": lat,
        "lng": lng,
        "severity": (3 + (ped | cyc).astype(int)),
        "source": NAME,
        "confidence": 0.9,
        "details": [details(i) for i in df.index],
        "raw": None,
    })
    res.frame = out[keep]
    res.unmapped = ["day (derivable from start_time)"]
    return res
