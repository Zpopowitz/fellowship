"""Procedural damaged-building floorplan generator for Fellowship.

Every floorplan is 48x48, True=open. A 1-cell outer wall is always closed.
Kinds: home, office, datacenter, factory. Damage adds rubble, then the largest
4-connected open area is kept so every open cell is reachable.
"""
from __future__ import annotations

import os
import numpy as np

from .maps import largest_component, REGION

SIZE = REGION  # 48
MIN_OPEN_FRAC = 0.40
N_RUBBLE = 6
FLOORPLAN_KINDS = ("home", "office", "datacenter", "factory")


def _blank() -> np.ndarray:
    """All-open grid with a closed 1-cell outer wall."""
    g = np.ones((SIZE, SIZE), dtype=bool)
    g[0, :] = False
    g[-1, :] = False
    g[:, 0] = False
    g[:, -1] = False
    return g


def _doorway(g: np.ndarray, wall_cells: list[tuple[int, int]], rng, width: int = 2):
    """Open a doorway of `width` along a listed wall (middle if too short)."""
    if not wall_cells:
        return
    n = len(wall_cells)
    if n <= width:
        mid = n // 2
        y, x = wall_cells[mid]
        g[y, x] = True
        return
    start = int(rng.integers(0, n - width + 1))
    for k in range(start, start + width):
        y, x = wall_cells[k]
        g[y, x] = True


# ---------------------------------------------------------------- home
def gen_home(rng) -> np.ndarray:
    g = _blank()

    def split(y0, x0, y1, x1, depth):
        h = y1 - y0
        w = x1 - x0
        if depth >= 5 or (h < 12 and w < 12):
            return
        vertical = w >= h  # split the longer side
        if vertical:
            if w < 12:
                return
            lo, hi = x0 + 5, x1 - 5
            if hi <= lo:
                return
            xs = int(rng.integers(lo, hi))
            g[y0:y1, xs] = False
            wall = [(y, xs) for y in range(y0, y1)]
            _doorway(g, wall, rng)
            split(y0, x0, y1, xs, depth + 1)
            split(y0, xs + 1, y1, x1, depth + 1)
        else:
            if h < 12:
                return
            lo, hi = y0 + 5, y1 - 5
            if hi <= lo:
                return
            ys = int(rng.integers(lo, hi))
            g[ys, x0:x1] = False
            wall = [(ys, x) for x in range(x0, x1)]
            _doorway(g, wall, rng)
            split(y0, x0, ys, x1, depth + 1)
            split(ys + 1, x0, y1, x1, depth + 1)

    split(1, 1, SIZE - 1, SIZE - 1, 0)
    return g


# ---------------------------------------------------------------- office
def gen_office(rng) -> np.ndarray:
    g = _blank()
    # Central 3-wide corridor rows 20..27 region; use rows 22,23,24 as corridor,
    # with walls at 21 and 25 (so corridor interior is 22-24 → 3 wide).
    cor_top, cor_bot = 22, 24
    g[cor_top - 1, 1:SIZE - 1] = False  # top wall of corridor
    g[cor_bot + 1, 1:SIZE - 1] = False  # bottom wall of corridor

    def rooms(y0, y1, wall_row):
        x = 2
        while x < SIZE - 2:
            w = int(rng.integers(6, 13))
            x_end = min(x + w, SIZE - 2)
            if x_end - 1 > x:
                g[y0:y1, x_end - 1] = False  # room separator wall
            # door onto corridor at this room's span
            door_cols = list(range(x, x_end - 1))
            if door_cols:
                dstart = int(rng.integers(min(door_cols), max(door_cols) + 1))
                for dx in (dstart, min(dstart + 1, x_end - 2)):
                    g[wall_row, dx] = True
            x = x_end
    rooms(1, cor_top - 1, cor_top - 1)
    rooms(cor_bot + 2, SIZE - 1, cor_bot + 1)

    if rng.random() < 0.5:  # cross corridor
        cx = int(rng.integers(12, SIZE - 12))
        g[1:SIZE - 1, cx:cx + 3] = True
    return g


# ---------------------------------------------------------------- datacenter
def gen_datacenter(rng) -> np.ndarray:
    g = _blank()
    y = 3
    rack_rows = []
    while y < SIZE - 5:
        g[y:y + 2, 4:44] = False  # rack 2 thick
        rack_rows.append(y)
        aisle = int(rng.integers(2, 4))
        y += 2 + aisle
    # two cross aisles cutting all rows
    if rack_rows:
        c1 = int(rng.integers(8, 20))
        c2 = int(rng.integers(26, 40))
        for cx in (c1, c2):
            g[1:SIZE - 1, cx:cx + 2] = True
    # electrical room top-right corner
    g[2:12, 34:44] = True
    g[2:12, 33] = False
    g[12, 33:44] = False
    g[1:12, 44 if 44 < SIZE - 1 else SIZE - 2] = False
    # door into an aisle (bottom wall of electrical room)
    g[12, int(rng.integers(34, 43))] = True
    return g


