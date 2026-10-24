"""Per-action features for the swarm policy, computed from a robot's own
knowledge (its map + linked teammates). Pure functions where possible.
"""
from __future__ import annotations

import numpy as np

# action id -> (dy, dx): 0 stay, 1 N, 2 S, 3 E, 4 W
DELTAS = np.array([[0, 0], [-1, 0], [1, 0], [0, 1], [0, -1]], dtype=int)
N_ACTIONS = 5
N_FEATURES = 9
DIST_CAP = 40


def bfs_distance(passable: np.ndarray, sources: np.ndarray, cap: int = DIST_CAP) -> np.ndarray:
    """Multi-source BFS distance via iterated 4-neighbour dilation (numpy).

    passable: bool [H,W] cells we may stand on/pass through.
    sources:  bool [H,W] starting cells (distance 0).
    Returns int [H,W]; unreachable cells = cap.
    """
    H, W = passable.shape
    dist = np.full((H, W), cap, dtype=np.int32)
    frontier = sources & passable
    dist[frontier] = 0
    cur = frontier.copy()
    for d in range(1, cap):
        nxt = np.zeros_like(cur)
        nxt[1:, :] |= cur[:-1, :]
        nxt[:-1, :] |= cur[1:, :]
        nxt[:, 1:] |= cur[:, :-1]
        nxt[:, :-1] |= cur[:, 1:]
        nxt &= passable
        nxt &= dist == cap  # only newly reached
        if not nxt.any():
            break
        dist[nxt] = d
        cur = nxt
    return dist


def frontier_mask(known: np.ndarray) -> np.ndarray:
    """Known-open cells (==1) adjacent to an unknown cell (==0)."""
    open_cells = known == 1
    unknown = known == 0
    nbr_unknown = np.zeros_like(unknown)
    nbr_unknown[1:, :] |= unknown[:-1, :]
    nbr_unknown[:-1, :] |= unknown[1:, :]
    nbr_unknown[:, 1:] |= unknown[:, :-1]
    nbr_unknown[:, :-1] |= unknown[:, 1:]
    return open_cells & nbr_unknown


def _passable_for_planning(known: np.ndarray) -> np.ndarray:
    """Unknown (0) and open (1) are passable; blocked (2) is not."""
    return known != 2


def legal_mask(known: np.ndarray, pos: tuple[int, int]) -> np.ndarray:
    """mask[a] True if action a is legal (on-map and target not known-blocked)."""
    H, W = known.shape
    y, x = pos
    mask = np.zeros(N_ACTIONS, dtype=bool)
    for a in range(N_ACTIONS):
        ty, tx = y + DELTAS[a, 0], x + DELTAS[a, 1]
        if a == 0:  # stay is always legal
            mask[a] = True
            continue
        if 0 <= ty < H and 0 <= tx < W and known[ty, tx] != 2:
            mask[a] = True
    return mask


def compute_features(known: np.ndarray, pos: tuple[int, int],
                     teammate_pos: list[tuple[int, int]],
                     survivors_known: list[tuple[int, int]],
                     visits: np.ndarray,
                     fire_danger: np.ndarray | None = None,
                     flood_danger: np.ndarray | None = None):
    """Return (features[5,9], mask[5]) for a robot.

    known: uint8 [H,W] robot's merged knowledge map.
    survivors_known: known, unrescued survivor cells.
    visits: int [H,W] visit counts for THIS robot.
    fire_danger / flood_danger: float [H,W] in [0,1], the robot's own knowledge
        of fire/flood danger per cell (0 everywhere when no hazards are sensed).
        When both are None the last three features are 0, so a 6-feature policy
        reads the same as before.

    Features (per action):
        f0 new area, f1 frontier progress, f2 survivor progress, f3 crowding,
        f4 revisits, f5 stay, f6 fire danger at target, f7 flood danger at
        target, f8 survivor urgency (progress toward a survivor weighted by how
        much danger that survivor sits in).
    """
    H, W = known.shape
    y, x = pos
    mask = legal_mask(known, pos)
    feats = np.zeros((N_ACTIONS, N_FEATURES), dtype=np.float64)

    passable = _passable_for_planning(known)
    if fire_danger is None:
        fire_danger = np.zeros((H, W), dtype=np.float64)
    if flood_danger is None:
        flood_danger = np.zeros((H, W), dtype=np.float64)

    # frontier distance field from all frontiers
    fmask = frontier_mask(known)
    fdist = bfs_distance(passable, fmask) if fmask.any() else None

    # survivor distance field from all known unrescued survivors
    if survivors_known:
        smask = np.zeros((H, W), dtype=bool)
        for (sy, sx) in survivors_known:
            smask[sy, sx] = True
        sdist = bfs_distance(passable, smask)
        # urgency distance: survivors sitting in danger pull harder. Weight each
        # survivor source by (1 + danger there); approximated by a danger-biased
        # second field that only lights up near dangerous survivors.
        danger_here = fire_danger + flood_danger
        urgent = [(sy, sx) for (sy, sx) in survivors_known if danger_here[sy, sx] > 0.0]
        if urgent:
            umask = np.zeros((H, W), dtype=bool)
            for (sy, sx) in urgent:
                umask[sy, sx] = True
            udist = bfs_distance(passable, umask)
        else:
            udist = None
    else:
        sdist = None
        udist = None

    def dist_at(field, cy, cx):
        if field is None:
            return DIST_CAP
        return int(field[cy, cx])

    cur_fd = dist_at(fdist, y, x)
    cur_sd = dist_at(sdist, y, x)
    cur_ud = dist_at(udist, y, x)

    for a in range(N_ACTIONS):
        ty, tx = y + DELTAS[a, 0], x + DELTAS[a, 1]
        if not (0 <= ty < H and 0 <= tx < W):
            ty, tx = y, x  # off-map handled by mask; keep indices valid

        # f0 new area: unknown cells in 5x5 around target / 25
        y0, y1 = max(0, ty - 2), min(H, ty + 3)
        x0, x1 = max(0, tx - 2), min(W, tx + 3)
        win = known[y0:y1, x0:x1]
        feats[a, 0] = float((win == 0).sum()) / 25.0

        # f1 frontier progress: cur - target
        feats[a, 1] = (cur_fd - dist_at(fdist, ty, tx)) if fdist is not None else 0.0

        # f2 survivor progress
        feats[a, 2] = (cur_sd - dist_at(sdist, ty, tx)) if sdist is not None else 0.0

        # f3 crowding: sum over teammates max(0, 5 - cheby(mate, target)) / 5
        crowd = 0.0
        for (my, mx) in teammate_pos:
            crowd += max(0, 5 - max(abs(my - ty), abs(mx - tx)))
        feats[a, 3] = crowd / 5.0

        # f4 revisits: -log(1 + visits[target])
        feats[a, 4] = -np.log1p(float(visits[ty, tx]))

        # f5 stay
        feats[a, 5] = 1.0 if a == 0 else 0.0

        # f6 fire danger at target cell (0 when no fire sensed)
        feats[a, 6] = float(fire_danger[ty, tx])

        # f7 flood danger at target cell
        feats[a, 7] = float(flood_danger[ty, tx])

        # f8 survivor urgency: progress toward a survivor that sits in danger
        feats[a, 8] = (cur_ud - dist_at(udist, ty, tx)) if udist is not None else 0.0

    return feats, mask
