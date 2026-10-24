"""Export a physical-AI training dataset from Fellowship Gym.

Records full episodes on TRAINING seeds only (0..3999 — never the held-out
5000+ benchmark maps) for every task x map family, with the rule and trained
policies driving the swarm. This is the R2 deliverable: data for training robot
swarms without risking real robots.

Output (dataset/):
  steps.parquet     one row per (episode, step, robot): pos, action, features,
                    mask, rescued_so_far, drone_lost
  episodes.parquet  one row per episode: outcome metrics
  maps/             the floorplan PNGs, the Boston grid, fire & flood density
  README.md         the dataset card

Run:  python scripts/export_dataset.py            (100 episodes per combo)
      python scripts/export_dataset.py --n 5       (small sample)
      python scripts/export_dataset.py --sample    (writes dataset/sample/, 5/combo)

The full export is gitignored; a 5-episode-per-combo sample is committed.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from fellowship import policies  # noqa: E402
from fellowship.tasks import list_map_families, list_tasks, make_env  # noqa: E402
from fellowship.env import agent_name  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_SEED0 = 0
TRAIN_SEED_MAX = 3999

FAMILY_SITUATION = {"streets_real": "outdoor", "streets_grid": "outdoor",
                    "buildings": "indoor"}


def _policy(name, maps):
    if name == "rule":
        return policies.get_policy("rule")
    if name == "trained":
        w = policies.load_trained(FAMILY_SITUATION.get(maps, "balanced"))
        return policies.linear_policy_factory(w) if w is not None \
            else policies.get_policy(FAMILY_SITUATION.get(maps, "balanced"))
    raise ValueError(name)


def _record_episode(task, maps, seed, policy_name, pol, step_rows, ep_rows):
    env = make_env(task=task, maps=maps, seed=seed)
    obs, _ = env.reset(seed=seed)
    rng = np.random.default_rng(seed ^ 0x5DEECE66D & 0xFFFFFFFF)
    eid = f"{task}:{maps}:{policy_name}:{seed}"
    kind = env.kind
    step = 0
    while env.agents:
        acts = {}
        for i in range(env.n_robots):
            a = agent_name(i)
            feats = obs[a]["features"]; mask = np.asarray(obs[a]["mask"], bool)
            act = int(pol(feats, mask, rng))
            acts[a] = act
            py, px = env.positions[i]
            step_rows.append({
                "episode_id": eid, "task": task, "map_family": maps, "kind": kind,
                "seed": seed, "policy": policy_name, "step": step, "robot": i,
                "pos_y": int(py), "pos_x": int(px), "action": act,
                "features": feats.astype(np.float32).ravel().tolist(),
                "mask": mask.astype(np.int8).tolist(),
                "rescued_so_far": int(env.rescued.sum()),
                "drone_lost": bool(env.disabled[i]) if env.hazards else False,
            })
        obs, _, term, _, _ = env.step(acts)
        step += 1
        if not env.agents:
            break
    m = env.episode_metrics()
    ep_rows.append({
        "episode_id": eid, "task": task, "map_family": maps, "kind": kind,
        "seed": seed, "policy": policy_name, "rescued": m["rescued"],
        "explored": m["explored"], "steps": m["steps"],
        "drones_lost": m.get("disabled", 0), "survivors_in_hazard": m.get("abandoned", 0),
    })


def _export_maps(dest):
    md = os.path.join(dest, "maps")
    os.makedirs(md, exist_ok=True)
    # floorplan PNGs
    src_fp = os.path.join(ROOT, "data", "floorplans")
    if os.path.isdir(src_fp):
        shutil.copytree(src_fp, os.path.join(md, "floorplans"), dirs_exist_ok=True)
    # georeferenced Boston grid + processed base (grid.json etc.)
    src_grid = os.path.join(ROOT, "data", "processed", "base", "grid.json")
    if os.path.exists(src_grid):
        shutil.copy(src_grid, os.path.join(md, "boston_grid.json"))
    # fire & flood density layers from the hazard field
    try:
        from fellowship import sar_dataset
        haz = sar_dataset.load_hazard_field()
        np.save(os.path.join(md, "fire_density.npy"), haz.fire)
        np.save(os.path.join(md, "flood_density.npy"), haz.flood)
    except Exception as exc:  # noqa: BLE001
        print(f"  (skipped density layers: {exc})")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=100, help="episodes per (task,family,policy)")
    ap.add_argument("--sample", action="store_true", help="write dataset/sample/ with 5/combo")
    args = ap.parse_args()

    n = 5 if args.sample else args.n
    dest = os.path.join(ROOT, "dataset", "sample" if args.sample else "")
    os.makedirs(dest, exist_ok=True)

    step_rows, ep_rows = [], []
    for task in list_tasks():
        for maps in list_map_families():
            for policy_name in ("rule", "trained"):
                pol = _policy(policy_name, maps)
                for i in range(n):
                    seed = TRAIN_SEED0 + i
                    assert seed <= TRAIN_SEED_MAX, "export must stay on training seeds"
                    _record_episode(task, maps, seed, policy_name, pol, step_rows, ep_rows)
                print(f"[{task}/{maps}/{policy_name}] {n} episodes", flush=True)

    pd.DataFrame(step_rows).to_parquet(os.path.join(dest, "steps.parquet"), index=False)
    pd.DataFrame(ep_rows).to_parquet(os.path.join(dest, "episodes.parquet"), index=False)
    _export_maps(dest)
    print(f"\nwrote {len(ep_rows)} episodes, {len(step_rows)} step rows to {dest}")
    print("\nTo publish to Hugging Face (not done automatically):")
    print(f"  huggingface-cli upload Zpopowitz/fellowship-gym {dest} --repo-type=dataset")


if __name__ == "__main__":
    main()
