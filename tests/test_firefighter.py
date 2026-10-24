"""Tests for the firefighter objective and per-situation trained models."""
from __future__ import annotations

import numpy as np

from fellowship import policies
from fellowship.env import SwarmEnv


def test_firefighter_score_rewards_rescue_over_survival():
    """Saving a savable person must outweigh keeping a drone: the objective
    should prefer a rescue even at the cost of one drone."""
    env = SwarmEnv(kind="sar", hazards=True, sensing="ir_gas")
    env.reset(seed=7)
    # 2 rescued, 0 lost, 0 abandoned
    env.rescued[:2] = True
    env.disabled[:] = False
    s_rescue2 = env.score_firefighter()
    # 2 rescued but 1 drone lost: should still be high (a life > a drone)
    env.disabled[0] = True
    s_rescue2_lost1 = env.score_firefighter()
    # losing one drone costs far less than a rescue is worth
    assert s_rescue2 - s_rescue2_lost1 < 10.0  # w_drone_loss << w_rescue
    assert s_rescue2_lost1 > 0


def test_firefighter_penalizes_abandoning_reachable_survivor():
    env = SwarmEnv(kind="sar", hazards=True, sensing="ir_gas")
    env.reset(seed=7)
    base = env.score_firefighter()
    # put an unrescued survivor on a fire cell -> abandoned
    sy, sx = env.survivor_cells[0]
    env.fire[sy, sx] = True
    worse = env.score_firefighter()
    assert worse < base, "leaving a survivor to burn must lower the score"


def test_situation_models_are_distinct():
    w_in = policies.MODES["indoor"]
    w_out = policies.MODES["outdoor"]
    w_fl = policies.MODES["flood"]
    assert not np.allclose(w_in, w_out)
    assert not np.allclose(w_out, w_fl)


def test_auto_and_trained_policies_resolve():
    # auto picks indoor for a building kind
    assert policies.get_policy("auto", kind="office") is not None
    # trained falls back to hand-set if no weights file, else loads them
    p = policies.get_policy("trained", kind="sar")
    assert p is not None
    f = np.zeros((5, 9)); f[2, 2] = 5.0
    a = p(f, np.ones(5, dtype=bool), np.random.default_rng(0))
    assert 0 <= a < 5


def test_episode_metrics_include_firefighter_fields_with_hazards():
    env = SwarmEnv(kind="sar", hazards=True, sensing="ir_gas")
    obs, _ = env.reset(seed=7)
    pol = policies.get_policy("auto", kind="sar")
    rng = np.random.default_rng(0)
    for _ in range(10):
        if not env.agents:
            break
        acts = {a: pol(obs[a]["features"], obs[a]["mask"], rng) for a in env.agents}
        obs, _, term, _, _ = env.step(acts)
        if all(term.values()):
            break
    m = env.episode_metrics()
    assert "firefighter_score" in m and "abandoned" in m
