# Fellowship — Design

## Modules
- `maps.py` — Boston loader (`load_boston`), `crop_region`, `largest_component`, `sample_map`.
- `floorplans.py` — `gen_home/office/datacenter/factory`, `damage`, `generate_floorplan(kind, seed)`, `floorplans_preview`.
- `comms.py` — `link_components(positions, COMM)`, `merge_maps`, `merge_sightings`.
- `env.py` — `SwarmEnv(ParallelEnv)` + pure step helpers.
- `features.py` — `bfs_distance` (numpy dilation), `compute_features(robot_view, pos, teammates, visits)`.
- `policies.py` — `random_policy`, `rule_policy`, `linear_policy(w)`; all `(features5x6, mask5, rng)->action`.
- `train.py`, `evaluate.py`, `render.py`.

## Key representations
- A map is a bool numpy array `open_grid[H,W]` (True=open).
- A robot's knowledge map: uint8 `[H,W]` with 0 unknown / 1 open / 2 blocked.
- Position: `(y,x)`. Actions dy/dx: stay(0,0), N(-1,0), S(1,0), E(0,1), W(0,-1).

## BFS (numpy)
Multi-source BFS by iterated 4-neighbour dilation over a passable mask, distance cap 40.
`bfs_distance(passable, sources)` returns int array, unreachable = cap. Used for frontier/survivor progress; unknown cells are passable for planning.

## Determinism
Every randomized step draws from a `numpy.random.Generator` seeded from the episode seed. Map generation is a pure function of `(kind, seed)`. The env seeds its RNG in `reset(seed=...)`.

## Comms
Build an adjacency over robot positions (Chebyshev ≤ COMM), connected components via union-find. Each component merges knowledge maps with cell-wise max and unions survivor sightings, then writes the merged state back to every member.

## Features (per action a → target cell t)
- f0 new area: unknown cells in 5x5 around t / 25.
- f1 frontier progress: bfs(frontier, from cur) − bfs(frontier, from t).
- f2 survivor progress: same toward nearest known unrescued survivor, else 0.
- f3 crowding: Σ teammates max(0, 5−cheby(mate,t)) / 5.
- f4 revisits: −log(1 + visits[t]).
- f5 stay: 1 if a==stay.
Mask: off-map or known-blocked target → illegal.

## Score & metrics
`score = rescued + 0.5*explored_frac + ((T−steps)/T if rescued==K else 0)`. Per-episode metrics: rescued, explored_frac, steps, kind.

## Training (CEM)
Mean/std over 6 weights. Each iter: sample 16, evaluate on fixed train maps (2/kind), take elite 4, refit mean/std (std floor 0.1). 20 iters. Multiprocessing pool over candidates.

## Rendering
matplotlib figure with 3 axes; per frame draw walls, shade unknown (team union), robots, survivors (green if rescued), debris; save frames to an animated GIF via pillow.
