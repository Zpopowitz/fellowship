"""Real-Boston search-and-rescue dataset for training the drone swarm.

This turns the standardized pipeline data (`data/processed/`) into training
*scenarios*: a 48x48 region cut from the REAL Boston street grid, with survivors
and hazards (fire, flood) placed where real incidents actually happened.

Why a separate module from ``maps.py``:
    ``maps.py`` crops the Moving AI ``boston_map.csv``. The pipeline's REPORT.md
    shows that map is NOT georeferenced (it did not line up with real streets),
    so real fire/flood coordinates cannot be placed on it. This module crops the
    pipeline's OWN 256x256 street-occupancy grid (``data/processed/base/grid.json``),
    which every event is already geocoded against, so hazards land in the right
    place relative to streets.

A scenario is fully determined by (seed): same seed -> same region, same
survivors, same hazards, everywhere. Train seeds are 0..3999, eval seeds 5000+,
exactly as in ``maps.py`` -- they never overlap.

Hazard placement is honest about resolution: fire incidents are geocoded by ZIP
centroid (no street coordinates exist in the feed), so fire RATE per area is real
but the exact cell is not. Survivors are biased toward high-fire areas, because
that is where a rescue swarm is dispatched; the bias strength is `hazard_pull`.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import numpy as np

from .maps import largest_component, REGION, TRAIN_SEED_MAX, EVAL_SEED_MIN

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GRID_JSON = os.path.join(REPO, "data", "processed", "base", "grid.json")
EVENTS_PARQUET = os.path.join(REPO, "data", "processed", "events.parquet")

GRID_SIZE = 256
MIN_OPEN_FRAC = 0.12  # street cells are sparse (~24% of the box); 0.12 keeps real blocks

# Hazard event types this dataset uses.
HAZARD_TYPES = ("hazard.fire", "hazard.flood", "water.flood_risk")


@dataclass
class HazardField:
    """Per-cell hazard weights over the full 256x256 grid, from real events."""

    fire: np.ndarray       # severity-weighted fire incidents per cell
    flood: np.ndarray      # severity-weighted flood incidents per cell
    loaded_from: str = ""
    counts: dict = field(default_factory=dict)

    @property
    def total(self) -> np.ndarray:
        return self.fire + self.flood


_GRID_CACHE: np.ndarray | None = None
_HAZARD_CACHE: HazardField | None = None


def load_street_grid() -> np.ndarray:
    """Load the pipeline's 256x256 street-occupancy grid (True = street cell)."""
    global _GRID_CACHE
    if _GRID_CACHE is not None:
        return _GRID_CACHE
    with open(GRID_JSON, encoding="utf-8") as fh:
        meta = json.load(fh)
    rows = meta["rows_data"]
    grid = np.array([[c == "1" for c in row] for row in rows], dtype=bool)
    _GRID_CACHE = grid
    return grid


def load_hazard_field() -> HazardField:
    """Build per-cell fire/flood weights from events.parquet (cached)."""
    global _HAZARD_CACHE
    if _HAZARD_CACHE is not None:
        return _HAZARD_CACHE
    import pandas as pd  # heavy import kept local

    df = pd.read_parquet(EVENTS_PARQUET, columns=["type", "cell_row", "cell_col", "severity"])
    fire = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
    flood = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
    counts: dict[str, int] = {}
    for etype, grp in df.groupby("type"):
        if etype not in HAZARD_TYPES:
            continue
        counts[etype] = int(len(grp))
        target = flood if "flood" in etype else fire
        rr = grp["cell_row"].to_numpy()
        cc = grp["cell_col"].to_numpy()
        w = grp["severity"].to_numpy(dtype=np.float32)
        inside = (rr >= 0) & (rr < GRID_SIZE) & (cc >= 0) & (cc < GRID_SIZE)
        np.add.at(target, (rr[inside], cc[inside]), w[inside])
    field_ = HazardField(fire=fire, flood=flood, loaded_from=EVENTS_PARQUET, counts=counts)
    _HAZARD_CACHE = field_
    return field_


