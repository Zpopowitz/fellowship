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

from . import comms, features, maps, hazards as hz
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
                 t_steps: int = T_STEPS, comm: int = COMM,
                 hazards: bool = False, fire_spread_p: float = 0.15,
                 n_fire_seeds: int = 1, flood_frac: float = 0.05,
                 sensing: str = "local", wind: tuple = (0, 0)):
        self.kind = kind
        self._init_seed = seed
        self.n_robots = n_robots
        self.k_survivors = k_survivors
        self.t_steps = t_steps
        self.comm = comm
        self.hazards = hazards
        self.fire_spread_p = fire_spread_p
        self.n_fire_seeds = n_fire_seeds
        self.flood_frac = flood_frac
        self.sensing = sensing      # 'local' (5x5) or 'ir_gas' (thermal + smoke)
        self.wind = wind            # (dy, dx) smoke drift direction
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

        # hazards: fire (spreads) and flood (static). Off unless enabled.
        self.fire = np.zeros((H, W), dtype=bool)
        self.flood = np.zeros((H, W), dtype=bool)
        if self.hazards:
            self._place_hazards()

        # per-robot knowledge and sightings
        self.known = np.zeros((self.n_robots, H, W), dtype=np.uint8)
        self.sightings = [set() for _ in range(self.n_robots)]
        self.visits = np.zeros((self.n_robots, H, W), dtype=np.int64)
        # per-robot sensed hazard danger fields (0 until sensed)
        self.known_fire = np.zeros((self.n_robots, H, W), dtype=bool)
        self.known_flood = np.zeros((self.n_robots, H, W), dtype=bool)
        self.known_gas = np.zeros((self.n_robots, H, W), dtype=np.float64)  # smoke reading
        self.disabled = np.zeros(self.n_robots, dtype=bool)  # a drone lost to fire

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

    def _place_hazards(self) -> None:
        """Fill self.fire / self.flood. Real SAR-data seeds for kind='sar',
        procedural seeds otherwise. Never ignite the staging cell."""
        if self.kind == "sar":
            from . import sar_dataset
            sc = sar_dataset.sample_scenario(self.seed, n_survivors=self.k_survivors)
            for (y, x) in sc.fire_cells:
                if (y, x) != self.staging and self.open_grid[y, x]:
                    self.fire[y, x] = True
            for (y, x) in sc.flood_cells:
                if (y, x) != self.staging and self.open_grid[y, x]:
                    self.flood[y, x] = True
            # SAR crops may have no in-region hazard; fall back to one seed so a
            # hazard episode always has a hazard.
            if not self.fire.any() and not self.flood.any():
                self.fire, self.flood = hz.place_procedural_hazards(
                    self.open_grid, self.rng, self.n_fire_seeds, self.flood_frac)
        else:
            self.fire, self.flood = hz.place_procedural_hazards(
                self.open_grid, self.rng, self.n_fire_seeds, self.flood_frac)
        # keep staging safe
        self.fire[self.staging] = False
        self.flood[self.staging] = False

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
        # hazards in the window
        if self.hazards:
            if self.sensing == "ir_gas":
                # thermal IR: sees fire by heat, line-of-sight, through smoke/dark
                blocked = ~self.open_grid  # walls block IR
                ir = hz.thermal_ir_view(self.fire, blocked, self.positions[i])
                self.known_fire[i] |= ir
                # gas/particulate: smoke plume drifting downwind, early warning
                plume = hz.gas_plume(self.fire, self.positions[i], wind=self.wind)
                self.known_gas[i] = np.maximum(self.known_gas[i] * 0.8, plume)
                # flood still sensed locally (water has no heat/smoke signature)
                self.known_flood[i, y0:y1, x0:x1] |= self.flood[y0:y1, x0:x1]
            else:
                self.known_fire[i, y0:y1, x0:x1] |= self.fire[y0:y1, x0:x1]
                self.known_flood[i, y0:y1, x0:x1] |= self.flood[y0:y1, x0:x1]
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
            if self.hazards:
                mf = np.any(self.known_fire[g], axis=0)
                mfl = np.any(self.known_flood[g], axis=0)
                mg = np.max(self.known_gas[g], axis=0) if self.sensing == "ir_gas" else None
                for i in g:
                    self.known_fire[i] = mf.copy()
                    self.known_flood[i] = mfl.copy()
                    if mg is not None:
                        self.known_gas[i] = mg.copy()

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
        fire_danger = flood_danger = None
        if self.hazards:
            fire_danger = hz.danger_field(self.known_fire[i])
            if self.sensing == "ir_gas":
                # smoke the drone smells adds to perceived fire danger (early warning)
                fire_danger = np.maximum(fire_danger, self.known_gas[i])
            flood_danger = hz.danger_field(self.known_flood[i])
        feats, mask = features.compute_features(
            self.known[i], self.positions[i], linked,
            self._survivors_known_for(i), self.visits[i],
            fire_danger=fire_danger, flood_danger=flood_danger)
        return {"features": feats, "mask": mask.astype(np.int8)}

    def _all_obs(self):
        return {agent_name(i): self._obs_for(i) for i in range(self.n_robots)}

    # ---------------------------------------------------------------- step
    def step(self, actions: dict):
        self._communicate()  # share at the start of the step

        for i in range(self.n_robots):
            if self.hazards and self.disabled[i]:
                continue  # a drone lost to fire takes no action
            a = int(actions[agent_name(i)])
            y, x = self.positions[i]
            dy, dx = DELTAS[a]
            ty, tx = y + dy, x + dx
            if a == 0:
                pass
            elif (0 <= ty < self.H and 0 <= tx < self.W and self.open_grid[ty, tx]
                  and not (self.hazards and self.flood[ty, tx])):
                self.positions[i] = (ty, tx)
            else:
                # blocked move: stay + mark blocked in own map
                if 0 <= ty < self.H and 0 <= tx < self.W:
                    self.known[i, ty, tx] = BLOCKED
                    if self.hazards and self.flood[ty, tx]:
                        self.known_flood[i, ty, tx] = True
            self.visits[i][self.positions[i]] += 1
            # stepping onto / sitting in fire disables the drone
            if self.hazards and self.fire[self.positions[i]]:
                self.disabled[i] = True
                self.known_fire[i, self.positions[i]] = True

        for i in range(self.n_robots):
            self._sense(i)
            self._rescue(i)

        self.step_count += 1
        if self.hazards and self.fire.any():
            self.fire = hz.spread_fire(self.fire, self.open_grid, self.rng,
                                       p=self.fire_spread_p)
            # a drone caught by newly-spread fire is disabled
            for i in range(self.n_robots):
                if not self.disabled[i] and self.fire[self.positions[i]]:
                    self.disabled[i] = True
        if self.step_count % AFTERSHOCK_EVERY == 0:
            self._aftershock()

        done = bool(self.rescued.all()) or self.step_count >= self.t_steps
        if self.hazards and self.disabled.all():
            done = True  # whole swarm lost
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

    def score_firefighter(self, w_rescue: float = 10.0, w_drone_loss: float = 1.0,
                          w_abandon: float = 4.0, w_explore: float = 1.0) -> float:
        """Firefighter risk-vs-reward objective: optimise for SAVING PEOPLE,
        calibrated the way fire-service doctrine is ("risk a lot to save a
        savable life; risk little for little; risk nothing for the lost").

        reward = w_rescue * survivors_rescued            (saving people dominates)
               + w_explore * explored_fraction           (find the unseen)
               - w_drone_loss * drones_lost               (don't throw drones away...
               - w_abandon * reachable_survivors_left_to_die  ...but losing a drone
                                                           to reach a SAVABLE person
                                                           costs far less than letting
                                                           that person die)

        A survivor "left to die" = not rescued AND their cell is on fire or
        flooded at episode end (they were in danger and the swarm didn't reach
        them in time). A survivor simply unreached on a safe cell is a miss, not
        an abandonment, so it is not double-counted beyond the rescue term.
        """
        rescued = int(self.rescued.sum())
        explored = self.explored_fraction()
        lost = int(self.disabled.sum()) if self.hazards else 0
        abandoned = 0
        if self.hazards:
            for sid, (sy, sx) in enumerate(self.survivor_cells):
                if not self.rescued[sid] and (self.fire[sy, sx] or self.flood[sy, sx]):
                    abandoned += 1
        s = (w_rescue * rescued
             + w_explore * explored
             - w_drone_loss * lost
             - w_abandon * abandoned)
        # small time bonus for clearing everyone, like score()
        if rescued == self.k_survivors:
            s += (self.t_steps - self.step_count) / self.t_steps
        return float(s)

    def episode_metrics(self) -> dict:
        m = {
            "rescued": int(self.rescued.sum()),
            "explored": self.explored_fraction(),
            "steps": self.step_count,
            "kind": self.kind,
            "score": self.score(),
        }
        if self.hazards:
            m["disabled"] = int(self.disabled.sum())
            m["fire_cells"] = int(self.fire.sum())
            m["flood_cells"] = int(self.flood.sum())
            abandoned = 0
            for sid, (sy, sx) in enumerate(self.survivor_cells):
                if not self.rescued[sid] and (self.fire[sy, sx] or self.flood[sy, sx]):
                    abandoned += 1
            m["abandoned"] = abandoned
            m["firefighter_score"] = self.score_firefighter()
        return m


def raw_env(**kwargs):
    return SwarmEnv(**kwargs)


def env(**kwargs):
    """PettingZoo-style wrapped constructor (order-enforcing)."""
    e = SwarmEnv(**kwargs)
    e = wrappers.OrderEnforcingParallelWrapper(e) if hasattr(wrappers, "OrderEnforcingParallelWrapper") else e
    return e
