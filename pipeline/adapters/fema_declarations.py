"""OpenFEMA disaster declarations (Massachusetts) -> hazard.flood events.

Source: data/raw/_excluded/fema/data.csv (415 MA declarations). This feed is
COUNTY-LEVEL: each row is "a disaster of this type was declared for this county
on this date", with NO coordinates and NO sub-county location. It therefore
cannot place a flood on a specific cell.

What it CAN do honestly: tell the swarm that flooding is a real, repeatedly
declared hazard for the Boston area, with real dates and categories. So this
adapter keeps only water-related declarations whose ``designatedArea`` covers
Boston's county (Suffolk) or is a statewide/all-counties declaration, and places
each at the GRID CENTRE with ``location_method = "county_declaration"`` and a
county-scale ``location_precision_m``. The SAR builder treats these as a
regional flood BASELINE, never as an exact flood cell.

Water-related incident types kept: Flood, Coastal Storm, Hurricane, Severe Storm,
Tsunami. (Hurricanes and severe/coastal storms are the cause of Boston's actual
flooding; winter storms, snow, ice, biological and fishing-loss declarations are
dropped as not flooding.)
"""
from __future__ import annotations

import pandas as pd

from pipeline import grid
from pipeline.common import RAW, Result, iso_utc, stable_id, to_utc

NAME = "fema-declarations"
KIND = "events"

# This dataset was moved to _excluded/ by the original pipeline; read it there.
SOURCE = RAW / "_excluded" / "fema" / "data.csv"

# incident type -> flood category + severity (1-5). Everything else is dropped.
WATER_TYPES: dict[str, tuple[str, int]] = {
    "Flood": ("major", 5),
    "Hurricane": ("major", 5),
    "Coastal Storm": ("moderate", 4),
    "Severe Storm": ("moderate", 4),
    "Tsunami": ("major", 5),
}

# Area strings that mean "includes Boston". Suffolk is Boston's county; a few
# older declarations are statewide and list all counties / "Statewide".
BOSTON_AREA_HINTS = ("Suffolk", "Boston", "Statewide", "(all)", "All counties")

SEVERITY_RULE = ("FEMA declaration: Flood / Hurricane / Tsunami = 5, Coastal Storm / "
                 "Severe Storm = 4. County-level only; non-water incident types dropped.")


def _covers_boston(area: str) -> bool:
    area = area or ""
    return any(h.lower() in area.lower() for h in BOSTON_AREA_HINTS)


def run() -> Result:
    res = Result(NAME, KIND, rows_in=0, severity_rule=SEVERITY_RULE)
    df = pd.read_csv(SOURCE, dtype=str, keep_default_na=False, na_values=[""])
    res.rows_in = len(df)

    water = df["incidentType"].isin(WATER_TYPES)
    res.dropped["incident type not water-related"] += int((~water).sum())
    df = df[water]

    boston = df["designatedArea"].map(_covers_boston)
    res.dropped["designated area does not cover Boston (Suffolk)"] += int((~boston).sum())
    df = df[boston]

    start = to_utc(df["declarationDate"], assume_tz="UTC")
    bad = start.isna()
    res.dropped["unparseable declaration date"] += int(bad.sum())
    df, start = df[~bad], start[~bad]

    # Place at the grid centre; county-scale precision (~Suffolk County radius).
    clat, clng = grid.cell_center(grid.SIZE // 2, grid.SIZE // 2)
    county_precision_m = 12000  # Suffolk County is ~120 km^2; half-extent order

    cat = df["incidentType"].map(lambda t: WATER_TYPES[t][0])
    sev = df["incidentType"].map(lambda t: WATER_TYPES[t][1])

    def details(r: pd.Series) -> dict:
        return {
            "hazard_kind": "flood",
            "category": r["incidentType"],
            "property_use": None,
            "neighborhood": r["designatedArea"],
            "zip_code": None,
            "estimated_loss_usd": None,
            "location_method": "county_declaration",
            "location_precision_m": county_precision_m,
        }

    res.frame = pd.DataFrame({
        "event_id": df.apply(
            lambda r: f"{NAME}_{stable_id(r['disasterNumber'], r['designatedArea'])}", axis=1),
        "type": "hazard.flood",
        "start_time": iso_utc(start),
        "end_time": None,
        "duration_min": None,
        "lat": clat,
        "lng": clng,
        "severity": sev.astype(int),
        "source": NAME,
        "confidence": 0.9,  # official federal declaration (but coarse location)
        "details": df.apply(details, axis=1),
        "raw": None,
    })
    res.unmapped = ["declarationTitle (free text, kept only in source)",
                    "declarationType (DR/EM/FM declaration class)"]
    res.notes.append("COUNTY-LEVEL ONLY: declarations carry no coordinates, so every flood "
                     "event sits at the grid centre with location_method='county_declaration'. "
                     "Used as a regional flood baseline, never an exact flood cell.")
    res.notes.append("Kept water incident types: " + ", ".join(WATER_TYPES) +
                     "; areas covering Boston (Suffolk) or statewide.")
    return res
