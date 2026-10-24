"""Shared paths, result type, and helpers for the data pipeline."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
EXTERNAL = RAW / "_external"
PROCESSED = ROOT / "data" / "processed"

# Sources that publish wall-clock time without an offset are Boston local time.
LOCAL_TZ = "America/New_York"
EARTH_RADIUS_M = 6_371_008.8
MPH_TO_KMH = 1.609344

_HAS_OFFSET = re.compile(r"(?:Z|[+-]\d{2}(?::?\d{2})?)$")


@dataclass
class Result:
    """What an adapter hands back to build.py.

    ``frame`` holds events or density rows (lat/lng but no grid cells yet).
    ``layers`` holds BASE features per layer name: dicts with ``geometry`` and
    ``properties`` (GeoJSON shape, no grid cells yet). build.py assigns cells,
    drops anything outside the grid, and records the counts.
    """

    name: str
    kind: str  # "events" | "density" | "base"
    rows_in: int
    frame: pd.DataFrame | None = None
    layers: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    dropped: Counter[str] = field(default_factory=Counter)
    unmapped: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    severity_rule: str = ""


def read_raw(dataset: str) -> pd.DataFrame:
    """Read data/raw/<dataset>/data.csv as strings (keeps ZIP codes and ids intact)."""
    return pd.read_csv(RAW / dataset / "data.csv", dtype=str, keep_default_na=False, na_values=[""])


def stable_id(*parts: Any) -> str:
    """Short deterministic id for sources that publish no record id."""
    key = "|".join("" if p is None or (isinstance(p, float) and math.isnan(p)) else str(p)
                   for p in parts)
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def to_utc(values: pd.Series, assume_tz: str = LOCAL_TZ) -> pd.Series:
    """Parse timestamps to tz-aware UTC.

    Strings that carry an offset are converted directly; naive strings are taken
    as ``assume_tz``. Ambiguous fall-back hours become NaT (the caller counts them).
    """
    s = values.astype("string").str.strip()
    aware = s.str.contains(_HAS_OFFSET, na=False)
    # "+00" is not ISO 8601; pandas wants "+00:00".
    fixed = s.str.replace(r"([+-]\d{2})$", r"\1:00", regex=True)
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns, UTC]")
    if aware.any():
        out[aware] = pd.to_datetime(fixed[aware], utc=True, errors="coerce", format="ISO8601")
    naive = ~aware & s.notna()
    if naive.any():
        local = pd.to_datetime(s[naive], errors="coerce", format="ISO8601")
        out[naive] = local.dt.tz_localize(
            assume_tz, ambiguous="NaT", nonexistent="shift_forward"
        ).dt.tz_convert("UTC")
    return out


def iso_utc(ts: pd.Series) -> pd.Series:
    """Format UTC timestamps as ISO 8601 strings ending in Z (NaT stays null)."""
    return ts.dt.strftime("%Y-%m-%dT%H:%M:%SZ").where(ts.notna(), None)


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in meters between two WGS84 points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def to_float(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce")


def snake(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
