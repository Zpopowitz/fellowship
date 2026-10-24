"""Boston 311 service requests -> street-level events.

The saved slice has no coordinates, only ZIP / ward / neighborhood, so each case
is placed at its ZIP code's area-weighted centroid (City of Boston ZIP polygons).
That is coarse: ``location_precision_m`` holds half the square root of the ZIP's
area, and every event is marked ``location_method = "zip_centroid"``.
"""

from __future__ import annotations

import math

import pandas as pd

from pipeline import external
from pipeline.common import Result, iso_utc, read_raw, stable_id, to_utc

NAME = "boston-311"
KIND = "events"

# service_name -> (event type, severity). Anything not listed is not something a
# street robot meets (admin requests, park programming) and is dropped.
SERVICE_MAP: dict[str, tuple[str, int]] = {
    "Illegal Parking": ("road.illegal_parking", 2),
    "Abandoned Vehicles": ("road.illegal_parking", 2),
    "Pothole": ("road.pothole", 3),
    "Missing Manhole Cover": ("road.pothole", 5),
    "Utility Contractor Complaints": ("road.construction", 3),
    "Traffic Signal Knockdown": ("road.signal_issue", 4),
    "Traffic Signal Request": ("road.signal_issue", 2),
    "Missing / Knocked Down Sign": ("road.sign_issue", 2),
    "Knocked Down Sign": ("road.sign_issue", 2),
    "Damaged/Faded Sign": ("road.sign_issue", 1),
    "Crosswalk Maintenance": ("road.markings_faded", 2),
    "Road Marking Maintenance": ("road.markings_faded", 1),
    "Lane Divider": ("road.markings_faded", 2),
    "Litter & Debris": ("street.debris", 1),
    "Illegal Dumping or Disposal": ("street.debris", 3),
    "Construction Debris": ("street.debris", 3),
    "Needle Pickup": ("street.debris", 3),
    "Dead Animal General": ("street.debris", 2),
    "Fallen Tree or Branches": ("street.fallen_tree", 4),
    "Domestic Animal Issue": ("street.animal", 2),
    "Wild Animal Issue": ("street.animal", 2),
    "General Emergency": ("street.emergency", 5),
    "Illegally Blocked Sidewalk": ("sidewalk.blocked", 4),
    "Trash Placed Out Early": ("sidewalk.blocked", 2),
    "Improper Trash Storage": ("sidewalk.blocked", 2),
    "Overflowing Trash": ("sidewalk.blocked", 2),
    "Missed Waste Pick-up": ("sidewalk.blocked", 2),
    "Broken Public Waste Receptacle": ("sidewalk.blocked", 1),
    "Unauthorized Vending": ("sidewalk.blocked", 2),
    "Sidewalk Repair": ("sidewalk.damaged", 3),
    "Street Light Outage": ("streetlight.outage", 2),
    "Street Light Knockdown": ("streetlight.outage", 4),
    "Street Light Electrical Safety": ("streetlight.outage", 4),
    "Street Light Other": ("streetlight.outage", 1),
    "Park Light Outage": ("streetlight.outage", 2),
}

SEVERITY_RULE = ("Fixed severity per 311 service type (see SERVICE_MAP in "
                 "pipeline/adapters/boston_311.py): e.g. litter 1, illegal parking 2, pothole 3, "
                 "blocked sidewalk / fallen tree / signal knockdown 4, missing manhole cover / "
                 "general emergency 5.")


def zip_centroids() -> dict[str, tuple[float, float, float]]:
    """ZIP -> (lat, lng, precision_m) from area-weighted ring centroids."""
    acc: dict[str, list[float]] = {}
    for f in external.boston_zip_polygons():
        for ring in f["rings"]:
            a = cx = cy = 0.0
            for (x0, y0), (x1, y1) in zip(ring[:-1], ring[1:], strict=False):
                cross = x0 * y1 - x1 * y0
                a += cross
                cx += (x0 + x1) * cross
                cy += (y0 + y1) * cross
            a /= 2  # signed: holes subtract from their outer ring
            if a == 0:
                continue
            s = acc.setdefault(f["zip"], [0.0, 0.0, 0.0])
            s[0] += a
            s[1] += cx / 6
            s[2] += cy / 6
    out = {}
    for z, (a, sx, sy) in acc.items():
        lat, lng = sy / a, sx / a
        area_m2 = abs(a) * (111_320 ** 2) * math.cos(math.radians(lat))
        out[z] = (lat, lng, round(math.sqrt(area_m2) / 2))
    return out


def run() -> Result:
    df = read_raw(NAME)
    res = Result(NAME, KIND, rows_in=len(df), severity_rule=SEVERITY_RULE)

    mapped = df["service_name"].isin(SERVICE_MAP)
    res.dropped["service type not street-level"] += int((~mapped).sum())
    skipped = df.loc[~mapped, "service_name"].value_counts()
    res.notes.append("Service types dropped as not street-level: " +
                     ", ".join(f"{name} ({n})" for name, n in skipped.items()) + ".")
    df = df[mapped]

    centroids = zip_centroids()
    known_zip = df["zip_code"].isin(centroids)
    res.dropped["ZIP missing or not a Boston ZIP polygon"] += int((~known_zip).sum())
    df = df[known_zip]

    start = to_utc(df["open_date"])
    res.dropped["unparseable time"] += int(start.isna().sum())
    df, start = df[start.notna()], start[start.notna()]

    loc = df["zip_code"].map(centroids)
    types = df["service_name"].map(lambda s: SERVICE_MAP[s][0])
    sev = df["service_name"].map(lambda s: SERVICE_MAP[s][1])

    def details(r: pd.Series) -> dict:
        return {
            "service_name": r["service_name"], "status": r["case_status"],
            "department": r["assigned_department"], "neighborhood": r["neighborhood"],
            "zip_code": r["zip_code"], "on_time": r["on_time"] == "ONTIME",
            "location_method": "zip_centroid",
            "location_precision_m": centroids[r["zip_code"]][2],
        }

    res.frame = pd.DataFrame({
        "event_id": df.apply(lambda r: f"{NAME}_{stable_id(*r.values)}", axis=1),
        "type": types,
        "start_time": iso_utc(start),
        "end_time": None,
        "duration_min": None,
        "lat": loc.map(lambda t: t[0]),
        "lng": loc.map(lambda t: t[1]),
        "severity": sev.astype(int),
        "source": NAME,
        "confidence": 0.6,  # citizen report, not verified on site
        "details": df.apply(details, axis=1),
        "raw": None,
    })
    res.unmapped = ["case_topic (identical to service_name)",
                    "city_council_district, ward (administrative areas)"]
    res.notes.append("No case id or close date in the slice: event_id is a row hash and "
                     "end_time is null.")
    return res