def _crop_bounds(grid: np.ndarray, rng: np.random.Generator, size: int,
                 min_open_frac: float) -> tuple[int, int]:
    """Top-left (row, col) of a size x size crop with enough open cells."""
    H, W = grid.shape
    for _ in range(4000):
        y = int(rng.integers(0, H - size + 1))
        x = int(rng.integers(0, W - size + 1))
        if grid[y:y + size, x:x + size].mean() >= min_open_frac:
            return y, x
    best, best_frac = (0, 0), -1.0
    for _ in range(1000):
        y = int(rng.integers(0, H - size + 1))
        x = int(rng.integers(0, W - size + 1))
        frac = grid[y:y + size, x:x + size].mean()
        if frac > best_frac:
            best, best_frac = (y, x), frac
    return best


@dataclass
class SARScenario:
    """One training scenario on the real Boston grid."""

    seed: int
    open_grid: np.ndarray             # 48x48 bool, True = reachable open cell
    survivors: list                   # [(row, col)] cells, all reachable
    fire_cells: list                  # seed cells where fire starts (local coords)
    flood_cells: list
    origin: tuple                     # (row, col) of this crop in the 256x256 grid
    region_fire_total: float          # real fire weight summed over the crop
    region_flood_total: float

    @property
    def split(self) -> str:
        if 0 <= self.seed <= TRAIN_SEED_MAX:
            return "train"
        if self.seed >= EVAL_SEED_MIN:
            return "eval"
        return "reserved"


def sample_scenario(seed: int, *, n_survivors: int = 8, size: int = REGION,
                    hazard_pull: float = 3.0) -> SARScenario:
    """Deterministic SAR scenario for a seed, on the real Boston street grid.

    Survivors are placed on reachable open cells, biased toward cells near real
    fire/flood activity (``hazard_pull`` = how strongly; 0 = uniform). Fire and
    flood seed cells are the hazard cells inside the crop with real incidents.
    """
    grid = load_street_grid()
    haz = load_hazard_field()
    rng = np.random.default_rng(seed)

    y, x = _crop_bounds(grid, rng, size, MIN_OPEN_FRAC)
    sub = largest_component(grid[y:y + size, x:x + size])
    fire_sub = haz.fire[y:y + size, x:x + size] * sub
    flood_sub = haz.flood[y:y + size, x:x + size] * sub

    open_cells = np.argwhere(sub)
    if len(open_cells) == 0:
        return SARScenario(seed, sub, [], [], [], (y, x), 0.0, 0.0)

    haz_local = fire_sub + flood_sub
    haz_norm = haz_local / haz_local.max() if haz_local.max() > 0 else haz_local
    weights = 1.0 + hazard_pull * haz_norm[sub]
    weights = weights / weights.sum()

    k = min(n_survivors, len(open_cells))
    idx = rng.choice(len(open_cells), size=k, replace=False, p=weights)
    survivors = [(int(open_cells[i][0]), int(open_cells[i][1])) for i in idx]

    fire_cells = [(int(c[0]), int(c[1])) for c in np.argwhere(fire_sub > 0)]
    flood_cells = [(int(c[0]), int(c[1])) for c in np.argwhere(flood_sub > 0)]

    return SARScenario(
        seed=seed, open_grid=sub, survivors=survivors,
        fire_cells=fire_cells, flood_cells=flood_cells, origin=(y, x),
        region_fire_total=float(fire_sub.sum()), region_flood_total=float(flood_sub.sum()),
    )


def dataset_split(n_train: int = 4000, n_eval: int = 1000) -> dict:
    """Canonical train/eval seed lists. Never overlap (train < 4000 <= 5000 <= eval)."""
    train = list(range(0, n_train))
    eval_ = list(range(EVAL_SEED_MIN, EVAL_SEED_MIN + n_eval))
    assert max(train) < EVAL_SEED_MIN <= min(eval_), "train/eval seed overlap"
    return {"train": train, "eval": eval_}
