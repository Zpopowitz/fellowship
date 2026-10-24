"""Radio-range communication: link robots into components and merge knowledge."""
from __future__ import annotations

import numpy as np

COMM = 10  # Chebyshev radio range in cells


def _cheby(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def link_components(positions: list[tuple[int, int]], comm: int = COMM,
                    active: list[bool] | np.ndarray | None = None) -> list[list[int]]:
    """Connected components of robots within Chebyshev `comm` (links chain).

    ``active`` (optional) marks which robots can relay: a robot with active[i]
    False (e.g. disabled by fire) links to no one and comes back as its own
    singleton group, so a dead drone neither relays maps nor adds to crowding.
    """
    n = len(positions)
    parent = list(range(n))
    if active is None:
        active = [True] * n

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        if not active[i]:
            continue
        for j in range(i + 1, n):
            if not active[j]:
                continue
            if _cheby(positions[i], positions[j]) <= comm:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def merge_maps(maps_stack: np.ndarray, members: list[int]) -> np.ndarray:
    """Cell-wise max over the members' knowledge maps (0 unknown/1 open/2 blocked).

    Returns the single merged map for the component. 'blocked' (2) beats 'open'
    (1) beats 'unknown' (0), which matches cell-wise max.
    """
    return np.max(maps_stack[members], axis=0)


def merge_sightings(sightings: list[set], members: list[int]) -> set:
    """Union of survivor-id sightings across component members."""
    out: set = set()
    for i in members:
        out |= sightings[i]
    return out
