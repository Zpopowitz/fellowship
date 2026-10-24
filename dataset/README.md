# Fellowship Gym — SAR swarm dataset

A dataset of decentralized search-and-rescue episodes, for training physical-AI
robot swarms without risking real robots (Hackachusetts Robotics, challenge R2).

## What it is

Full trajectories of 4-robot swarms searching for 8 survivors across real Boston
street grids and procedurally damaged buildings, under four tasks (plain search,
rescue, rescue-under-fire, rescue-under-flood). Each robot is decentralized: it
acts only on what it has sensed or heard over short-range radio.

## How it was generated

`python scripts/export_dataset.py` runs the gym (`fellowship.make_env`) on
**training seeds only (0–3999)** for every task × map family, driven by two
policies — `rule` (hand-tuned linear) and `trained` (CEM, the firefighter
objective). Default 100 episodes per combination; the committed `sample/` holds
5 per combination.

**Held-out split:** this dataset is TRAINING data (seeds 0–3999). The benchmark
maps (seeds 5000+, `LEADERBOARD.md`) are never recorded here, so a model trained
on this dataset can be evaluated on unseen maps honestly.

## Files

| File | One row per | Key columns |
|---|---|---|
| `steps.parquet` | (episode, step, robot) | `episode_id, task, map_family, kind, seed, policy, step, robot, pos_y, pos_x, action, features (list of 9), mask (list of 5), rescued_so_far, drone_lost` |
| `episodes.parquet` | episode | `episode_id, task, map_family, kind, seed, policy, rescued, explored, steps, drones_lost, survivors_in_hazard` |
| `maps/floorplans/` | — | 240 floorplan PNGs (white=open, black=wall/rubble) |
| `maps/boston_grid.json` | — | the georeferenced 256×256 Boston street-occupancy grid |
| `maps/fire_density.npy` | — | per-cell real fire density (severity-weighted, from Boston fire incidents) |
| `maps/flood_density.npy` | — | per-cell flood density (FEMA declarations + tide) |

### Column detail — `steps.parquet`

- `action`: 0 stay, 1 north, 2 south, 3 east, 4 west.
- `features`: the 9 per-action policy features flattened to length 45 (5 actions ×
  9: new-area, frontier, survivor, crowding, revisits, stay, fire-danger,
  flood-danger, survivor-urgency).
- `mask`: which of the 5 actions were legal that step.
- `drone_lost`: whether this robot had been disabled by fire by this step.

## Sample stats (committed `sample/`)

120 episodes, ~72k step rows, ~1.7 MB. Full default export (`--n 100`) is ~2.4k
episodes and is **gitignored** (regenerate with the script).

## Known limitations

- Grid world, not real physics; 71 m cells.
- Survivors placed at random (or biased toward real fire density on `sar` maps).
- Fire is geocoded only to ZIP centroid; flood only to county.
- Rescue status is currently global (a robot's `rescued_so_far` reflects team
  rescues even out of radio range) — see the repo README Limits.
- Procedural floorplans, not scanned buildings.

## Licenses

- **Code & dataset schema:** MIT (repo `LICENSE`).
- **Boston open data** (streets, fire incidents): PDDL — see `docs/DATA_SOURCES.md`.
- **Moving AI Boston_0_256 grid:** cite Sturtevant, "Benchmarks for Grid-Based
  Pathfinding", IEEE TCIAIG 2012.
- **MBTA data:** under MBTA licensing terms.

## Publish (not done automatically)

```
huggingface-cli upload Zpopowitz/fellowship-gym dataset/ --repo-type=dataset
```
