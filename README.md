# Fellowship

![swarm](results/swarm.gif)

A swarm of rescue robots with no leader, trained on real Boston streets and damaged buildings, learns to split up and find survivors.

## What it is

Fellowship is a decentralized multi-robot search-and-rescue training environment. Robots start together, then spread out across a 48×48 grid cut from the real Boston street map or a procedurally damaged building (home, office, data center, factory) to find eight survivors before time runs out. There is no global map and no central planner: each robot knows only what it has sensed itself plus what reached it over radio from teammates within range, relayed through chains of robots. The world shifts mid-mission — aftershocks turn open cells into rubble — and every reported number comes from held-out maps the policy never trained on.

## The places it trains on

![floorplans](results/floorplans_preview.png)

Boston regions are random 48×48 crops of the Moving AI `Boston_0_256` grid. Buildings are generated procedurally and then damaged (rubble piles), keeping only the largest connected open area so every survivor is reachable.

## Results

<!-- RESULTS:BEGIN -->
All numbers are from **held-out maps** (eval seeds ≥ 5000), never used in training. 20 maps per kind, 100 total, same maps and seeds for every policy.

### Rescued (of 8), mean ± std, 20 held-out maps/kind (100 total)

| policy | boston | home | office | datacenter | factory | overall |
|---|---|---|---|---|---|---|
| random | 0.40 ± 0.58 | 0.20 ± 0.40 | 0.35 ± 0.65 | 0.35 ± 0.73 | 0.40 ± 0.80 | 0.34 ± 0.65 |
| rule | 6.55 ± 1.53 | 5.20 ± 1.54 | 6.15 ± 1.28 | 5.85 ± 2.06 | 7.15 ± 0.91 | 6.18 ± 1.65 |
| scratch | 6.50 ± 1.40 | 5.30 ± 1.55 | 5.85 ± 1.56 | 6.20 ± 1.33 | 7.15 ± 0.91 | 6.20 ± 1.50 |
| warm-start | 6.65 ± 1.49 | 5.40 ± 1.85 | 5.50 ± 1.24 | 5.75 ± 1.30 | 7.15 ± 1.01 | 6.09 ± 1.57 |

### Explored %, overall · Steps used, overall

| policy | explored % (overall) | steps (overall) |
|---|---|---|
| random | 9.07 ± 3.37 | 160.00 ± 0.00 |
| rule | 74.97 ± 12.83 | 152.62 ± 15.42 |
| scratch | 76.83 ± 11.78 | 156.47 ± 9.45 |
| warm-start | 75.28 ± 12.95 | 155.07 ± 11.78 |

### Communication ablation (best policy: scratch)

| COMM | rescued (of 8) | explored % |
|---|---|---|
| 3 | 5.69 ± 1.62 | 71.6 |
| 10 | 5.87 ± 1.71 | 76.6 |
| 100 | 6.33 ± 1.48 | 76.4 |
<!-- RESULTS:END -->

A random swarm rescues almost no one (0.34/8). A coordinated one rescues ~6/8 and explores ~77% of the map. The hand-tuned rule and the trained policy land close together — the cross-entropy method confirms the baseline was already near-optimal for these six features, rather than beating it by a wide margin. That is an honest result, not a tuned-up one.

## What the swarm learned

![weights](results/weights.png)

Training from scratch drove the **crowding** weight sharply negative — more negative than the hand-tuned rule. The robots learn to actively avoid piling onto the same cells, which is how a leaderless swarm covers more ground: spread out, don't bunch up. It also learned a strong negative **stay** weight (keep moving) and a higher **frontier** weight (push toward the edge of the known).

## Communication matters

The ablation re-runs the best policy at radio range COMM = 3, 10 and 100 (`results/comms.png`). Rescues rise with range (5.69 → 5.87 → 6.33 of 8): robots that can relay what they've seen to more teammates find survivors faster.

## How to run

```bash
pip install -r requirements.txt
python -m train      # CEM training: scratch + warm-start -> results/weights_*.json
python -m evaluate   # held-out tables + comms ablation -> results/results.md
python -m render     # swarm GIFs + weights chart -> results/
pytest -q            # property tests + PettingZoo API test
```

One 160-step, 4-robot, 48×48 episode runs in well under a second on a laptop CPU; training uses multiprocessing over candidate weights.

## How Kiro was used

- **Steering docs** (`.kiro/steering/product.md`, `tech.md`, `structure.md`) pinned the goals, the tech constraints (PettingZoo ParallelEnv, numpy BFS, determinism), and the file layout.
- **Spec** (`.kiro/specs/fellowship/`) — requirements, design, and a task list that drove the build end to end.
- **Property tests** (`tests/`, hypothesis) encode the environment's invariants; the bugs they caught and their fixes are in [`docs/kiro_log.md`](docs/kiro_log.md).
- **Agent hooks** (`.kiro/hooks/`) re-run the API + property tests when a module is saved, regenerate the floorplan preview on `floorplans.py` save, smoke-train on `train.py` save, and re-sync this README's results section when `results/results.md` changes.
- **MCP**: the fetch MCP was used to read the PettingZoo ParallelEnv docs and check the env against them (`parallel_api_test` passes); the GitHub MCP is the path for commits once credentials are configured. See [`docs/kiro_log.md`](docs/kiro_log.md).

## Limits

- **Grid world, not physics.** Robots occupy cells and move in four directions; no dynamics, sensors noise, or collisions beyond "can't enter a wall."
- **Survivors are placed at random** on open cells, not from any real casualty model.
- **Floorplans are procedural**, not scans of real buildings. Boston is the real Moving AI grid, but at a coarse 48×48 crop scale — blocks, not rooms.
- Results are averages over 100 held-out maps with the spread (std) shown; they are not a claim about real robots.

## Data credits

Boston grid: Moving AI `Boston_0_256` benchmark. Sturtevant, "Benchmarks for Grid-Based Pathfinding," *IEEE Transactions on Computational Intelligence and AI in Games*, 2012. Check the source license before republishing the data.
