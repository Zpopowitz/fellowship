"""Tests 1-8: environment invariants (hypothesis, random seeds/kinds/actions)."""
import numpy as np
from hypothesis import given, settings, strategies as st

from fellowship.env import SwarmEnv, agent_name, BLOCKED, UNKNOWN, OPEN
from fellowship import comms, maps

KINDS = st.sampled_from(("boston", "home", "office", "datacenter", "factory", "mixed"))
SEEDS = st.integers(0, 3999)


def _random_actions(env, rng):
    return {agent_name(i): int(rng.integers(0, 5)) for i in range(env.n_robots)}


@settings(max_examples=25, deadline=None)
@given(kind=KINDS, seed=SEEDS, steps=st.integers(1, 40))
def test_1_never_on_blocked(kind, seed, steps):
    env = SwarmEnv(kind=kind, seed=seed)
    env.reset(seed=seed)
    rng = np.random.default_rng(seed)
    for _ in range(steps):
        if not env.agents:
            break
        env.step(_random_actions(env, rng))
        for (y, x) in env.positions:
            assert env.open_grid[y, x], "robot stands on a blocked cell"


@settings(max_examples=25, deadline=None)
@given(kind=KINDS, seed=SEEDS, steps=st.integers(1, 40))
def test_2_map_never_false_blocked(kind, seed, steps):
    env = SwarmEnv(kind=kind, seed=seed)
    env.reset(seed=seed)
    rng = np.random.default_rng(seed)
    orig_open = env.open_grid.copy()
    for _ in range(steps):
        if not env.agents:
            break
        env.step(_random_actions(env, rng))
        # a cell a robot thinks is blocked must be truly blocked NOW
        for i in range(env.n_robots):
            blocked_known = env.known[i] == BLOCKED
            truly_blocked = ~env.open_grid
            assert not (blocked_known & ~truly_blocked).any(), \
                "known blocked but truly open"


@settings(max_examples=25, deadline=None)
@given(kind=KINDS, seed=SEEDS)
def test_3_merge_only_adds(kind, seed):
    env = SwarmEnv(kind=kind, seed=seed)
    env.reset(seed=seed)
    before = env.known.copy()
    merged = comms.merge_maps(env.known, list(range(env.n_robots)))
    # merged knows at least as much as any single robot
    for i in range(env.n_robots):
        known_i = before[i] != UNKNOWN
        assert (merged[known_i] != UNKNOWN).all(), "merge dropped knowledge"
        # no known cell flipped to unknown
        assert ((before[i] != UNKNOWN) <= (merged != UNKNOWN)).all()


@settings(max_examples=20, deadline=None)
@given(seed=SEEDS)
def test_4_isolated_gains_nothing(seed):
    # Force robot 0 far from the rest by checking components: a robot alone in
    # its component gets no external knowledge this step.
    env = SwarmEnv(kind="boston", seed=seed, comm=1)
    env.reset(seed=seed)
    groups = comms.link_components(env.positions, env.comm)
    # at reset all share the staging cell, so they are one group; step them apart
    rng = np.random.default_rng(seed)
    for _ in range(30):
        if not env.agents:
            break
        env.step(_random_actions(env, rng))
    groups = comms.link_components(env.positions, env.comm)
    for g in groups:
        if len(g) == 1:
            i = g[0]
            snapshot = env.known[i].copy()
            env._communicate()
            assert np.array_equal(snapshot, env.known[i]), \
                "isolated robot gained knowledge"


@settings(max_examples=30, deadline=None)
@given(kind=KINDS, seed=SEEDS)
def test_5_all_survivors_reachable(kind, seed):
    env = SwarmEnv(kind=kind, seed=seed)
    env.reset(seed=seed)
    comp = maps.largest_component(env.open_grid)
    # staging is in the largest component; every survivor must be too
    assert comp[env.staging], "staging not in largest open component"
    for (sy, sx) in env.survivor_cells:
        assert comp[sy, sx], "survivor not reachable from staging"


@settings(max_examples=20, deadline=None)
@given(kind=KINDS, seed=SEEDS, steps=st.integers(5, 40))
def test_6_determinism(kind, seed, steps):
    seq = [np.random.default_rng(seed + 99).integers(0, 5, size=4) for _ in range(steps)]

    def run():
        env = SwarmEnv(kind=kind, seed=seed)
        env.reset(seed=seed)
        traj = []
        for acts in seq:
            if not env.agents:
                break
            env.step({agent_name(i): int(acts[i]) for i in range(4)})
            traj.append(list(env.positions))
        return traj, env.episode_metrics()

    a_traj, a_m = run()
    b_traj, b_m = run()
    assert a_traj == b_traj
    assert a_m == b_m


@settings(max_examples=25, deadline=None)
@given(kind=KINDS, seed=SEEDS, steps=st.integers(1, 60))
def test_7_rescued_monotone(kind, seed, steps):
    env = SwarmEnv(kind=kind, seed=seed)
    env.reset(seed=seed)
    rng = np.random.default_rng(seed)
    last = 0
    for _ in range(steps):
        if not env.agents:
            break
        env.step(_random_actions(env, rng))
        r = int(env.rescued.sum())
        assert r >= last, "rescued count decreased"
        assert r <= env.k_survivors, "rescued exceeds K"
        last = r


@settings(max_examples=25, deadline=None)
@given(kind=KINDS, seed=SEEDS, steps=st.integers(1, 40))
def test_8_legal_action_not_known_blocked(kind, seed, steps):
    from fellowship import features as F
    env = SwarmEnv(kind=kind, seed=seed)
    obs, _ = env.reset(seed=seed)
    rng = np.random.default_rng(seed)
    for _ in range(steps):
        if not env.agents:
            break
        for i in range(env.n_robots):
            mask = np.asarray(obs[agent_name(i)]["mask"], dtype=bool)
            y, x = env.positions[i]
            for a in range(1, 5):
                if mask[a]:
                    ty, tx = y + F.DELTAS[a, 0], x + F.DELTAS[a, 1]
                    assert env.known[i, ty, tx] != BLOCKED, \
                        "legal action targets known-blocked cell"
        obs, _, _, _, _ = env.step(_random_actions(env, rng))
