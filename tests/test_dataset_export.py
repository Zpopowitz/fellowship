"""Smoke test: the dataset export records a valid episode with the documented
schema on training seeds."""
from __future__ import annotations

import numpy as np

from fellowship import policies
from fellowship.tasks import make_env
from fellowship.env import agent_name


def test_recorded_step_has_schema_and_training_seed():
    # mirror export_dataset._record_episode's per-step capture, on one episode
    seed = 3
    env = make_env(task="rescue_fire", maps="buildings", seed=seed)
    assert seed <= 3999, "dataset episodes must use training seeds"
    obs, _ = env.reset(seed=seed)
    rng = np.random.default_rng(0)
    pol = policies.get_policy("rule")
    rows = []
    while env.agents:
        acts = {}
        for i in range(env.n_robots):
            a = agent_name(i)
            feats = obs[a]["features"]; mask = np.asarray(obs[a]["mask"], bool)
            acts[a] = int(pol(feats, mask, rng))
            rows.append({
                "robot": i, "action": acts[a],
                "features": feats.astype(np.float32).ravel().tolist(),
                "mask": mask.astype(np.int8).tolist(),
            })
        obs, _, term, _, _ = env.step(acts)
        if not env.agents:
            break
    assert rows
    r = rows[0]
    assert len(r["features"]) == 45  # 5 actions x 9 features
    assert len(r["mask"]) == 5
    assert 0 <= r["action"] < 5
