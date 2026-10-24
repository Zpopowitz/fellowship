"""Hazards the swarm must reason about: fire (spreads) and flood (static water).

Pure functions so the dynamics can be property-tested (steering: keep world
logic pure). A hazard state is two bool grids over the map: ``fire`` and
``flood``. Fire grows outward into open cells each step; flood is fixed water
placed at reset. Both BLOCK movement and are DANGEROUS to enter.

Hazard seed cells come from the real-data SAR scenarios
(``fellowship/sar_dataset.py``) when the env is built with ``kind='sar'``, or
are placed procedurally for the floorplan/boston kinds so every map can carry a
situation.
"""
from __future__ import annotations

import numpy as np

# how far a drone "feels" danger (Chebyshev); used to build the danger feature
DANGER_RADIUS = 3


def _dilate(mask: np.ndarray) -> np.ndarray:
    """4-neighbour dilation of a boolean mask."""
    out = mask.copy()
    out[1:, :] |= mask[:-1, :]
    out[:-1, :] |= mask[1:, :]
    out[:, 1:] |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    return out


def spread_fire(fire: np.ndarray, open_grid: np.ndarray, rng: np.random.Generator,
                p: float = 0.35) -> np.ndarray:
    """One step of fire spread.

    Fire moves into 4-neighbour OPEN cells with probability ``p`` each. Returns a
    new fire grid (the old fire cells stay on fire). Deterministic given ``rng``.
    """
    fire = np.asarray(fire, dtype=bool)
    if not fire.any():
        return fire.copy()
    candidates = _dilate(fire) & open_grid & ~fire
    if not candidates.any():
        return fire.copy()
    draw = rng.random(fire.shape) < p
    new_fire = fire | (candidates & draw)
    return new_fire


def danger_field(hazard: np.ndarray, radius: int = DANGER_RADIUS) -> np.ndarray:
    """Per-cell danger in [0,1]: 1 on a hazard cell, decaying with Chebyshev
    distance out to ``radius`` (0 beyond). Built by repeated dilation so it needs
    no distance transform.
    """
    hazard = np.asarray(hazard, dtype=bool)
    field = hazard.astype(np.float64)
    if not hazard.any():
        return field
    reach = hazard.copy()
    for step in range(1, radius + 1):
        reach = _dilate(reach)
        val = 1.0 - step / (radius + 1)
        field = np.maximum(field, reach * val)
    return field


def block_grid(open_grid: np.ndarray, fire: np.ndarray, flood: np.ndarray) -> np.ndarray:
    """Cells a drone may stand on: open AND not on fire AND not flooded."""
    return np.asarray(open_grid, dtype=bool) & ~np.asarray(fire, bool) & ~np.asarray(flood, bool)


def place_procedural_hazards(open_grid: np.ndarray, rng: np.random.Generator,
                             n_fire_seeds: int = 1, flood_frac: float = 0.0
                             ) -> tuple[np.ndarray, np.ndarray]:
    """Fire/flood seed grids for a map with no real hazard data (floorplans).

    Places ``n_fire_seeds`` single-cell fires on random open cells, and floods a
    ``flood_frac`` fraction of open cells in one contiguous low corner (simple
    stand-in; real flood extent needs flood-zone data).
    """
    H, W = open_grid.shape
    fire = np.zeros((H, W), dtype=bool)
    flood = np.zeros((H, W), dtype=bool)
    ys, xs = np.nonzero(open_grid)
    if len(ys) == 0:
        return fire, flood
    cells = list(zip(ys.tolist(), xs.tolist()))

    for _ in range(n_fire_seeds):
        y, x = cells[int(rng.integers(0, len(cells)))]
        fire[y, x] = True

    if flood_frac > 0:
        # flood the cells closest to the bottom-right corner (a "low" area)
        order = sorted(cells, key=lambda c: -(c[0] + c[1]))
        n = int(flood_frac * len(cells))
        for (y, x) in order[:n]:
            flood[y, x] = True
    return fire, flood



