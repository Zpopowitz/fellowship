# SAR training dataset — overlap check, standardization, and how the swarm uses it

Built by `pipeline/build.py` (events, incl. fire) + `fellowship/sar_dataset.py`
(scenarios). This file answers three things you asked for: **is there overlap,
is it standardized, and how it is used.**

## The repo has three data layers (not two competing copies)

| Layer | Path | Role | Read by |
|---|---|---|---|
| Raw archive | `boston_data/` (~575 MB) | Exact source files + `MANIFEST.md` with sha256 per file | nobody at runtime; provenance only |
| Standardized raw | `data/raw/<dataset>/data.csv` | Source kits in one CSV shape | `pipeline/build.py` |
| Processed | `data/processed/` | One grid, one event schema, parquet | the swarm (`fellowship/sar_dataset.py`) |

Only **`data/processed/`** feeds training. `boston_data/` is kept as the honest
source-of-record (checksums, download log), not as a second input. This is why
both can stay in the repo without the swarm ever seeing a value twice.

## Overlap check (your "make sure there is no overlap")

**Between the two data trees.** Comparing `boston_data/` and `data/raw/` by
real-world source, exactly one dataset appears in both:

- **Boston street segments** — `boston_data/A1_street_segments_sam` (19,440
  GeoJSON features) and `data/raw/boston-streets` (19,440 rows). Same city
  dataset, two formats. **Resolution:** the pipeline reads only
  `data/raw/boston-streets`; `A1` is the archive copy. Not double-counted.

Everything else is unique to one tree (fire, hydrants, buildings, property,
permits only in `boston_data/`; 311, crashes, MBTA, tides only in `data/raw/`).

**Inside the training data.** The swarm's train/eval split cannot overlap by
construction: `fellowship/sar_dataset.dataset_split()` uses seeds `0..3999` for
train and `5000+` for eval, asserts no intersection, and leaves `4000..4999` as
a reserved gap. Same rule as the original `maps.py`. Verified: 4000 train, 1000
eval, intersection empty.

**Inside the events table.** `build_events()` drops duplicate `event_id`s per
source; fire rows that repeat across NFIRS lines collapse to one event by
`(incident_number, exposure_number, alarm_date)`.

## Standardization (your "make sure it is standardized")

Every hazard the swarm trains on is one row in `data/processed/events.parquet`,
same schema as all other events:

```
event_id, type, start_time, end_time, duration_min, lat, lng,
cell_row, cell_col, severity (1-5), source, confidence (0-1), details(JSON), raw
```

- **Grid:** one 256×256 grid, ~71 m cells, `data/processed/base/grid.json`.
  Every event is geocoded to a `(cell_row, cell_col)` on it.
- **New hazard types** added for SAR: `hazard.fire` (and `hazard.flood`, reserved).
  See `pipeline/event_types.py`.
- **Fire source:** `boston_data/D13_fire_incidents` (601,721 rows) →
  `pipeline/adapters/fire_incidents.py`. Kept categories: Fire (sev 5), Rescue
  (5), Hazardous Situation (4). **4,281** real incidents kept; the rest
  (blank / Public Service / No Emergency / Law Enforcement) are not rescue
  incidents and are dropped.
- **Flood source:** `data/raw/_excluded/fema/data.csv` (OpenFEMA MA disaster
  declarations) → `pipeline/adapters/fema_declarations.py`. Kept water incident
  types (Flood, Hurricane, Coastal/Severe Storm, Tsunami) whose designated area
  covers Boston's county (Suffolk) or is statewide. **25** real flood
  declarations kept, plus **1** NOAA tide `water.flood_risk` event.

## How the swarm uses it

`fellowship/sar_dataset.sample_scenario(seed)` returns, deterministically:

- a 48×48 region **cut from the real Boston street grid** (largest connected
  open area, so every cell is reachable);
- **survivors** placed on open cells, biased toward cells with real fire/flood
  activity (`hazard_pull`), because that is where a rescue swarm is dispatched;
- **fire / flood seed cells** — the cells in the crop with real incidents.

Same seed → same region, survivors, and hazards, everywhere.

## Honest limits

1. **Fire location is ZIP-level, not street-level.** The fire feed has no
   coordinates, only an address and ZIP, so each incident sits at its ZIP
   centroid (`location_method = "zip_centroid"`, same as 311). Fire *rate per
   area* is real; the exact cell is not. 4,281 fires land on 32 ZIP-centroid
   cells.
2. **Flood is county-level, not street-level.** FEMA declarations say a flood
   was declared for Suffolk County on a date — no location inside the county.
   So all 25 flood events sit at the grid centre
   (`location_method = "county_declaration"`, ~12 km precision) and act as a
   regional flood BASELINE, not an exact flood cell. For true per-cell flooding,
   a flood-extent dataset (FEMA NFHL flood-zone polygons, or storm-surge /
   burst-main records) would still need to be added — the declaration feed does
   not carry geometry.
3. **Grid, not physics.** 71 m cells, survivors placed by rule, no real fire
   spread model yet (fire/flood seed cells mark where hazard STARTS; a spread
   model is future work).
4. **The game map and the geo-grid are different grids.** The swarm's original
   `data/boston_map.csv` (Moving AI) is not georeferenced (REPORT.md). Real
   hazards can only be placed on the pipeline grid, which is why the SAR dataset
   uses that one.
