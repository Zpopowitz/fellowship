"""Property tests for the real-Boston SAR training dataset."""
from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from scipy import ndimage

from fellowship import sar_dataset as sar

_STRUCT = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)


def _one_component_containing(grid: np.ndarray, cells: list) -> bool:
    """True if every cell is open and all share one connected component."""
    if not cells:
        return True
    labels, _ = ndimage.label(grid, structure=_STRUCT)
    seen = set()
    for r, c in cells:
        if not grid[r, c]:
            return False
        seen.add(int(labels[r, c]))
    return len(seen) == 1 and 0 not in seen


@settings(max_examples=25, deadline=None)
@given(seed=st.integers(min_value=0, max_value=3999))
def test_survivors_reachable_and_on_open_cells(seed):
    sc = sar.sample_scenario(seed)
    assert _one_component_containing(sc.open_grid, sc.survivors)


@settings(max_examples=25, deadline=None)
@given(seed=st.integers(min_value=0, max_value=9000))
def test_deterministic_per_seed(seed):
    a = sar.sample_scenario(seed)
    b = sar.sample_scenario(seed)
    assert a.survivors == b.survivors
    assert a.fire_cells == b.fire_cells
    assert a.origin == b.origin
    assert np.array_equal(a.open_grid, b.open_grid)


@settings(max_examples=20, deadline=None)
@given(seed=st.integers(min_value=0, max_value=3999),
       k=st.integers(min_value=1, max_value=12))
def test_survivor_count_and_region_shape(seed, k):
    sc = sar.sample_scenario(seed, n_survivors=k)
    assert sc.open_grid.shape == (sar.REGION, sar.REGION)
    assert len(sc.survivors) <= k
    # survivors are distinct cells
    assert len(set(sc.survivors)) == len(sc.survivors)


def test_train_eval_split_never_overlaps():
    sp = sar.dataset_split()
    assert set(sp["train"]).isdisjoint(sp["eval"])
    assert max(sp["train"]) < sar.EVAL_SEED_MIN <= min(sp["eval"])


def test_split_label_matches_seed():
    assert sar.sample_scenario(0).split == "train"
    assert sar.sample_scenario(3999).split == "train"
    assert sar.sample_scenario(5000).split == "eval"
    assert sar.sample_scenario(4500).split == "reserved"


def test_hazard_field_has_real_fire():
    haz = sar.load_hazard_field()
    assert haz.counts.get("hazard.fire", 0) > 1000, "fire events missing from events.parquet"
    assert haz.fire.sum() > 0


@settings(max_examples=15, deadline=None)
@given(seed=st.integers(min_value=0, max_value=3999))
def test_hazard_cells_are_inside_region(seed):
    sc = sar.sample_scenario(seed)
    for r, c in sc.fire_cells + sc.flood_cells:
        assert 0 <= r < sar.REGION and 0 <= c < sar.REGION
