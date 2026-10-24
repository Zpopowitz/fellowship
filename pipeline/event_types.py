"""Controlled list of event types and the fixed ``details`` fields for each.

Every event's ``type`` must be a key of EVENT_TYPES, and its ``details`` JSON
must contain exactly the fields listed for that type's group (missing values
are null). build.py enforces both.

Severity is an integer 1-5 everywhere:
  1 = cosmetic / informational   2 = minor, easy to route around
  3 = moderate, slows movement   4 = serious, avoid the cell / line
  5 = severe, cell or service effectively unusable
Each adapter documents how its source maps onto this scale (see REPORT.md).
"""

from __future__ import annotations

# Fields every event carries, whatever its group.
LOCATION_FIELDS = ["location_method", "location_precision_m"]

GROUP_FIELDS: dict[str, list[str]] = {
    "crash": ["mode", "involves_pedestrian", "involves_cyclist", "street", "cross_street",
              "location_type", "collision_manner", "first_harmful_event", "light",
              "weather", "road_surface", "speed_limit_kmh"],
    "street_report": ["service_name", "status", "department", "neighborhood", "zip_code",
                      "on_time"],
    "transit": ["alert_id", "effect", "mbta_severity", "routes", "stop_id", "stop_name"],
    "water": ["station_id", "peak_water_level_m", "threshold_m", "flood_category",
              "datum", "hours_above"],
}

EVENT_TYPES: dict[str, dict[str, str]] = {
    # roads
    "road.crash": {"group": "crash", "desc": "Traffic crash at a location"},
    "road.pothole": {"group": "street_report", "desc": "Pothole or missing manhole cover"},
    "road.construction": {"group": "street_report", "desc": "Utility or contractor work in the street"},
    "road.illegal_parking": {"group": "street_report", "desc": "Illegally parked or abandoned vehicle"},
    "road.signal_issue": {"group": "street_report", "desc": "Traffic signal down or malfunctioning"},
    "road.sign_issue": {"group": "street_report", "desc": "Street sign missing, knocked down or damaged"},
    "road.markings_faded": {"group": "street_report", "desc": "Crosswalk, lane or road markings worn"},
    # street space shared by robots and people
    "street.debris": {"group": "street_report", "desc": "Litter, dumping, needles, dead animal, construction debris"},
    "street.fallen_tree": {"group": "street_report", "desc": "Fallen tree or branches"},
    "street.animal": {"group": "street_report", "desc": "Loose domestic or wild animal"},
    "street.emergency": {"group": "street_report", "desc": "General emergency reported through 311"},
    "sidewalk.blocked": {"group": "street_report", "desc": "Sidewalk obstructed (trash, vending, illegal blocking)"},
    "sidewalk.damaged": {"group": "street_report", "desc": "Sidewalk in need of repair"},
    "streetlight.outage": {"group": "street_report", "desc": "Street or park light out, down or unsafe"},
    # transit
    "transit.breakdown": {"group": "transit", "desc": "Delay caused by a disabled vehicle, signal or power problem"},
    "transit.delay": {"group": "transit", "desc": "Service running late"},
    "transit.suspension": {"group": "transit", "desc": "Service suspended"},
    "transit.shuttle": {"group": "transit", "desc": "Rail replaced by shuttle buses"},
    "transit.detour": {"group": "transit", "desc": "Bus detoured; stops skipped"},
    "transit.stop_moved": {"group": "transit", "desc": "Stop temporarily relocated"},
    "transit.station_closure": {"group": "transit", "desc": "Station or stop closed"},
    "transit.station_issue": {"group": "transit", "desc": "Station works or partial closure"},
    "transit.accessibility": {"group": "transit", "desc": "Elevator / escalator out or access issue"},
    "transit.service_change": {"group": "transit", "desc": "Planned service change"},
    # water
    "water.flood_risk": {"group": "water", "desc": "Coastal water level at or above NOAA flood threshold"},
}


def detail_fields(event_type: str) -> list[str]:
    """Ordered list of details keys required for an event type."""
    return GROUP_FIELDS[EVENT_TYPES[event_type]["group"]] + LOCATION_FIELDS
