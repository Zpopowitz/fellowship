"""Fellowship SwarmEnv: a decentralized multi-robot SAR PettingZoo ParallelEnv.

No global map, no central planner. Each robot keeps its own knowledge map and
survivor sightings; at the start of every step, robots within radio range share
merged knowledge through chains of teammates.
"""
from __future__ import annotations

import functools
import numpy as np
import gymnasium as gym
from pettingzoo import ParallelEnv
from pettingzoo.utils import wrappers

from . import comms, features, maps
from .features import DELTAS, N_ACTIONS, N_FEATURES

N_ROBOTS = 4
K_SURVIVORS = 8
T_STEPS = 160
VIEW = 2            # Chebyshev sensing radius
COMM = comms.COMM   # 10
AFTERSHOCK_EVERY = 25
AFTERSHOCK_N = 4

# knowledge codes
UNKNOWN, OPEN, BLOCKED = 0, 1, 2


def agent_name(i: int) -> str:
    return f"robot_{i}"


class SwarmEnv(ParallelEnv):
    metadata = {"render_modes": [], "name": "fellowship_swarm_v0"}

    def __init__(self, kind: str = "mixed", seed: int | None = None,
                 n_robots: int = N_ROBOTS, k_survivors: int = K_SURVIVORS,
                 t_steps: int = T_STEPS, comm: int = COMM):
        self.kind = kind
        self._init_seed = seed
        self.n_robots = n_robots
        self.k_survivors = k_survivors
        self.t_steps = t_steps
        self.comm = comm
        self.possible_agents = [agent_name(i) for i in range(n_robots)]
        self.agents = list(self.possible_agents)
        self.size = maps.REGION
        self._built = False

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        H = self.size
        return gym.spaces.Dict({
            "features": gym.spaces.Box(-np.inf, np.inf, shape=(N_ACTIONS, N_FEATURES), dtype=np.float64),
            "mask": gym.spaces.MultiBinary(N_ACTIONS),
        })

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return gym.spaces.Discrete(N_ACTIONS)

    # ---------------------------------------------------------------- reset
    def reset(self, seed: int | None = None, options=None):
        if seed is None:
            seed = self._init_seed if self._init_seed is not None else 0
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)

        self.open_grid = maps.sample_map(self.kind, self.seed)  # True=open
        H, W = self.open_grid.shape
        self.H, self.W = H, W

        self.staging = self._nearest_open_to_corner()
        self.positions = [self.staging for _ in range(self.n_robots)]

        self.survivor_cells = self._place_survivors()
        self.rescued = np.zeros(self.k_survivors, dtype=bool)

        # per-robot knowledge and sightings
        self.known = np.zeros((self.n_robots, H, W), dtype=np.uint8)
        self.sightings = [set() for _ in range(self.n_robots)]
        self.visits = np.zeros((self.n_robots, H, W), dtype=np.int64)

        self.step_count = 0
        self.agents = list(self.possible_agents)
        self._built = True

        for i in range(self.n_robots):
            self.visits[i][self.positions[i]] += 1
            self._sense(i)
        self._communicate()

        obs = self._all_obs()
        infos = {a: {} for a in self.agents}
        return obs, infos

    def _nearest_open_to_corner(self) -> tuple[int, int]:
        ys, xs = np.nonzero(self.open_grid)
        d = ys + xs  # manhattan to (0,0)
        k = int(np.argmin(d))
        return int(ys[k]), int(xs[k])

    def _place_survivors(self) -> list[tuple[int, int]]:
        ys, xs = np.nonzero(self.open_grid)
        cells = list(zip(ys.tolist(), xs.tolist()))
        cells = [c for c in cells if c != self.staging]
        idx = self.rng.choice(len(cells), size=min(self.k_survivors, len(cells)),
                              replace=False)
        return [cells[int(i)] for i in idx]

    # ---------------------------------------------------------------- sensing
    def _sense(self, i: int):
        y, x = self.positions[i]
        y0, y1 = max(0, y - VIEW), min(self.H, y + VIEW + 1)
        x0, x1 = max(0, x - VIEW), min(self.W, x + VIEW + 1)
        sub = self.open_grid[y0:y1, x0:x1]
        kv = self.known[i, y0:y1, x0:x1]
        kv[sub] = np.maximum(kv[sub], OPEN)
        kv[~sub] = BLOCKED
        self.known[i, y0:y1, x0:x1] = kv
        # survivors in window
        for sid, (sy, sx) in enumerate(self.survivor_cells):
            if self.rescued[sid]:
                continue
            if y0 <= sy < y1 and x0 <= sx < x1:
                self.sightings[i].add(sid)

    # ---------------------------------------------------------------- comms
    def _communicate(self):
        groups = comms.link_components(self.positions, self.comm)
        for g in groups:
            if len(g) <= 1:
                continue
            merged = comms.merge_maps(self.known, g)
            merged_s = comms.merge_sightings(self.sightings, g)
            for i in g:
                self.known[i] = merged.copy()
                self.sightings[i] = set(merged_s)

    # ---------------------------------------------------------------- obs
    def _survivors_known_for(self, i: int) -> list[tuple[int, int]]:
        return [self.survivor_cells[sid] for sid in self.sightings[i]
                if not self.rescued[sid]]

    def _obs_for(self, i: int):
        teammates = [self.positions[j] for j in range(self.n_robots) if j != i]
        # only teammates currently linked contribute to crowding
        groups = comms.link_components(self.positions, self.comm)
        my_group = next(g for g in groups if i in g)
        linked = [self.positions[j] for j in my_group if j != i]
        feats, mask = features.compute_features(
            self.known[i], self.positions[i], linked,
            self._survivors_known_for(i), self.visits[i])
        return {"features": feats, "mask": mask.astype(np.int8)}

    def _all_obs(self):
        return {agent_name(i): self._obs_for(i) for i in range(self.n_robots)}

    # ---------------------------------------------------------------- step
    def step(self, actions: dict):
        self._communicate()  # share at the start of the step

        for i in range(self.n_robots):
            a = int(actions[agent_name(i)])
            y, x = self.positions[i]
            dy, dx = DELTAS[a]
            ty, tx = y + dy, x + dx
            if a == 0:
                pass
            elif 0 <= ty < self.H and 0 <= tx < self.W and self.open_grid[ty, tx]:
                self.positions[i] = (ty, tx)
            else:
                # blocked move: stay + mark blocked in own map
                if 0 <= ty < self.H and 0 <= tx < self.W:
                    self.known[i, ty, tx] = BLOCKED
            self.visits[i][self.positions[i]] += 1

        for i in range(self.n_robots):
            self._sense(i)
            self._rescue(i)

        self.step_count += 1
        if self.step_count % AFTERSHOCK_EVERY == 0:
            self._aftershock()

        done = bool(self.rescued.all()) or self.step_count >= self.t_steps
        obs = self._all_obs()
        rewards = {a: 0.0 for a in self.agents}
        terminations = {a: done for a in self.agents}
        truncations = {a: False for a in self.agents}
        infos = {a: {} for a in self.agents}
        if done:
            self.agents = []
        return obs, rewards, terminations, truncations, infos

    def _rescue(self, i: int):
        pos = self.positions[i]
        for sid, cell in enumerate(self.survivor_cells):
            if not self.rescued[sid] and cell == pos:
                self.rescued[sid] = True

    def _aftershock(self):
        occupied = set(self.positions)
        ys, xs = np.nonzero(self.open_grid)
        candidates = [(int(a), int(b)) for a, b in zip(ys, xs)
                      if (int(a), int(b)) not in occupied
                      and (int(a), int(b)) not in self.survivor_cells]
        if not candidates:
            return
        n = min(AFTERSHOCK_N, len(candidates))
        pick = self.rng.choice(len(candidates), size=n, replace=False)
        for k in pick:
            cell = candidates[int(k)]
            self.open_grid[cell] = False  # now a wall; robots learn by sensing

    # ---------------------------------------------------------------- metrics
    def explored_fraction(self) -> float:
        team = np.max(self.known, axis=0)
        total_open = int(self.open_grid.sum()) + int((self.known == BLOCKED).any(axis=0).sum() & 0)
        known_cells = int((team != UNKNOWN).sum())
        denom = int((self.open_grid).sum())
        # fraction of originally-open cells the team has any knowledge of
        open_known = int(((team != UNKNOWN) & self.open_grid).sum())
        return open_known / max(1, denom)

    def score(self) -> float:
        rescued = int(self.rescued.sum())
        explored = self.explored_fraction()
        s = rescued + 0.5 * explored
        if rescued == self.k_survivors:
            s += (self.t_steps - self.step_count) / self.t_steps
        return float(s)

    def episode_metrics(self) -> dict:
        return {
            "rescued": int(self.rescued.sum()),
            "explored": self.explored_fraction(),
            "steps": self.step_count,
            "kind": self.kind,
            "score": self.score(),
        }


def raw_env(**kwargs):
    return SwarmEnv(**kwargs)


def env(**kwargs):
    """PettingZoo-style wrapped constructor (order-enforcing)."""
    e = SwarmEnv(**kwargs)
    e = wrappers.OrderEnforcingParallelWrapper(e) if hasattr(wrappers, "OrderEnforcingParallelWrapper") else e
    return e
