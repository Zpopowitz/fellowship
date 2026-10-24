"""Test the benchmark harness returns the right shape on held-out maps."""
from __future__ import annotations

import numpy as np

from fellowship import policies
from fellowship.benchmark import evaluate_policy, EVAL_SEED0


def test_evaluate_policy_shape_and_heldout():
    pol = policies.get_policy("rule")
    r = evaluate_policy(pol, task="rescue", maps="buildings", n_maps=3)
    for key in ("rescued", "explored", "steps", "drones_lost", "survivors_in_hazard"):
        assert key in r and len(r[key]) == 2  # (mean, std)
    assert 0 <= r["rescued"][0] <= 8
    assert r["n_maps"] == 3


def test_evaluate_uses_heldout_seeds():
    # seeds must be >= 5000 (never training seeds)
    from fellowship.benchmark import eval_seeds
    assert min(eval_seeds(5, "buildings")) >= EVAL_SEED0


def test_random_worse_than_rule_on_rescue():
    rnd = evaluate_policy(policies.get_policy("random"), task="rescue",
                          maps="buildings", n_maps=4)
    rule = evaluate_policy(policies.get_policy("rule"), task="rescue",
                           maps="buildings", n_maps=4)
    assert rule["rescued"][0] > rnd["rescued"][0]
