"""Hand-curated coordinates for sources that publish a place name but no point.

Each entry records where the coordinate came from so it can be checked.
"""

from __future__ import annotations

# Numina sensors (Analyze Boston "Numina Sensor Measurement of Multimodal Activity
# and Shared Streets"). Zone id -> resource file was matched via the datastore API.
# The sensor PDFs all repeat the Northern Ave coordinate, so only Northern Ave uses
# it; the other two sites use the City of Boston SAM intersection points.
NUMINA_SITES = {
    "jackson_square": {"lat": 42.322815, "lng": -71.100574,
                       "source": "SAM intersection 'Centre St / Lamartine St'"},
    "northern_ave": {"lat": 42.353301, "lng": -71.046501,
                     "source": "Numina sensor PDF location field (sensor 2)"},
    "tremont": {"lat": 42.352368, "lng": -71.064543,
                "source": "SAM intersection 'Boylston St / Tremont St'"},
}

NUMINA_ZONES = {
    "52115": ("jackson_square", "eastbound_lanes"),
    "52113": ("jackson_square", "eastside_crosswalk"),
    "51671": ("jackson_square", "northside_sidewalk"),
    "52114": ("jackson_square", "westbound_lanes"),
    "52110": ("northern_ave", "northside_sidewalk"),
    "52112": ("northern_ave", "roadway"),
    "51600": ("tremont", "diagonal_crossing"),
    "52117": ("tremont", "northside_crosswalk"),
    "52116": ("tremont", "northwest_side_bicycles"),
}

# Cambridge Broadway Eco-Totem. The city only says "Broadway in Kendall Square";
# this is the midpoint of Broadway between Ames St and Galileo Galilei Way
# (OpenStreetMap), so it is approximate to roughly +/-150 m.
ECO_TOTEM = {"lat": 42.36452, "lng": -71.08835, "precision_m": 150,
             "source": "Approximate: Broadway between Ames St and Galileo Galilei Way"}
