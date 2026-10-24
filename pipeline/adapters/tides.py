"""NOAA Boston tide gauge 8443970 -> water.flood_risk events.

An event is a run of consecutive hourly readings at or above NOAA's minor
coastal flood level. NOAA publishes flood levels in feet above station datum
(STND); they are converted to meters above MLLW to match the readings.
"""

from __future__ import annotations

import pandas as pd

from pipeline import external
from pipeline.common import Result, iso_utc, read_raw, to_float, to_utc

NAME = "tides"
KIND = "events"
STATION = "8443970"
FT_TO_M = 0.3048

SEVERITY_RULE = "Peak level: NOAA minor flood = 3, moderate = 4, major = 5."


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df), severity_rule=SEVERITY_RULE)
    st = external.noaa_station(STATION)
    mllw = st["datums_m"]["MLLW"]
    levels = {k: st["flood_levels_ft_stnd"][f"nos_{k}"] * FT_TO_M - mllw
              for k in ("minor", "moderate", "major")}

    t = to_utc(df["time_gmt"], assume_tz="UTC")
    level = to_float(df["water_level_m"])
    frame = pd.DataFrame({"t": t, "level": level}).dropna().sort_values("t")
    above = frame["level"] >= levels["minor"]
    run_id = (above != above.shift()).cumsum()

    rows = []
    for _, g in frame[above].groupby(run_id[above]):
        peak = g["level"].max()
        cat = "major" if peak >= levels["major"] else "moderate" if peak >= levels["moderate"] \
            else "minor"
        start, end = g["t"].iloc[0], g["t"].iloc[-1] + pd.Timedelta(hours=1)
        rows.append({
            "event_id": f"{NAME}_{STATION}_{start:%Y%m%dT%H%M}",
            "type": "water.flood_risk",
            "start_time": start, "end_time": end,
            "duration_min": (end - start).total_seconds() / 60,
            "lat": st["lat"], "lng": st["lng"],
            "severity": {"minor": 3, "moderate": 4, "major": 5}[cat],
            "source": NAME, "confidence": 0.95,
            "details": {"station_id": STATION, "peak_water_level_m": round(peak, 3),
                        "threshold_m": round(levels["minor"], 3), "flood_category": cat,
                        "datum": "MLLW", "hours_above": len(g),
                        "location_method": "gauge_location", "location_precision_m": None},
            "raw": None,
        })
    out = pd.DataFrame(rows)
    if len(out):
        out["start_time"] = iso_utc(out["start_time"])
        out["end_time"] = iso_utc(out["end_time"])
    res.frame = out
    res.dropped["hourly reading below flood threshold"] += int((~above).sum())
    res.notes.append(f"Thresholds (m above MLLW): " +
                     ", ".join(f"{k} {v:.3f}" for k, v in levels.items()) +
                     ". The gauge sits on the harbor; flood risk applies to the waterfront, "
                     "not just its one grid cell.")
    return res