# =====================================================================
# Sensor models: how a drone detects fire from a distance.
#
# Real SAR drones carry two complementary sensors, modelled here:
#
#   Thermal IR camera  -> sees HEAT directly, through smoke and in the dark,
#                         but needs line of sight: a wall blocks it. Medium
#                         range. Gives a precise fire location.
#   Gas / particulate  -> smells smoke, CO and fine particulate that DIFFUSE
#     sensor              outward from a fire and DRIFT downwind. Detects a fire
#                         earlier and from farther, even around a corner, but
#                         fuzzily (a direction and a "something is burning", not
#                         an exact cell).
#
# Each returns a per-cell confidence in [0,1] over what the drone would detect
# from its position. The env ORs the thermal hit into known_fire (precise) and
# keeps the gas field as an early-warning danger layer.
# =====================================================================

IR_RANGE = 6          # thermal camera reach (Chebyshev cells)
GAS_RANGE = 10        # smoke/particulate reach (diffuses farther than IR sees)


def _line_clear(grid_blocked: np.ndarray, y0: int, x0: int, y1: int, x1: int) -> bool:
    """True if nothing blocks the straight line from (y0,x0) to (y1,x1).

    ``grid_blocked`` is True on cells that stop IR (walls). Bresenham-style walk;
    the fire cell itself (endpoint) is allowed to be 'blocked' (it is the target).
    """
    dy = abs(y1 - y0)
    dx = abs(x1 - x0)
    sy = 1 if y0 < y1 else -1
    sx = 1 if x0 < x1 else -1
    err = dx - dy
    cy, cx = y0, x0
    while (cy, cx) != (y1, x1):
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
        if (cy, cx) == (y1, x1):
            break
        if grid_blocked[cy, cx]:
            return False
    return True


def thermal_ir_view(fire: np.ndarray, blocked: np.ndarray, pos, rng=None,
                    ir_range: int = IR_RANGE) -> np.ndarray:
    """Fire cells a drone at ``pos`` detects with its thermal IR camera.

    Returns a bool grid: True on each fire cell within ``ir_range`` (Chebyshev)
    that has clear line of sight (no wall between drone and fire). Walls block IR;
    smoke and darkness do not. ``rng`` is unused (IR is deterministic) but kept so
    all sensor functions share one signature.
    """
    fire = np.asarray(fire, dtype=bool)
    out = np.zeros_like(fire)
    if not fire.any():
        return out
    y, x = pos
    H, W = fire.shape
    y0, y1 = max(0, y - ir_range), min(H, y + ir_range + 1)
    x0, x1 = max(0, x - ir_range), min(W, x + ir_range + 1)
    for fy, fx in np.argwhere(fire[y0:y1, x0:x1]):
        fy, fx = int(fy) + y0, int(fx) + x0
        if max(abs(fy - y), abs(fx - x)) > ir_range:
            continue
        if _line_clear(blocked, y, x, fy, fx):
            out[fy, fx] = True
    return out


def gas_plume(fire: np.ndarray, pos, wind=(0, 0), gas_range: int = GAS_RANGE,
              rng=None) -> np.ndarray:
    """Smoke/particulate confidence a drone at ``pos`` would sense per cell.

    Models diffusion: each cell's reading grows with how much fire is nearby and
    shrinks with distance, out to ``gas_range``. ``wind`` = (dy, dx) biases the
    plume downwind, so a drone downwind of a fire smells it from farther. Returns
    a float grid in [0,1]. Fuzzy by design: it signals 'fire that way', not an
    exact cell.
    """
    fire = np.asarray(fire, dtype=bool)
    H, W = fire.shape
    out = np.zeros((H, W), dtype=np.float64)
    if not fire.any():
        return out
    y, x = pos
    wy, wx = wind
    for fy, fx in np.argwhere(fire):
        fy, fx = int(fy), int(fx)
        # downwind distance: subtract movement in the wind direction
        ddy = (fy - y) - wy
        ddx = (fx - x) - wx
        dist = max(abs(fy - y), abs(fx - x))
        if dist > gas_range:
            continue
        eff = (abs(ddy) + abs(ddx)) / 2.0  # wind-shifted distance
        val = max(0.0, 1.0 - eff / (gas_range + 1))
        # accumulate (more fire nearby -> stronger smell), clamp at 1
        out[y, x] = min(1.0, out[y, x] + val)
    # spread the reading as a small local field so the drone has a gradient
    field = out.copy()
    reach = out > 0
    for step in range(1, 4):
        reach = _dilate(reach)
        field = np.maximum(field, reach * (out.max() * (1.0 - step / 4.0)))
    return field
