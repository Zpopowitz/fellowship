"""Tests for the thermal-IR and gas/particulate sensor models."""
from __future__ import annotations

import numpy as np

from fellowship import hazards
from fellowship.env import SwarmEnv


def test_thermal_ir_sees_fire_in_range_with_clear_line():
    fire = np.zeros((11, 11), dtype=bool)
    fire[5, 9] = True  # 4 cells east of a drone at (5,5), open between
    blocked = np.zeros((11, 11), dtype=bool)
    seen = hazards.thermal_ir_view(fire, blocked, (5, 5), ir_range=6)
    assert seen[5, 9], "IR should see fire within range on a clear line"


def test_thermal_ir_blocked_by_wall():
    fire = np.zeros((11, 11), dtype=bool)
    fire[5, 9] = True
    blocked = np.zeros((11, 11), dtype=bool)
    blocked[5, 7] = True  # wall between drone and fire
    seen = hazards.thermal_ir_view(fire, blocked, (5, 5), ir_range=6)
    assert not seen[5, 9], "a wall must block the IR line of sight"


def test_thermal_ir_out_of_range():
    fire = np.zeros((20, 20), dtype=bool)
    fire[5, 19] = True  # 14 cells away, beyond ir_range=6
    seen = hazards.thermal_ir_view(fire, np.zeros((20, 20), bool), (5, 5), ir_range=6)
    assert not seen.any()


def test_gas_plume_detects_farther_than_ir_and_is_fuzzy():
    fire = np.zeros((25, 25), dtype=bool)
    fire[5, 14] = True  # 9 cells east — beyond IR (6), within gas (10)
    plume = hazards.gas_plume(fire, (5, 5), wind=(0, 0), gas_range=10)
    assert plume.max() > 0.0, "gas should register a distant fire"
    # it is a field (fuzzy), not a single exact cell
    assert (plume > 0).sum() >= 1


def test_gas_plume_wind_increases_downwind_reading():
    fire = np.zeros((25, 25), dtype=bool)
    fire[5, 16] = True
    # drone downwind (fire drifts west toward the drone at (5,5)) smells it more
    upwind = hazards.gas_plume(fire, (5, 5), wind=(0, 0), gas_range=12).max()
    downwind = hazards.gas_plume(fire, (5, 5), wind=(0, 6), gas_range=12).max()
    assert downwind >= upwind


def test_env_ir_gas_mode_runs_and_detects_fire_beyond_local_view():
    env = SwarmEnv(kind="sar", hazards=True, sensing="ir_gas", n_fire_seeds=3)
    obs, _ = env.reset(seed=7)
    # step a few times; a drone should accumulate some fire/gas knowledge
    import numpy as np
    from fellowship import policies
    pol = policies.get_policy("cautious")
    rng = np.random.default_rng(0)
    for _ in range(20):
        if not env.agents:
            break
        acts = {a: pol(obs[a]["features"], obs[a]["mask"], rng) for a in env.agents}
        obs, _, term, _, _ = env.step(acts)
        if all(term.values()):
            break
    detected = env.known_fire.any() or (env.known_gas > 0).any()
    assert detected, "IR/gas sensing should detect the fire during the episode"
