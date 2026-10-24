"""Benchmark harness for Fellowship Gym.

``evaluate_policy(policy_fn, task, maps, n_maps)`` runs a policy on the fixed
HELD-OUT maps (seeds 5000+) for a (task, map family) and returns mean +/- std of
rescued, explored, steps, drones lost and survivors left in hazards.

A policy_fn has the gym's standard signature:
    policy_fn(features[5, N], mask[5], rng) -> action int
"""
from __future__ import annotations

import numpy as np

from .tasks import make_env

EVAL_SEED0 = 5000  # held-out range; training never uses >= 5000


def eval_seeds(n_maps: int, maps: str) -> list[int]:
    """Fixed held-out seeds for a family. Flood-heavy outdoor keeps a disjoint
    block so it does not reuse the plain outdoor maps."""
    base = EVAL_SEED0
    return [base + i for i in range(n_maps)]


def evaluate_policy(policy_fn, task: str = "rescue", maps: str = "buildings",
                    n_maps: int = 20, seed0: int = EVAL_SEED0) -> dict:
    """Evaluate a policy on n_maps held-out maps of (task, maps).

    Returns a dict of (mean, std) tuples for: rescued, explored, steps,
    drones_lost, survivors_in_hazard. drones_lost and survivors_in_hazard are 0
    on non-hazard tasks.
    """
    rescued, explored, steps, lost, in_haz = [], [], [], [], []
    for i in range(n_maps):
        s = seed0 + i
        env = make_env(task=task, maps=maps, seed=s)
        obs, _ = env.reset(seed=s)
        rng = np.random.default_rng(s ^ 0x5DEECE66D & 0xFFFFFFFF)
        while env.agents:
            acts = {a: policy_fn(obs[a]["features"], np.asarray(obs[a]["mask"], bool), rng)
                    for a in env.agents}
            obs, _, term, _, _ = env.step(acts)
            if not env.agents:
                break
        m = env.episode_metrics()
        rescued.append(m["rescued"]); explored.append(m["explored"]); steps.append(m["steps"])
        lost.append(m.get("disabled", 0)); in_haz.append(m.get("abandoned", 0))

    def ms(a):
        a = np.asarray(a, dtype=float)
        return (float(a.mean()), float(a.std()))
    return {
        "rescued": ms(rescued), "explored": ms(explored), "steps": ms(steps),
        "drones_lost": ms(lost), "survivors_in_hazard": ms(in_haz),
        "n_maps": n_maps, "task": task, "maps": maps,
    }
