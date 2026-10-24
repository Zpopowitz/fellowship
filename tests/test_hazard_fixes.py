"""Section-3 hazard-fix tests: gas plume direction, fire-in-mask, and disabled
drones going fully silent."""
from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from fellowship import features, hazards
from fellowship.env import SwarmEnv, agent_name
from fellowship import policies


# ---- 3a: gas plume is directional --------------------------------------
@settings(max_examples=20, deadline=None)
@given(fx=st.integers(min_value=12, max_value=18))
def test_gas_reading_higher_toward_fire(fx):
    N = 25
    fire = np.zeros((N, N), dtype=bool)
    fire[10, fx] = True            # fire to the EAST of the drone at (10,10)
    plume = hazards.gas_plume(fire, (10, 10), wind=(0, 0), gas_range=12)
    east = plume[10, 11]           # one step toward the fire
    west = plume[10, 9]            # one step away
    assert east > west, "stepping toward the fire must read strictly higher"


def test_gas_wind_toward_drone_raises_reading_at_drone():
    N = 25
    fire = np.zeros((N, N), dtype=bool)
    fire[10, 18] = True            # fire to the east
    no_wind = hazards.gas_plume(fire, (10, 10), wind=(0, 0), gas_range=14)[10, 10]
    # wind blowing the smoke west (toward the drone): positive east-component
    toward = hazards.gas_plume(fire, (10, 10), wind=(0, 6), gas_range=14)[10, 10]
    assert toward > no_wind, "wind carrying smoke onto the drone raises its reading"


# ---- 3b: known fire is an illegal move ---------------------------------
def test_known_fire_cell_is_illegal_move():
    known = np.ones((7, 7), dtype=np.uint8)  # all open
    kf = np.zeros((7, 7), dtype=bool)
    kf[2, 3] = True                           # fire just NORTH of (3,3)
    mask = features.legal_mask(known, (3, 3), known_fire=kf)
    # action 1 = north (DELTAS[1] = (-1,0)) targets the fire cell -> illegal
    assert mask[1] == False
    assert mask[0] == True                    # stay still legal


# ---- 3d: a disabled drone adds nothing after it dies -------------------
@settings(max_examples=6, deadline=None)
@given(seed=st.integers(min_value=5000, max_value=5040))
def test_disabled_drone_adds_no_new_knowledge(seed):
    env = SwarmEnv(kind="sar", hazards=True, sensing="ir_gas", n_fire_seeds=3,
                   fire_spread_p=0.1)
    obs, _ = env.reset(seed=seed)
    pol = policies.get_policy("blind", kind="sar")  # blind: will walk into fire
    rng = np.random.default_rng(0)
    snap = None
    while env.agents:
        acts = {a: pol(obs[a]["features"], obs[a]["mask"], rng) for a in env.agents}
        obs, _, term, _, _ = env.step(acts)
        # find a drone that is disabled; snapshot its maps, step once, compare
        dis = np.flatnonzero(env.disabled)
        if len(dis):
            i = int(dis[0])
            before = (env.known[i].copy(), env.known_fire[i].copy())
            # run one more step; the dead drone must not add cells
            if env.agents:
                acts = {a: pol(obs[a]["features"], obs[a]["mask"], rng) for a in env.agents}
                obs, _, term, _, _ = env.step(acts)
            after = (env.known[i], env.known_fire[i])
            assert (after[0] >= before[0]).all()  # monotone anyway
            # a disabled drone's OWN sensing adds nothing; any growth could only
            # come from a radio merge, which it is also excluded from -> equal
            assert np.array_equal(after[0], before[0]), "disabled drone gained map cells"
            assert np.array_equal(after[1], before[1]), "disabled drone gained fire cells"
            break
        if all(term.values()):
            break
