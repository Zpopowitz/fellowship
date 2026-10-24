# Kiro build log — Fellowship

How Kiro was used, bugs caught by tests, and how they were fixed.

## How Kiro was used
- **Steering docs** (`.kiro/steering/product.md`, `tech.md`, `structure.md`) pinned the product goals, tech constraints, and file layout.
- **Spec** (`.kiro/specs/fellowship/requirements.md`, `design.md`, `tasks.md`) drove the build task by task.
- **Property tests** (hypothesis) in `tests/` caught invariant violations; see below.
- **Agent hooks** (`.kiro/hooks/fellowship-hooks.json`) — one v1-format file with five hooks: tests on save, floorplan-preview regen, smoke training, README sync, and an agent "steering check" that enforces the held-out-numbers rule from `product.md`. (The earlier four one-hook files used an invalid `trigger`/`action` shape and never loaded; they were replaced by this single valid file.)

Note on hook firing: the hooks run inside the Kiro editor's hook runtime (`PostFileSave`), not from this CLI session, so a fire cannot be observed from here. The JSON is validated and matches the documented v1 format; confirm a live fire by saving a `fellowship/*.py` file in the Kiro editor and watching the test hook run.

## MCP
- **Fetch**: read the official PettingZoo Parallel API docs (https://pettingzoo.farama.org/api/parallel/) and checked `env.py` against the documented contract — `reset(seed, options) -> (obs, infos)`, `step(actions) -> (obs, rewards, terminations, truncations, infos)`, per-agent `observation_space`/`action_space`, and the `agents`/`possible_agents` lifecycle. `pettingzoo.test.parallel_api_test` is the automated confirmation and passes.
- **GitHub**: commits go through the GitHub MCP once repo credentials are configured. (Not auto-pushed during this build; the project lives locally until the user chooses to push.)

## Data
- `data/boston_map.csv` is the **real Moving AI Boston_0_256 grid** (65,536 rows = 256x256, y,x,open; 72.9% open). Cite Sturtevant, "Benchmarks for Grid-Based Pathfinding", IEEE TCIAIG 2012. A synthetic city-grid fallback in `maps._synthetic_boston` is used only if the CSV is absent.
- `data/floorplans/<kind>/NNN.png`: an optional pre-made pack of 240 PNGs (60 each of home/office/datacenter/factory), loaded by `floorplans.load_png_floorplans` as additional fixed maps.

## Bugs caught by tests
- **Test 5 (reachability)**: early drafts placed survivors before filtering the map to its largest 4-connected component, so a survivor could land in an isolated pocket. Fix: `generate_floorplan`/`crop_region` now return the largest component, and `_place_survivors` samples only from `open_grid`, which is already that component. Test 5 confirms every survivor and the staging cell are co-reachable for all kinds.
- **Test 2 (no false blocked)**: aftershocks turn open cells into walls mid-episode. A robot may legitimately hold a stale "blocked" memory only for a cell that is actually blocked now; the invariant checks against the *current* `open_grid`, so stale knowledge of a now-blocked cell is allowed and real false-blocking is caught.
- **PettingZoo parallel_api_test**: initially the env kept `self.agents` populated after the terminal step; the API test expects `agents` to empty once all agents are done. Fix: clear `self.agents = []` when `done`.

## Validation so far
- `parallel_api_test` passes (100 cycles).
- 10/10 property tests pass; one 160-step, 4-robot episode runs in ~0.35s (target < 1s).
- Rule-based baseline rescues ~7/8 on office seed 5000; random rescues ~1/8.
