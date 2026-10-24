# Kiro build log — Fellowship

How Kiro was used, bugs caught by tests, and how they were fixed.

## How Kiro was used
- **Steering docs** (`.kiro/steering/product.md`, `tech.md`, `structure.md`) pinned the product goals, tech constraints, and file layout.
- **Spec** (`.kiro/specs/fellowship/requirements.md`, `design.md`, `tasks.md`) drove the build task by task.
- **Property tests** (hypothesis) in `tests/` caught invariant violations; see below.
- **Agent hooks** (`.kiro/hooks/fellowship-hooks.json`) — one v1-format file with five hooks: tests on save, floorplan-preview regen, smoke training, README sync, and an agent "steering check" that enforces the held-out-numbers rule from `product.md`. (The earlier four one-hook files used an invalid `trigger`/`action` shape and never loaded; they were replaced by this single valid file.)

Note on hook firing: the hooks run inside the Kiro editor's hook runtime (`PostFileSave`), not from this CLI session, so a fire cannot be observed from here. The JSON is validated and matches the documented v1 format; confirm a live fire by saving a `fellowship/*.py` file in the Kiro editor and watching the test hook run.

## MCP
Config: `.kiro/settings/mcp.json` (no secrets in the file; the GitHub token is referenced as the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable).
- **fetch** (`mcp-server-fetch`): read the official PettingZoo Parallel API docs (https://pettingzoo.farama.org/api/parallel/) and checked `env.py` against the documented contract — `reset(seed, options) -> (obs, infos)`, `step(actions) -> (obs, rewards, terminations, truncations, infos)`, per-agent `observation_space`/`action_space`, and the `agents`/`possible_agents` lifecycle. `pettingzoo.test.parallel_api_test` is the automated confirmation and passes.
- **github** (`@modelcontextprotocol/server-github`): used to publish the repo and manage branches/commits for the hazards-and-SAR work. The repo is **public on GitHub** (github.com/Zpopowitz/fellowship); `data/processed/` is committed so the gym runs without the raw data, which is re-downloadable via `scripts/download_boston_data.py`.

## Data
- `data/boston_map.csv` is the **real Moving AI Boston_0_256 grid** (65,536 rows = 256x256, y,x,open; 72.9% open). Cite Sturtevant, "Benchmarks for Grid-Based Pathfinding", IEEE TCIAIG 2012. A synthetic city-grid fallback in `maps._synthetic_boston` is used only if the CSV is absent.
- `data/floorplans/<kind>/NNN.png`: an optional pre-made pack of 240 PNGs (60 each of home/office/datacenter/factory), loaded by `floorplans.load_png_floorplans` as additional fixed maps.

## Bugs caught by tests
- **Test 5 (reachability)**: early drafts placed survivors before filtering the map to its largest 4-connected component, so a survivor could land in an isolated pocket. Fix: `generate_floorplan`/`crop_region` now return the largest component, and `_place_survivors` samples only from `open_grid`, which is already that component. Test 5 confirms every survivor and the staging cell are co-reachable for all kinds.
- **Test 2 (no false blocked)**: aftershocks turn open cells into walls mid-episode. A robot may legitimately hold a stale "blocked" memory only for a cell that is actually blocked now; the invariant checks against the *current* `open_grid`, so stale knowledge of a now-blocked cell is allowed and real false-blocking is caught.
- **PettingZoo parallel_api_test**: initially the env kept `self.agents` populated after the terminal step; the API test expects `agents` to empty once all agents are done. Fix: clear `self.agents = []` when `done`.

## Hazard bugs (found while making the gym submission-ready)
- **Gas plume had no direction** (`hazards.gas_plume`): every fire's contribution was written to the drone's OWN cell, so the field was symmetric — one step toward the fire and one step away read the same, and "stay" looked most dangerous. Fix: each cell now gets its own reading from that cell's wind-shifted distance to the nearest fire. Tests: `test_gas_reading_higher_toward_fire`, `test_gas_wind_toward_drone_raises_reading_at_drone`.
- **Drones walked into fire they could see**: known-fire cells were still legal moves. Fix: `features.legal_mask` now treats `known_fire` (and `known_flood`) cells as illegal, like walls; stay stays legal. Test: `test_known_fire_cell_is_illegal_move`.
- **Decisions used stale fire**: fire spread AFTER sensing in `step()`, so the observation handed to the policy missed cells that had just caught fire. Fix: after `spread_fire`, re-sense every active drone and re-`_communicate()` before building observations.
- **Disabled drones still sensed and relayed**: a drone lost to fire kept sensing, relaying maps, rescuing and counting toward crowding. Fix: `_sense` and `_rescue` skip disabled drones, and `comms.link_components` takes an `active` mask so a dead drone links to no one. Test: `test_disabled_drone_adds_no_new_knowledge`.
- **Fire spread too fast**: at the old `fire_spread_p=0.15`, ~36% of open cells burned by episode end and the swarm was wiped out every run. Tuned to 0.04 (~17% burned on held-out `sar` maps), documented in `product.md`.

## Validation so far
- `parallel_api_test` passes (100 cycles).
- 10/10 property tests pass; one 160-step, 4-robot episode runs in ~0.35s (target < 1s).
- Rule-based baseline rescues ~7/8 on office seed 5000; random rescues ~1/8.
