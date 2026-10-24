"""Run one full episode with a single policy applied to every robot."""
from __future__ import annotations

import numpy as np

from .env import SwarmEnv, agent_name


def run_episode(policy, kind: str, seed: int, comm: int | None = None,
                collect_frames: bool = False, **env_kwargs):
    """Run one episode; return (metrics, frames).

    policy: (features[5,N], mask[5], rng) -> action.
    env_kwargs: forwarded to SwarmEnv (hazards, sensing, wind, n_fire_seeds, ...).
    frames: list of dicts for rendering (only if collect_frames).
    """
    kwargs = {"kind": kind, "seed": seed}
    if comm is not None:
        kwargs["comm"] = comm
    kwargs.update(env_kwargs)
    env = SwarmEnv(**kwargs)
    obs, _ = env.reset(seed=seed)
    rng = np.random.default_rng(seed ^ 0x5DEECE66D & 0xFFFFFFFF)

    frames = []
    if collect_frames:
        frames.append(_frame(env))

    done = False
    while env.agents:
        actions = {}
        for i in range(env.n_robots):
            a = agent_name(i)
            actions[a] = policy(obs[a]["features"], np.asarray(obs[a]["mask"], dtype=bool), rng)
        obs, _, term, trunc, _ = env.step(actions)
        if collect_frames:
            frames.append(_frame(env))
        if not env.agents:
            break
    return env.episode_metrics(), frames


def _frame(env):
    import numpy as np
    team_known = np.max(env.known, axis=0)
    return {
        "open_grid": env.open_grid.copy(),
        "known": team_known.copy(),
        "positions": list(env.positions),
        "survivors": list(env.survivor_cells),
        "rescued": env.rescued.copy(),
        "step": env.step_count,
        "n_rescued": int(env.rescued.sum()),
    }
