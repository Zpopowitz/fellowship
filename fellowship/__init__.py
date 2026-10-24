"""Fellowship Gym: search-and-rescue training environments built from real
Boston streets and damaged buildings, plus a dataset, for training robot swarms.

Public API:
    fellowship.make_env(task="rescue", maps="buildings", seed=0) -> SwarmEnv
    fellowship.list_tasks()         -> list of task names
    fellowship.list_map_families()  -> list of map-family names
"""
from .tasks import list_map_families, list_tasks, make_env, task_goal

__all__ = ["make_env", "list_tasks", "list_map_families", "task_goal"]
