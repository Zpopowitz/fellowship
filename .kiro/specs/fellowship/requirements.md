# Fellowship — Requirements

## Problem
Train a decentralized robot swarm to find survivors in real places, with no central controller and no global map. Measure it honestly on maps it never trained on.

## Users
- Judges / readers who want to see a swarm that works without a leader.
- Developers who want to run training and evaluation themselves.

## Functional requirements

### R1 Real-place maps
- Load the Boston 256x256 grid; crop random 48x48 regions with ≥55% open cells.
- Generate damaged floorplans (home, office, datacenter, factory), 48x48, closed outer wall.
- Damage every floorplan (rubble piles); keep only the largest 4-connected open area.
- Every floorplan is ≥40% open after damage.
- `sample_map(kind, seed)` is deterministic; kinds: boston, home, office, datacenter, factory, mixed.
- Train seeds 0–3999, eval seeds ≥5000, never overlapping.

### R2 Environment
- PettingZoo ParallelEnv, passes `parallel_api_test`.
- N=4 robots start at the staging cell (open cell nearest top-left).
- K=8 survivors on distinct open cells. T=160 steps.
- Actions: stay/N/S/E/W. Blocked move = stay + mark blocked.
- Sensing: Chebyshev VIEW=2 window into own map (0 unknown/1 open/2 blocked) + survivor sightings.
- Rescue on occupying a survivor cell.
- Comms: Chebyshev COMM=10 links chain into components; component shares merged map (cell-wise max) + sightings.
- Aftershocks: every 25 steps block 4 random unoccupied open cells.
- Score = rescued + 0.5·explored_fraction + (T−steps)/T if all rescued.

### R3 Policy
- 6 features per action (new area, frontier progress, survivor progress, crowding, revisits, stay). Illegal actions masked.
- Policies: random, rule-based (fixed w), linear (argmax features@w). Shared interface.

### R4 Training
- Cross-entropy method, 6 weights, 20 iterations, 16 candidates, keep best 4, std floor 0.1.
- Score each candidate on 2 maps/kind from training seeds.
- Two variants: scratch (mean 0, std 1.5) and warm-start (rule-based mean, std 0.6).
- Save weights, learning curve, per-iteration log.

### R5 Evaluation
- random/rule/scratch/warm on 20 held-out maps/kind (100), same maps/seeds per policy.
- Report mean±std rescued, explored %, steps, per-kind and overall.
- Comms ablation COMM=3/10/100 with best policy.

### R6 Rendering
- `swarm.gif`: 3-panel (random, rule, best) per map kind + Boston, with walls, unexplored shading, robots, survivors (green when rescued), aftershock debris, step + rescued counters.
- `weights.png`: learned vs rule-based weights, plain labels.

### R7 Tests
- 10 property tests (hypothesis) + `parallel_api_test`.
- Log bugs + fixes in `docs/kiro_log.md`.

## Non-functional
- One 160-step, 4-robot, 48x48 episode < 1s on laptop CPU.
- Determinism: same seed+actions → identical trajectory everywhere.
- Honest reporting: held-out only, episodes + std stated.
