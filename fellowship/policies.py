"""Policies: random, rule-based, linear. Shared interface:
    policy(features[5,6], mask[5], rng) -> action int.
"""
from __future__ import annotations

import numpy as np

# fixed rule-based weights:
# [new area, frontier progress, survivor progress, crowding, revisits, stay]
RULE_WEIGHTS = np.array([1.0, 0.5, 3.0, -0.5, 0.3, -1.0], dtype=np.float64)


def random_policy(features: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> int:
    legal = np.flatnonzero(mask)
    return int(rng.choice(legal))


def linear_policy_factory(weights: np.ndarray):
    w = np.asarray(weights, dtype=np.float64)

    def policy(features: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> int:
        scores = features @ w
        scores = scores + rng.normal(0, 1e-6, size=scores.shape)  # tie-break noise
        scores = np.where(mask, scores, -np.inf)
        return int(np.argmax(scores))

    return policy


def rule_policy(features: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> int:
    return linear_policy_factory(RULE_WEIGHTS)(features, mask, rng)


def get_policy(name: str, weights: np.ndarray | None = None):
    """Factory by name: 'random', 'rule', or 'linear' (needs weights)."""
    if name == "random":
        return random_policy
    if name == "rule":
        return rule_policy
    if name == "linear":
        if weights is None:
            raise ValueError("linear policy needs weights")
        return linear_policy_factory(weights)
    raise ValueError(f"unknown policy: {name!r}")
