"""The shared 256 x 256 Boston grid.

Bounds are the extent of the City of Boston street centerlines (boston-streets),
rounded outward. That box is ~18.2 km east-west by ~18.1 km north-south, so a
cell is ~71 m on a side. Row 0 is the north edge, column 0 the west edge.

The Moving AI ``boston-map`` grid is NOT used: it carries no lat/lng bounds and
did not line up with the street network in any orientation (see REPORT.md).
Occupancy is instead derived from the street centerlines in build.py.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd

from pipeline.common import haversine_m

SIZE = 256
MIN_LAT, MAX_LAT = 42.2320, 42.3956
MIN_LNG, MAX_LNG = -71.1847, -70.9633

LAT_STEP = (MAX_LAT - MIN_LAT) / SIZE
LNG_STEP = (MAX_LNG - MIN_LNG) / SIZE
_MID_LAT = (MIN_LAT + MAX_LAT) / 2
CELL_HEIGHT_M = haversine_m(MIN_LAT, MIN_LNG, MIN_LAT + LAT_STEP, MIN_LNG)
CELL_WIDTH_M = haversine_m(_MID_LAT, MIN_LNG, _MID_LAT, MIN_LNG + LNG_STEP)

Cell = tuple[int, int]


def latlng_to_cell(lat: float, lng: float) -> Cell | None:
    """(row, col) for a WGS84 point, or None when it falls outside the grid."""
    if not (MIN_LAT <= lat <= MAX_LAT and MIN_LNG <= lng <= MAX_LNG):
        return None
    row = min(int((MAX_LAT - lat) / LAT_STEP), SIZE - 1)
    col = min(int((lng - MIN_LNG) / LNG_STEP), SIZE - 1)
    return row, col


def cells_for(lat: pd.Series, lng: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized latlng_to_cell. Outside or missing points get -1."""
    la = lat.to_numpy(dtype=float)
    ln = lng.to_numpy(dtype=float)
    inside = (la >= MIN_LAT) & (la <= MAX_LAT) & (ln >= MIN_LNG) & (ln <= MAX_LNG)
    with np.errstate(invalid="ignore"):
        rows = np.minimum(((MAX_LAT - la) / LAT_STEP).astype(int, copy=False), SIZE - 1)
        cols = np.minimum(((ln - MIN_LNG) / LNG_STEP).astype(int, copy=False), SIZE - 1)
    rows = np.where(inside, rows, -1)
    cols = np.where(inside, cols, -1)
    return rows, cols


def cell_center(row: int, col: int) -> tuple[float, float]:
    """(lat, lng) of a cell's center."""
    return MAX_LAT - (row + 0.5) * LAT_STEP, MIN_LNG + (col + 0.5) * LNG_STEP


def line_cells(coords: Sequence[Sequence[float]]) -> set[Cell]:
    """Cells crossed by a polyline of (lng, lat) pairs, sampled at quarter-cell spacing."""
    out: set[Cell] = set()
    step = min(LAT_STEP, LNG_STEP) / 4
    for (x0, y0), (x1, y1) in zip(coords[:-1], coords[1:], strict=False):
        n = max(1, math.ceil(max(abs(x1 - x0), abs(y1 - y0)) / step))
        for i in range(n + 1):
            t = i / n
            cell = latlng_to_cell(y0 + (y1 - y0) * t, x0 + (x1 - x0) * t)
            if cell:
                out.add(cell)
    if len(coords) == 1:
        cell = latlng_to_cell(coords[0][1], coords[0][0])
        if cell:
            out.add(cell)
    return out


def geometry_cells(geometry: dict) -> list[list[int]]:
    """Sorted [row, col] cells touched by a GeoJSON Point / LineString / MultiLineString."""
    kind, coords = geometry["type"], geometry["coordinates"]
    lines: Iterable[Sequence[Sequence[float]]]
    if kind == "Point":
        lines = [[coords]]
    elif kind == "LineString":
        lines = [coords]
    elif kind == "MultiLineString":
        lines = coords
    else:
        raise ValueError(f"unsupported geometry type {kind}")
    cells: set[Cell] = set()
    for line in lines:
        cells |= line_cells(line)
    return [list(c) for c in sorted(cells)]


def describe() -> dict:
    """Grid metadata written next to the outputs."""
    return {
        "rows": SIZE, "cols": SIZE,
        "min_lat": MIN_LAT, "max_lat": MAX_LAT, "min_lng": MIN_LNG, "max_lng": MAX_LNG,
        "cell_height_m": round(CELL_HEIGHT_M, 2), "cell_width_m": round(CELL_WIDTH_M, 2),
        "origin": "row 0 = north edge, col 0 = west edge",
        "crs": "WGS84 (EPSG:4326)",
    }
