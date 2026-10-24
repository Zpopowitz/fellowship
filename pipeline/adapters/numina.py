"""Boston Numina street sensors -> hourly density by mode.

Nine behavior zones at three sites (pipeline/locations.py). Counts are hourly,
so each row lands in the 15-minute bucket starting on the hour and carries
``interval_min = 60``.
"""

from __future__ import annotations

import pandas as pd

from pipeline.common import Result, iso_utc, read_raw, to_float, to_utc
from pipeline.locations import NUMINA_SITES, NUMINA_ZONES

NAME = "numina"
KIND = "density"

METRICS = {"pedestrian": "pedestrians", "bicycle": "bikes", "car": "cars",
           "truck": "trucks", "bus": "buses"}


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df))

    known = df["zone"].isin(NUMINA_ZONES)
    res.dropped["unknown zone id"] += int((~known).sum())
    df = df[known]
    t = to_utc(df["time"])
    value = to_float(df["count"])
    ok = t.notna() & value.notna()
    res.dropped["unparseable time or count"] += int((~ok).sum())
    df, t, value = df[ok], t[ok], value[ok]

    site = df["zone"].map(lambda z: NUMINA_ZONES[z][0])
    res.frame = pd.DataFrame({
        "lat": site.map(lambda s: NUMINA_SITES[s]["lat"]),
        "lng": site.map(lambda s: NUMINA_SITES[s]["lng"]),
        "time_bucket": iso_utc(t.dt.floor("15min")),
        "metric": df["object"].map(METRICS),
        "value": value,
        "source": NAME,
        "sensor_id": "numina_" + site + "_" + df["zone"].map(lambda z: NUMINA_ZONES[z][1]),
        "interval_min": 60,
    })
    res.unmapped = ["metric (always 'count')"]
    res.notes.append("Sensor sites: Jackson Sq (Centre St / Lamartine St), Northern Ave "
                     "(Seaport), Tremont St / Boylston St. Coverage 2020-07 to 2021-04.")
    return res
