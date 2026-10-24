"""MBTA service alerts -> transit.* events.

The saved alerts list route ids but no stops or coordinates. Each alert is placed:
  1. at the stop(s) of its routes whose name appears in the alert text
     (``location_method = "stop_named_in_text"``), else
  2. at every grid cell that holds a stop of an affected route, one event per
     cell (``location_method = "route_stop_cells"``).
Stops come from the MBTA v3 API (pipeline/external.py). Events from one alert
share ``details.alert_id``.
"""

from __future__ import annotations

import math
import re

import pandas as pd

from pipeline import external, grid
from pipeline.common import Result, iso_utc, read_raw, stable_id, to_utc

NAME = "mbta-alerts"
KIND = "events"

EFFECT_MAP = {
    "DELAY": "transit.delay",
    "SUSPENSION": "transit.suspension",
    "SHUTTLE": "transit.shuttle",
    "DETOUR": "transit.detour",
    "STOP_MOVE": "transit.stop_moved",
    "STATION_CLOSURE": "transit.station_closure",
    "STOP_CLOSURE": "transit.station_closure",
    "STATION_ISSUE": "transit.station_issue",
    "ELEVATOR_CLOSURE": "transit.accessibility",
    "ESCALATOR_CLOSURE": "transit.accessibility",
    "ACCESS_ISSUE": "transit.accessibility",
    "SERVICE_CHANGE": "transit.service_change",
}
BREAKDOWN = re.compile(r"disabled|mechanical|signal problem|power problem|switch problem",
                       re.IGNORECASE)

SEVERITY_RULE = ("MBTA publishes severity 0-10; mapped as ceil(mbta / 2), clamped to 1-5.")


def _named_stops(text: str, stops: list[dict]) -> list[dict]:
    """Stops whose name appears in the text; longest names win (e.g. 'South Station')."""
    lower = text.lower()
    hits = [s for s in stops if len(s["name"]) >= 4 and s["name"].lower() in lower]
    if not hits:
        return []
    longest = max(len(s["name"]) for s in hits)
    return [s for s in hits if len(s["name"]) == longest]


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df), severity_rule=SEVERITY_RULE)
    # Flattened from the API without the offset: MBTA publishes Boston local time.
    updated = to_utc(df["updated"])

    rows = []
    for i, r in df.iterrows():
        effect = r["effect"]
        if effect not in EFFECT_MAP:
            res.dropped[f"effect not a disruption: {effect}"] += 1
            continue
        etype = EFFECT_MAP[effect]
        if etype == "transit.delay" and BREAKDOWN.search(r["header"] or ""):
            etype = "transit.breakdown"
        routes = [x.strip() for x in (r["routes"] or "").split(",") if x.strip()]
        stops = [dict(s, route=rt) for rt in routes for s in external.mbta_route_stops(rt)]
        alert_id = stable_id(r["updated"], r["effect"], r["routes"], r["header"])

        named = _named_stops(r["header"] or "", stops)
        method = "stop_named_in_text" if named else "route_stop_cells"
        # One event per grid cell: stops sharing a cell collapse into one.
        by_cell: dict[tuple[int, int], dict] = {}
        for s in named or stops:
            cell = grid.latlng_to_cell(s["lat"], s["lng"])
            if cell and cell not in by_cell:
                by_cell[cell] = s
        if not by_cell:
            res.dropped["no affected stop inside the grid"] += 1
            continue

        sev = int(r["severity"]) if r["severity"] else 1
        for (row, col), s in by_cell.items():
            rows.append({
                "event_id": f"{NAME}_{alert_id}_{row}_{col}",
                "type": etype,
                "start_time": updated[i],
                "end_time": None,
                "duration_min": None,
                "lat": s["lat"],
                "lng": s["lng"],
                "severity": min(5, max(1, math.ceil(sev / 2))),
                "source": NAME,
                "confidence": 0.95,
                "details": {
                    "alert_id": alert_id, "effect": effect, "mbta_severity": sev,
                    "routes": routes,
                    "stop_id": s["id"] if method == "stop_named_in_text" else None,
                    "stop_name": s["name"] if method == "stop_named_in_text" else None,
                    "location_method": method,
                    "location_precision_m": 50 if method == "stop_named_in_text" else None,
                },
                "raw": r["header"],
            })
    out = pd.DataFrame(rows)
    out["start_time"] = iso_utc(out["start_time"])
    res.frame = out
    res.notes.append("start_time is the alert's last-updated time; the snapshot has no "
                     "active period, so end_time is null.")
    return res
