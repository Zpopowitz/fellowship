# Boston data pipeline

Turns the Hackachusetts starter kits in `data/raw/` into one consistent format on a
shared 256 x 256 Boston grid (~71 m cells).

```bash
python3 -m venv .venv && .venv/bin/pip install -r pipeline/requirements.txt
.venv/bin/python pipeline/build.py                     # rebuild data/processed/
.venv/bin/python pipeline/build.py --refresh-external  # also re-download outside data
```

Do not run the kits' `fetch.py` / `fetch.js`: they download a 100-row preview and
would overwrite the full `data.csv`.

## Outputs (`data/processed/`)

| File | What |
|---|---|
| `events.parquet` | One row per event: `event_id, type, start_time, end_time, duration_min, lat, lng, cell_row, cell_col, severity (1-5), source, confidence (0-1), details (JSON), raw` |
| `density.parquet` | One row per measurement: `cell_row, cell_col, lat, lng, time_bucket (15 min, UTC), metric, value, source, sensor_id, interval_min` |
| `base/*.geojson` | Streets, bridges, transit stations and routes, hospitals, colleges; each feature has `name`, `type`, and its grid cell(s) |
| `base/grid.json` | Grid bounds and street occupancy (1 = street in cell) |
| `REPORT.md` | Rows in/out per dataset, drop reasons, time ranges, counts by type, severity rules |
| `sample_events.json` | 50 example events |

## Layout

- `build.py`: entry point
- `grid.py`: lat/lng to `(row, col)`; row 0 is the north edge
- `event_types.py`: the controlled event types and their `details` fields
- `adapters/<dataset>.py`: one per kept dataset
- `external.py`: downloads coordinates the kits left out (MBTA, ZIPs, NBI, NOAA, MassGIS)
  into `data/raw/_external/`
- `locations.py`: hand-checked sensor coordinates, with sources

Datasets not useful at street level are in `data/raw/_excluded/`; `REPORT.md` lists why.

## Note on `data/boston_map.csv`

The grid here is **not** the Moving AI `Boston_0_256` map used by the environment.
That map has no lat/lng bounds and did not line up with the real street network, so
these events cannot be placed onto it directly. See `REPORT.md`.
