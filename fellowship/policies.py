"""Policies: random, rule-based, linear, and situation-aware. Shared interface:
    policy(features[5,9], mask[5], rng) -> action int.

The decision model is a linear policy over 9 per-action features:
    [new area, frontier progress, survivor progress, crowding, revisits, stay,
     fire danger, flood danger, survivor urgency]

Situation-dependent behaviour comes from the last three weights. A drone that
weights fire/flood danger strongly negative steers AROUND hazards; a positive
survivor-urgency weight makes it prioritise survivors trapped in danger. The
named MODES below are different standing strategies a commander could pick;
training (CEM) can also learn its own 9-weight vector.
"""
from __future__ import annotations

import numpy as np

# fixed rule-based weights (9):
# [new area, frontier, survivor, crowding, revisits, stay,
#  fire danger, flood danger, survivor urgency]
RULE_WEIGHTS = np.array([1.0, 0.5, 3.0, -0.5, 0.3, -1.0, -4.0, -2.5, 2.0], dtype=np.float64)

# Situation modes: same features, different priorities.
MODES: dict[str, np.ndarray] = {
    # avoid danger hard, still rescue the endangered; good default for fire
    "cautious": np.array([1.0, 0.5, 3.0, -0.5, 0.3, -1.0, -6.0, -4.0, 1.5]),
    # push toward survivors in danger, accept more risk (trained-rescue style)
    "aggressive": np.array([1.0, 0.6, 4.0, -0.6, 0.3, -1.2, -2.0, -1.5, 4.0]),
    # even trade-off
    "balanced": RULE_WEIGHTS,
    # hazard-blind baseline: ignores the 3 hazard features (old behaviour)
    "blind": np.array([1.0, 0.5, 3.0, -0.5, 0.3, -1.0, 0.0, 0.0, 0.0]),
}


def random_policy(features: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> int:
    legal = np.flatnonzero(mask)
    return int(rng.choice(legal))


def linear_policy_factory(weights: np.ndarray):
    w = np.asarray(weights, dtype=np.float64)

    def policy(features: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> int:
        f = features
        # tolerate a 6-feature observation with 9 weights (and vice versa)
        if f.shape[1] != w.shape[0]:
            n = min(f.shape[1], w.shape[0])
            scores = f[:, :n] @ w[:n]
        else:
            scores = f @ w
        scores = scores + rng.normal(0, 1e-6, size=scores.shape)  # tie-break noise
        scores = np.where(mask, scores, -np.inf)
        return int(np.argmax(scores))

    return policy


def rule_policy(features: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> int:
    return linear_policy_factory(RULE_WEIGHTS)(features, mask, rng)


def mode_policy(mode: str):
    """Policy for a named situation mode (cautious / aggressive / balanced / blind)."""
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode!r}; choose from {sorted(MODES)}")
    return linear_policy_factory(MODES[mode])


def get_policy(name: str, weights: np.ndarray | None = None):
    """Factory by name: 'random', 'rule', 'linear' (needs weights), or a mode name."""
    if name == "random":
        return random_policy
    if name == "rule":
        return rule_policy
    if name == "linear":
        if weights is None:
            raise ValueError("linear policy needs weights")
        return linear_policy_factory(weights)
    if name in MODES:
        return mode_policy(name)
    raise ValueError(f"unknown policy: {name!r}")
