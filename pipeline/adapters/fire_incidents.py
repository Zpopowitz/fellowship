"""Boston Fire Incident Reporting -> hazard.fire events.

Source: boston_data/D13_fire_incidents/fire_incident_reporting.csv (601,721 rows,
downloaded from data.boston.gov; see boston_data/MANIFEST.md). This is the RAW
source tree, not data/raw/, so this adapter reads it by its full path.

The feed has no coordinates, only a street address, neighborhood and ZIP. Like
boston-311, each kept incident is placed at its ZIP code's area-weighted centroid
(``location_method = "zip_centroid"``). That is coarse on purpose: the data cannot
support street-level fire placement, so the SAR dataset uses it as a per-ZIP fire
RATE, not an exact spot. ``location_precision_m`` records the ZIP's coarseness.

Only incidents that are a real emergency a rescue swarm would respond to are kept:
``incident_category`` in {Fire, Hazardous Situation, Rescue}. The large "blank"
and "Public Service" / "No Emergency" / "Law Enforcement Support" categories are
dropped (not fires). The CSV is read in chunks so it never loads whole (the host
is memory-constrained).
"""

from __future__ import annotations

import pandas as pd

from pipeline.adapters.boston_311 import zip_centroids
from pipeline.common import Result, iso_utc, stable_id, to_utc

NAME = "fire-incidents"
KIND = "events"

# Full path to the raw source file in the boston_data/ tree.
from pipeline.common import ROOT  # noqa: E402
SOURCE = ROOT / "boston_data" / "D13_fire_incidents" / "fire_incident_reporting.csv"

# incident_category -> (event type, severity). Everything else is dropped.
CATEGORY_MAP: dict[str, tuple[str, int]] = {
    "Fire": ("hazard.fire", 5),
    "Hazardous Situation": ("hazard.fire", 4),  # gas leak, spill, arcing wire, etc.
    "Rescue": ("hazard.fire", 5),               # extrication / trapped person
}

SEVERITY_RULE = ("Fire category = 5, Rescue = 5, Hazardous Situation = 4. Other "
                 "categories (Public Service, No Emergency, Law Enforcement Support, "
                 "blank) are not rescue incidents and are dropped.")

CHUNK = 50_000


def _to_int_usd(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0).astype("int64")


def run() -> Result:
    res = Result(NAME, KIND, rows_in=0, severity_rule=SEVERITY_RULE)
    centroids = zip_centroids()

    kept_chunks: list[pd.DataFrame] = []
    rows_in = 0
    dropped_not_rescue = 0
    dropped_zip = 0
    dropped_time = 0

    reader = pd.read_csv(SOURCE, dtype=str, keep_default_na=False, na_values=[""],
                         chunksize=CHUNK, encoding="utf-8", encoding_errors="replace")
    for df in reader:
        rows_in += len(df)
        cat = df["incident_category"].fillna("")
        keep = cat.isin(CATEGORY_MAP)
        dropped_not_rescue += int((~keep).sum())
        df = df[keep]
        if df.empty:
            continue

        # ZIP codes come as "02136"; normalize and require a known Boston ZIP polygon.
        zips = df["zip"].astype("string").str.strip().str.zfill(5)
        known = zips.isin(centroids)
        dropped_zip += int((~known).sum())
        df, zips = df[known], zips[known]
        if df.empty:
            continue

        start = to_utc(df["alarm_date"].fillna("") + "T" + df["alarm_time"].fillna("00:00:00"))
        bad_t = start.isna()
        dropped_time += int(bad_t.sum())
        df, zips, start = df[~bad_t], zips[~bad_t], start[~bad_t]
        if df.empty:
            continue

        loc = zips.map(centroids)
        etype = df["incident_category"].map(lambda c: CATEGORY_MAP[c][0])
        sev = df["incident_category"].map(lambda c: CATEGORY_MAP[c][1])
        loss = _to_int_usd(df["estimated_property_loss"]) + _to_int_usd(df["estimated_content_loss"])

        def details(r: pd.Series, z: str) -> dict:
            return {
                "hazard_kind": "fire",
                "category": r["incident_category"],
                "property_use": r.get("property_use") or r.get("location_type") or None,
                "neighborhood": r.get("neighborhood") or None,
                "zip_code": z,
                "estimated_loss_usd": None,  # filled below per-row
                "location_method": "zip_centroid",
                "location_precision_m": centroids[z][2],
            }

        chunk = pd.DataFrame({
            "event_id": [f"{NAME}_{stable_id(inc, exp, d)}"
                         for inc, exp, d in zip(df["incident_number"], df["exposure_number"],
                                                df["alarm_date"], strict=False)],
            "type": etype.to_numpy(),
            "start_time": iso_utc(start).to_numpy(),
            "end_time": None,
            "duration_min": None,
            "lat": loc.map(lambda t: t[0]).to_numpy(),
            "lng": loc.map(lambda t: t[1]).to_numpy(),
            "severity": sev.astype(int).to_numpy(),
            "source": NAME,
            "confidence": 0.9,  # official fire-department record
            "details": [dict(details(r, z), estimated_loss_usd=int(v))
                        for (_, r), z, v in zip(df.iterrows(), zips, loss, strict=False)],
            "raw": None,
        })
        kept_chunks.append(chunk)

    res.rows_in = rows_in
    res.frame = (pd.concat(kept_chunks, ignore_index=True) if kept_chunks
                 else pd.DataFrame(columns=["event_id", "type", "start_time", "end_time",
                                            "duration_min", "lat", "lng", "severity",
                                            "source", "confidence", "details", "raw"]))
    res.dropped["category not a rescue incident"] += dropped_not_rescue
    res.dropped["ZIP missing or not a Boston ZIP polygon"] += dropped_zip
    res.dropped["unparseable alarm time"] += dropped_time
    res.unmapped = ["incident_number, exposure_number (ids; folded into event_id)",
                    "incident_type, incident_description, incident_detail (NFIRS code text)",
                    "address, district, city_section (street address not geocoded; ZIP used)",
                    "location_subtype, property_description (free text)"]
    res.notes.append("Placed at ZIP centroid (no coordinates in the feed), same method as "
                     "boston-311. Fire density per ZIP is real; exact street location is not "
                     "available, so the SAR builder treats this as a per-ZIP fire rate.")
    res.notes.append("Duplicate incident rows (same incident reported on several NFIRS lines) "
                     "collapse to one event by (incident_number, exposure_number, alarm_date).")
    return res
