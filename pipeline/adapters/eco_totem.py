"""Cambridge Broadway Eco-Totem -> 15-minute bike counts."""

from __future__ import annotations

import pandas as pd

from pipeline.common import Result, iso_utc, read_raw, to_float, to_utc
from pipeline.locations import ECO_TOTEM

NAME = "eco-totem"
KIND = "density"


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df))
    # Wall-clock without an offset: Cambridge local time.
    t = to_utc(df["when"])
    value = to_float(df["total"])
    ok = t.notna() & value.notna()
    res.dropped["unparseable or ambiguous (DST) time"] += int((~ok).sum())
    res.frame = pd.DataFrame({
        "lat": ECO_TOTEM["lat"],
        "lng": ECO_TOTEM["lng"],
        "time_bucket": iso_utc(t[ok].dt.floor("15min")),
        "metric": "bikes",
        "value": value[ok],
        "source": NAME,
        "sensor_id": "eco_totem_broadway",
        "interval_min": 15,
    })
    res.unmapped = ["entries, exits (sum to total; the city does not say which direction "
                    "each is)", "day (derivable)"]
    res.notes.append(f"Location approximate (+/-{ECO_TOTEM['precision_m']} m): "
                     f"{ECO_TOTEM['source']}.")
    return res
