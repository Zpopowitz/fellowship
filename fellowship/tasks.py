"""Named tasks and map families for Fellowship Gym.

A *task* is a fixed environment configuration plus the metric it is scored on.
A *map family* chooses where episodes happen. Together they define a benchmark
setting: `make_env(task="rescue_fire", maps="buildings", seed=0)`.

This module only *configures* the existing SwarmEnv — it does not change any
environment behaviour. Each task is a dict of SwarmEnv kwargs plus a `goal`
label naming the primary metric.

Tasks:
    explore       no hazards; goal = explored fraction (survivors present but the
                  benchmark scores coverage, not rescues)
    rescue        the default SAR task; goal = survivors rescued
    rescue_fire   hazards on, fire only; goal = survivors rescued, drones kept
    rescue_flood  hazards on, flood-heavy; goal = survivors rescued

Map families:
    streets_real   kind="sar"    georeferenced real Boston street grid
    streets_grid   kind="boston" the Moving AI Boston_0_256 grid
    buildings      home/office/datacenter/factory floorplans (cycled by seed)
"""
from __future__ import annotations

from .env import SwarmEnv

# ---- tasks: SwarmEnv kwargs + the metric the task is judged on --------------
TASKS: dict[str, dict] = {
    "explore": {
        "goal": "explored",
        "env": dict(hazards=False),
    },
    "rescue": {
        "goal": "rescued",
        "env": dict(hazards=False),
    },
    "rescue_fire": {
        "goal": "rescued",
        "env": dict(hazards=True, sensing="ir_gas", n_fire_seeds=3, flood_frac=0.0,
                    fire_spread_p=0.04),
    },
    "rescue_flood": {
        "goal": "rescued",
        "env": dict(hazards=True, sensing="ir_gas", n_fire_seeds=1, flood_frac=0.12,
                    fire_spread_p=0.04),
    },
}

# ---- map families: how a family + seed pick a concrete map kind -------------
BUILDING_KINDS = ("home", "office", "datacenter", "factory")

MAP_FAMILIES = ("streets_real", "streets_grid", "buildings")


def _kind_for(maps: str, seed: int) -> str:
    if maps == "streets_real":
        return "sar"
    if maps == "streets_grid":
        return "boston"
    if maps == "buildings":
        return BUILDING_KINDS[seed % len(BUILDING_KINDS)]
    raise ValueError(f"unknown map family {maps!r}; choose from {MAP_FAMILIES}")


def list_tasks() -> list[str]:
    """Names of the available tasks."""
    return list(TASKS)


def list_map_families() -> list[str]:
    """Names of the available map families."""
    return list(MAP_FAMILIES)


def task_goal(task: str) -> str:
    """The primary metric a task is judged on."""
    return TASKS[task]["goal"]


def make_env(task: str = "rescue", maps: str = "buildings", seed: int = 0,
             **overrides) -> SwarmEnv:
    """Build the PettingZoo ParallelEnv for a (task, map family, seed).

    task: one of list_tasks(). maps: one of list_map_families(). seed picks the
    concrete map (and, for buildings, which floorplan kind). ``overrides`` are
    passed straight through to SwarmEnv for advanced use. Returns an unreset
    env; call ``env.reset(seed=seed)`` (or reset() — the seed is stored).
    """
    if task not in TASKS:
        raise ValueError(f"unknown task {task!r}; choose from {list_tasks()}")
    kind = _kind_for(maps, seed)
    env_kwargs = dict(TASKS[task]["env"])
    env_kwargs.update(overrides)
    return SwarmEnv(kind=kind, seed=seed, **env_kwargs)
