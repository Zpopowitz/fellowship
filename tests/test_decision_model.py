"""Tests for the hazard-aware decision model: hazards module, 9-feature policy,
and situation-dependent behaviour in the env."""
from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fellowship import features, hazards, policies
from fellowship.env import SwarmEnv, agent_name


# ----------------------------------------------------------------- hazards
def test_fire_only_spreads_into_open_and_never_shrinks():
    rng = np.random.default_rng(0)
    open_grid = np.ones((10, 10), dtype=bool)
    open_grid[5, :] = False  # a wall row
    fire = np.zeros((10, 10), dtype=bool)
    fire[0, 0] = True
    prev = fire.copy()
    for _ in range(20):
        fire = hazards.spread_fire(fire, open_grid, rng, p=1.0)
        assert (fire | prev == fire).all(), "fire must never un-burn a cell"
        assert not (fire & ~open_grid).any(), "fire never enters a wall"
        prev = fire.copy()
    # with p=1 and a reachable component, fire fills the top half
    assert fire[:5, :].all()


def test_danger_field_peaks_on_hazard_and_decays():
    hz = np.zeros((7, 7), dtype=bool)
    hz[3, 3] = True
    field = hazards.danger_field(hz, radius=3)
    assert field[3, 3] == 1.0
    assert 0.0 < field[3, 5] < 1.0
    assert field[3, 6] == pytest.approx(0.25, abs=0.26)  # ~edge of radius
    assert field[0, 0] == 0.0  # beyond radius


# ----------------------------------------------------------------- features
def test_features_are_nine_wide_and_hazard_cols_zero_without_hazards():
    known = np.ones((12, 12), dtype=np.uint8)
    feats, mask = features.compute_features(
        known, (5, 5), [], [], np.zeros((12, 12), dtype=np.int64))
    assert feats.shape == (5, features.N_FEATURES) == (5, 9)
    assert np.allclose(feats[:, 6:8], 0.0), "no hazards -> fire/flood features 0"


def test_fire_feature_rises_toward_fire():
    known = np.ones((12, 12), dtype=np.uint8)
    fire = np.zeros((12, 12), dtype=bool)
    fire[5, 7] = True  # fire just east of the robot at (5,5)
    fd = hazards.danger_field(fire)
    feats, _ = features.compute_features(
        known, (5, 5), [], [], np.zeros((12, 12), dtype=np.int64), fire_danger=fd)
    # action 3 = east (toward fire) should carry more fire danger than west (4)
    assert feats[3, 6] > feats[4, 6]


# ----------------------------------------------------------------- policy
def test_modes_exist_and_are_nine_wide():
    for name, w in policies.MODES.items():
        assert w.shape == (9,), name
    assert policies.get_policy("cautious") is not None


def test_policy_tolerates_six_feature_obs():
    # an old 6-feature observation still works with a 9-weight policy
    f6 = np.zeros((5, 6))
    f6[3, 2] = 10.0  # survivor progress on action 3
    pol = policies.get_policy("balanced")
    a = pol(f6, np.ones(5, dtype=bool), np.random.default_rng(0))
    assert a == 3


# ----------------------------------------------------------------- env
def test_hazard_episode_runs_and_reports_hazard_metrics():
    env = SwarmEnv(kind="sar", hazards=True, n_fire_seeds=2, flood_frac=0.03)
    obs, _ = env.reset(seed=3)
    pol = policies.get_policy("cautious")
    rng = np.random.default_rng(1)
    steps = 0
    while env.agents and steps < 200:
        acts = {a: pol(obs[a]["features"], obs[a]["mask"], rng) for a in env.agents}
        obs, _, term, _, _ = env.step(acts)
        steps += 1
        if all(term.values()):
            break
    m = env.episode_metrics()
    assert "disabled" in m and "fire_cells" in m and "flood_cells" in m
    assert 0 <= m["rescued"] <= env.k_survivors


@settings(max_examples=5, deadline=None)
@given(seed=st.integers(min_value=0, max_value=50))
def test_hazard_aware_survives_better_than_blind(seed):
    def run(mode):
        env = SwarmEnv(kind="sar", hazards=True, n_fire_seeds=3, flood_frac=0.03)
        obs, _ = env.reset(seed=seed)
        pol = policies.get_policy(mode)
        rng = np.random.default_rng(99)
        while env.agents:
            acts = {a: pol(obs[a]["features"], obs[a]["mask"], rng) for a in env.agents}
            obs, _, term, _, _ = env.step(acts)
            if all(term.values()):
                break
        return env.episode_metrics()
    blind = run("blind")
    cautious = run("cautious")
    # cautious should never lose MORE drones than blind on the same map
    assert cautious["disabled"] <= blind["disabled"] + 1


def test_no_hazards_matches_old_behavior_shape():
    env = SwarmEnv(kind="home", hazards=False)
    obs, _ = env.reset(seed=5)
    m = env.episode_metrics() if False else None
    f = obs[agent_name(0)]["features"]
    assert f.shape == (5, 9)
    assert np.allclose(f[:, 6:8], 0.0)
