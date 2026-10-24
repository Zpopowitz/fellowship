"""Boston grid loading and region cropping for Fellowship."""
from __future__ import annotations

import os
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BOSTON_CSV = os.path.join(REPO, "data", "boston_map.csv")

REGION = 48
BOSTON_SIZE = 256
MIN_OPEN_FRAC_BOSTON = 0.55

KINDS = ("boston", "home", "office", "datacenter", "factory")
MIXED = "mixed"

TRAIN_SEED_MAX = 3999  # inclusive
EVAL_SEED_MIN = 5000


def largest_component(open_grid: np.ndarray) -> np.ndarray:
    """Keep only the largest 4-connected open area; everything else blocked.

    Guarantees reachability of every open cell from any other open cell.
    """
    open_grid = np.asarray(open_grid, dtype=bool)
    if not open_grid.any():
        return open_grid.copy()
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    labels, n = ndimage.label(open_grid, structure=structure)
    if n <= 1:
        return open_grid.copy()
    sizes = ndimage.sum(np.ones_like(labels), labels, index=np.arange(1, n + 1))
    best = int(np.argmax(sizes)) + 1
    return labels == best


def load_boston() -> np.ndarray:
    """Load the 256x256 Boston grid (True=open). Generates data if missing."""
    if not os.path.exists(BOSTON_CSV):
        grid = _synthetic_boston()
        save_boston_csv(grid, BOSTON_CSV)
        return grid
    rows = np.loadtxt(BOSTON_CSV, delimiter=",", skiprows=1, dtype=int)
    grid = np.zeros((BOSTON_SIZE, BOSTON_SIZE), dtype=bool)
    ys = rows[:, 0]
    xs = rows[:, 1]
    op = rows[:, 2].astype(bool)
    grid[ys, xs] = op
    return grid


def save_boston_csv(grid: np.ndarray, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = grid.shape
    with open(path, "w", encoding="utf-8") as f:
        f.write("y,x,open\n")
        for y in range(h):
            for x in range(w):
                f.write(f"{y},{x},{int(bool(grid[y, x]))}\n")


def _synthetic_boston(size: int = BOSTON_SIZE) -> np.ndarray:
    """Deterministic synthetic 'city' street grid used when the Moving AI
    Boston_0_256 file is not present. Open = streets; blocked = building blocks.

    This is a stand-in so the repo runs offline; swap data/boston_map.csv for the
    real Moving AI grid (Sturtevant 2012) to use true Boston data.
    """
    rng = np.random.default_rng(1234)
    grid = np.zeros((size, size), dtype=bool)
    # Avenues (open streets) at irregular but deterministic spacing.
    y = 0
    while y < size:
        w = int(rng.integers(2, 4))
        grid[y:y + w, :] = True
        y += int(rng.integers(10, 20))
    x = 0
    while x < size:
        w = int(rng.integers(2, 4))
        grid[:, x:x + w] = True
        x += int(rng.integers(10, 20))
    # Diagonal-ish main roads for variety: a few wandering open paths.
    for _ in range(6):
        cy = int(rng.integers(0, size))
        cx = int(rng.integers(0, size))
        for _ in range(size):
            grid[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2] = True
            cy = int(np.clip(cy + rng.integers(-1, 2), 0, size - 1))
            cx = int(np.clip(cx + rng.integers(-1, 2), 0, size - 1))
    # Small plazas / open lots.
    for _ in range(40):
        py = int(rng.integers(0, size - 8))
        px = int(rng.integers(0, size - 8))
        s = int(rng.integers(3, 8))
        grid[py:py + s, px:px + s] = True
    return grid


def crop_region(grid: np.ndarray, seed: int, size: int = REGION,
                min_open_frac: float = MIN_OPEN_FRAC_BOSTON) -> np.ndarray:
    """Random `size`x`size` crop with >= min_open_frac open cells, largest comp."""
    rng = np.random.default_rng(seed)
    H, W = grid.shape
    for _ in range(2000):
        y = int(rng.integers(0, H - size + 1))
        x = int(rng.integers(0, W - size + 1))
        sub = grid[y:y + size, x:x + size]
        if sub.mean() >= min_open_frac:
            comp = largest_component(sub)
            if comp.mean() >= min_open_frac * 0.9:
                return comp.copy()
    # Fallback: densest crop found.
    best, best_frac = None, -1.0
    rng = np.random.default_rng(seed + 1)
    for _ in range(500):
        y = int(rng.integers(0, H - size + 1))
        x = int(rng.integers(0, W - size + 1))
        sub = largest_component(grid[y:y + size, x:x + size])
        if sub.mean() > best_frac:
            best, best_frac = sub.copy(), sub.mean()
    return best


def sample_map(kind: str, seed: int) -> np.ndarray:
    """Deterministic 48x48 open-grid (True=open) for a map kind and seed."""
    from . import floorplans  # local import to avoid cycle

    if kind == MIXED:
        pick = KINDS[np.random.default_rng(seed).integers(0, len(KINDS))]
        return sample_map(pick, seed)
    if kind == "boston":
        return crop_region(load_boston(), seed)
    if kind in ("home", "office", "datacenter", "factory"):
        return floorplans.generate_floorplan(kind, seed)
    raise ValueError(f"unknown map kind: {kind!r}")


def is_train_seed(seed: int) -> bool:
    return 0 <= seed <= TRAIN_SEED_MAX


def is_eval_seed(seed: int) -> bool:
    return seed >= EVAL_SEED_MIN
