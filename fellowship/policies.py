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

    # ---- situation-specific models (different behaviour per environment) ----
    # INDOOR (home/office/datacenter/factory): rooms are small and connect by
    # narrow corridors, radio dies through walls, and a fire fills a room with
    # one exit fast. So: don't over-spread (low crowding penalty), push HARD
    # into frontiers to clear room-by-room, very fire-cautious, and penalise
    # revisits strongly (backtracking in a corridor wastes the episode).
    "indoor": np.array([1.2, 1.8, 3.2, -0.2, 0.9, -1.2, -7.0, -3.0, 2.5]),
    # OUTDOOR / street (Boston, SAR): open grid, long sightlines, radio carries
    # far. So: spread out aggressively (high crowding penalty), chase new area,
    # fire-cautious but less cornered than indoors.
    "outdoor": np.array([1.4, 0.6, 3.0, -1.1, 0.3, -1.0, -4.0, -2.5, 2.0]),
    # FLOOD-dominant: water blocks whole runs of cells; frontier progress and
    # rerouting matter more than danger-dodging (flood is static, not spreading).
    "flood": np.array([1.2, 1.0, 3.2, -0.6, 0.4, -1.0, -2.0, -5.0, 2.2]),
}

# Which model fits which env map kind (used by situation_for / mode='auto').
SITUATION_BY_KIND: dict[str, str] = {
    "home": "indoor", "office": "indoor", "datacenter": "indoor", "factory": "indoor",
    "boston": "outdoor", "sar": "outdoor", "mixed": "balanced",
}


def situation_for(kind: str) -> str:
    """Name of the decision model that fits a given map kind."""
    return SITUATION_BY_KIND.get(kind, "balanced")


import json as _json
import os as _os

_WEIGHTS_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                             "results")


def load_trained(situation: str) -> np.ndarray | None:
    """Load a CEM-trained per-situation weight vector from
    results/weights_<situation>.json, or None if it hasn't been trained yet."""
    path = _os.path.join(_WEIGHTS_DIR, f"weights_{situation}.json")
    if not _os.path.exists(path):
        return None
    data = _json.load(open(path))
    w = np.asarray(data["weights"], dtype=np.float64)
    return w


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


def get_policy(name: str, weights: np.ndarray | None = None, kind: str | None = None):
    """Factory by name.

    'random', 'rule', 'linear' (needs weights), a mode name (cautious /
    aggressive / balanced / blind / indoor / outdoor / flood), or 'auto' to
    pick the situation model that fits ``kind`` (e.g. kind='office' -> indoor).
    """
    if name == "random":
        return random_policy
    if name == "rule":
        return rule_policy
    if name == "linear":
        if weights is None:
            raise ValueError("linear policy needs weights")
        return linear_policy_factory(weights)
    if name == "auto":
        return mode_policy(situation_for(kind or "mixed"))
    if name == "trained":
        sit = situation_for(kind or "mixed")
        w = load_trained(sit)
        if w is None:
            return mode_policy(sit)  # fall back to hand-set model
        return linear_policy_factory(w)
    if name in MODES:
        return mode_policy(name)
    raise ValueError(f"unknown policy: {name!r}")
