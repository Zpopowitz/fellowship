"""Tests 9 & 10: floorplan invariants and determinism."""
import numpy as np
from hypothesis import given, settings, strategies as st

from fellowship.floorplans import generate_floorplan, FLOORPLAN_KINDS, SIZE, MIN_OPEN_FRAC


@settings(max_examples=40, deadline=None)
@given(kind=st.sampled_from(FLOORPLAN_KINDS), seed=st.integers(0, 3999))
def test_floorplan_invariants(kind, seed):
    """Test 9: closed outer wall, 48x48, >=40% open after damage."""
    g = generate_floorplan(kind, seed)
    assert g.shape == (SIZE, SIZE)
    assert not g[0, :].any()
    assert not g[-1, :].any()
    assert not g[:, 0].any()
    assert not g[:, -1].any()
    assert g.mean() >= MIN_OPEN_FRAC - 1e-9, f"{kind} seed {seed}: {g.mean():.3f} open"


@settings(max_examples=40, deadline=None)
@given(kind=st.sampled_from(FLOORPLAN_KINDS), seed=st.integers(0, 3999))
def test_floorplan_determinism(kind, seed):
    """Test 10: same (kind, seed) -> identical floorplan."""
    a = generate_floorplan(kind, seed)
    b = generate_floorplan(kind, seed)
    assert np.array_equal(a, b)