# ---------------------------------------------------------------- factory
def gen_factory(rng) -> np.ndarray:
    g = _blank()
    # pillars every 10 cells
    for py in range(5, SIZE - 2, 10):
        for px in range(5, SIZE - 2, 10):
            g[py, px] = False
    # 5..8 machines
    for _ in range(int(rng.integers(5, 9))):
        mh = int(rng.integers(3, 7))
        mw = int(rng.integers(4, 10))
        my = int(rng.integers(2, SIZE - 2 - mh))
        mx = int(rng.integers(2, SIZE - 2 - mw))
        g[my:my + mh, mx:mx + mw] = False
    # one long conveyor line with 3 two-cell gaps
    row = int(rng.integers(10, SIZE - 10))
    g[row, 2:SIZE - 2] = False
    span = list(range(2, SIZE - 2))
    for gap_start in rng.choice(span[:-2], size=3, replace=False):
        g[row, int(gap_start):int(gap_start) + 2] = True
    return g


_GENERATORS = {
    "home": gen_home,
    "office": gen_office,
    "datacenter": gen_datacenter,
    "factory": gen_factory,
}


def damage(g: np.ndarray, rng) -> np.ndarray:
    """Add N_RUBBLE circular rubble piles (r 1..3); keep largest component.

    Redraw the damage step if the result is < MIN_OPEN_FRAC open.
    """
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    for _ in range(40):  # bounded retries on the damage draw
        d = g.copy()
        for _ in range(N_RUBBLE):
            cy = int(rng.integers(2, SIZE - 2))
            cx = int(rng.integers(2, SIZE - 2))
            r = int(rng.integers(1, 4))
            mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r
            d[mask] = False
        d = largest_component(d)
        if d.mean() >= MIN_OPEN_FRAC:
            return d
    return largest_component(g)  # give up: undamaged largest comp


def generate_floorplan(kind: str, seed: int) -> np.ndarray:
    """Deterministic 48x48 damaged floorplan for (kind, seed)."""
    if kind not in _GENERATORS:
        raise ValueError(f"unknown floorplan kind: {kind!r}")
    rng = np.random.default_rng(hash((kind, int(seed))) & 0xFFFFFFFF)
    g = _GENERATORS[kind](rng)
    g = largest_component(g)
    g = damage(g, rng)
    # enforce closed outer wall even after component filter
    g[0, :] = g[-1, :] = g[:, 0] = g[:, -1] = False
    g = largest_component(g)
    return g


def load_png_floorplans(root: str | None = None) -> dict[str, list[np.ndarray]]:
    """Load optional pre-made PNG packs under data/floorplans/<kind>/NNN.png."""
    from PIL import Image
    if root is None:
        root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "floorplans")
    out: dict[str, list[np.ndarray]] = {}
    if not os.path.isdir(root):
        return out
    for kind in FLOORPLAN_KINDS:
        kdir = os.path.join(root, kind)
        if not os.path.isdir(kdir):
            continue
        maps = []
        for fn in sorted(os.listdir(kdir)):
            if fn.lower().endswith(".png"):
                im = Image.open(os.path.join(kdir, fn)).convert("L").resize((SIZE, SIZE))
                arr = np.asarray(im) > 127  # white=open
                maps.append(largest_component(arr))
        if maps:
            out[kind] = maps
    return out


def floorplans_preview(path: str, seed0: int = 0) -> str:
    """Grid of 6 examples of each kind → results/floorplans_preview.png."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    kinds = FLOORPLAN_KINDS
    cols = 6
    fig, axes = plt.subplots(len(kinds), cols, figsize=(cols * 1.6, len(kinds) * 1.6))
    for r, kind in enumerate(kinds):
        for c in range(cols):
            g = generate_floorplan(kind, seed0 + r * 100 + c)
            ax = axes[r, c]
            ax.imshow(~g, cmap="gray", vmin=0, vmax=1)
            ax.set_xticks([]); ax.set_yticks([])
            if c == 0:
                ax.set_ylabel(kind, fontsize=9)
    fig.suptitle("Fellowship — procedural damaged floorplans", fontsize=11)
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
