"""Train (well, hand-write) your own Fellowship Gym policy and benchmark it.

    python -m examples.train_your_own

Shows the whole public API in one screen: make_env, a custom policy_fn, and
evaluate_policy against the built-in baselines.
"""
import numpy as np

import fellowship
from fellowship.benchmark import evaluate_policy
from fellowship import policies

TASK, MAPS = "rescue", "buildings"


def my_policy(features, mask, rng):
    """A tiny greedy policy: go for survivor progress (feature 2), break ties
    randomly, and never pick an illegal action."""
    scores = features[:, 2] + rng.normal(0, 1e-6, size=features.shape[0])
    scores = np.where(mask, scores, -np.inf)
    return int(np.argmax(scores))


def main():
    # 1. build an environment for a task + map family
    env = fellowship.make_env(task=TASK, maps=MAPS, seed=0)
    print(f"tasks available: {fellowship.list_tasks()}")
    print(f"map families:    {fellowship.list_map_families()}")
    print(f"evaluating on task={TASK}, maps={MAPS} (held-out seeds)\n")

    # 2. benchmark your policy and the baselines on the same held-out maps
    mine = evaluate_policy(my_policy, task=TASK, maps=MAPS, n_maps=10)
    rnd = evaluate_policy(policies.get_policy("random"), task=TASK, maps=MAPS, n_maps=10)
    rule = evaluate_policy(policies.get_policy("rule"), task=TASK, maps=MAPS, n_maps=10)

    print(f"{'policy':10} rescued/8")
    for name, r in [("mine", mine), ("random", rnd), ("rule", rule)]:
        print(f"{name:10} {r['rescued'][0]:.1f} ± {r['rescued'][1]:.1f}")


if __name__ == "__main__":
    main()
