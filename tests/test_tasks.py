"""Tests for the task suite / public gym API."""
from __future__ import annotations

import numpy as np
import pytest

import fellowship
from fellowship.env import SwarmEnv
from fellowship import tasks


def test_list_tasks_and_families():
    assert set(fellowship.list_tasks()) == {"explore", "rescue", "rescue_fire", "rescue_flood"}
    assert set(fellowship.list_map_families()) == {"streets_real", "streets_grid", "buildings"}


@pytest.mark.parametrize("task", ["explore", "rescue", "rescue_fire", "rescue_flood"])
@pytest.mark.parametrize("maps", ["streets_real", "streets_grid", "buildings"])
def test_make_env_builds_and_resets(task, maps):
    env = fellowship.make_env(task=task, maps=maps, seed=0)
    assert isinstance(env, SwarmEnv)
    obs, infos = env.reset(seed=0)
    assert len(obs) == env.n_robots
    # one step with legal actions
    acts = {a: int(np.argmax(obs[a]["mask"])) for a in env.agents}
    env.step(acts)


def test_buildings_cycle_kinds_by_seed():
    kinds = {fellowship.make_env(maps="buildings", seed=s).kind for s in range(4)}
    assert kinds == {"home", "office", "datacenter", "factory"}


def test_hazard_tasks_enable_hazards():
    assert fellowship.make_env(task="rescue_fire").hazards is True
    assert fellowship.make_env(task="rescue_flood").hazards is True
    assert fellowship.make_env(task="rescue").hazards is False


def test_unknown_task_and_family_rejected():
    with pytest.raises(ValueError):
        fellowship.make_env(task="nope")
    with pytest.raises(ValueError):
        fellowship.make_env(maps="nope")
