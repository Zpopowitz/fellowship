"""Rebuild data/processed/ from data/raw/.

    python pipeline/build.py                     # uses cached outside data
    python pipeline/build.py --refresh-external  # re-download outside data first

Outputs:
    data/processed/events.parquet
    data/processed/density.parquet
    data/processed/base/<layer>.geojson, base/grid.json
    data/processed/REPORT.md, sample_events.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from pipeline import external, grid  # noqa: E402
from pipeline.adapters import (  # noqa: E402
    boston_311,
    boston_streets,
    bridges,
    cambridge_crashes,
    colleges,
    eco_totem,
    fema_declarations,
    fire_incidents,
    hospitals,
    mbta_alerts,
    mbta_routes,
    mbta_stations,
    numina,
    tides,
    vision_zero,
)
from pipeline.common import PROCESSED, Result  # noqa: E402
from pipeline.event_types import EVENT_TYPES, detail_fields  # noqa: E402

ADAPTERS = [
    boston_streets, colleges, hospitals, bridges, mbta_stations, mbta_routes,
    vision_zero, cambridge_crashes, boston_311, mbta_alerts, tides, fire_incidents,
    fema_declarations,
    numina, eco_totem,
]

EVENT_COLUMNS = ["event_id", "type", "start_time", "end_time", "duration_min", "lat", "lng",
                 "cell_row", "cell_col", "severity", "source", "confidence", "details", "raw"]
DENSITY_COLUMNS = ["cell_row", "cell_col", "lat", "lng", "time_bucket", "metric", "value",
                   "source", "sensor_id", "interval_min"]

# Moved to data/raw/_excluded/ (not read by the pipeline). Reason shown in REPORT.md.
EXCLUDED = {
    "boston-map": "Not georeferenced: no lat/lng bounds, and it did not match the street "
                  "network in any orientation. Grid occupancy is built from boston-streets.",
    "bluebikes": "Monthly station-pair totals only; no time of day (coarse density dropped).",
    "cambridge-bikes": "Date + AM/PM only; no 15-minute timing (coarse density dropped).",
    "somerville-counts": "Year + AM/PM only (coarse density dropped); mostly north of the grid.",
    "permits": "Building permits (roofing, interior work) with ZIP-level location only.",
    "violations": "Property code violations with ZIP-level location only.",
    "fresh-pond": "Park visitor counts, not street traffic.",
    "ndbc": "Offshore buoy, outside the grid.",
    "charles": "River gauge in Waltham, outside the grid.",
    "berdo": "Building energy reporting.",
    "bridge-v2": "Tabletop robot-arm demonstrations, not street data.",
    "droid": "Tabletop robot-arm demonstrations, not street data.",
    "oxe": "Index of robot-learning datasets, not street data.",
    "cms-hospitals": "Hospital quality ratings.",
    "readmissions": "Hospital readmission rates.",
    "trials": "Clinical trials.",
    "places": "County health survey estimates.",
    "places-sleep": "County health survey estimates.",
    "openalex": "Research institutions.",
    "openalex-works": "Research papers.",
    "pubmed": "Research papers.",
    "emolt": "Offshore ocean temperature.",
    "ej": "Block-group demographics without geometry.",
    "neighborhoods": "Neighborhood demographics without geometry.",
    "fish": "Fish monitoring stations without coordinates.",
    "landfills": "Landfill solar projects without coordinates.",
    "utilities": "Electric utility per town.",
    "transmission": "Transmission lines without geometry.",
    "qcew": "Statewide employment statistics.",
    "onet": "Occupation descriptions.",
    "scorecard": "College cost and outcome statistics.",
    "ipeds": "Duplicates colleges.",
}


def place(frame: pd.DataFrame, res: Result) -> pd.DataFrame:
    """Add cell_row / cell_col and drop rows outside the grid (counted on ``res``)."""
    rows, cols = grid.cells_for(frame["lat"], frame["lng"])
    frame = frame.assign(cell_row=rows, cell_col=cols)
    outside = frame["cell_row"] < 0
    res.dropped["outside grid"] += int(outside.sum())
    return frame[~outside]


def build_events(results: list[Result]) -> pd.DataFrame:
    frames = []
    for res in results:
        f = place(res.frame, res)
        unknown = ~f["type"].isin(EVENT_TYPES)
        if unknown.any():
            raise ValueError(f"{res.name}: unknown event types {set(f.loc[unknown, 'type'])}")
        for etype, details in zip(f["type"], f["details"], strict=True):
            if list(details) != detail_fields(etype):
                raise ValueError(f"{res.name}: details for {etype} must be {detail_fields(etype)}")
        dup = f["event_id"].duplicated()
        res.dropped["duplicate row"] += int(dup.sum())
        frames.append(f[~dup])
    ev = pd.concat(frames, ignore_index=True)
    ev["details"] = ev["details"].map(lambda d: json.dumps(d, default=str))
    ev["duration_min"] = ev["duration_min"].astype("float64")
    ev["severity"] = ev["severity"].astype("int8")
    ev["confidence"] = ev["confidence"].astype("float64")
    ev["cell_row"] = ev["cell_row"].astype("int16")
    ev["cell_col"] = ev["cell_col"].astype("int16")
    return ev[EVENT_COLUMNS].sort_values(["start_time", "event_id"]).reset_index(drop=True)


def build_density(results: list[Result]) -> pd.DataFrame:
    frames = []
    for res in results:
        f = place(res.frame, res)
        dup = f.duplicated(["sensor_id", "time_bucket", "metric"])
        res.dropped["duplicate measurement"] += int(dup.sum())
        frames.append(f[~dup])
    d = pd.concat(frames, ignore_index=True)
    d["cell_row"] = d["cell_row"].astype("int16")
    d["cell_col"] = d["cell_col"].astype("int16")
    d["interval_min"] = d["interval_min"].astype("int16")
    return d[DENSITY_COLUMNS].sort_values(["time_bucket", "sensor_id", "metric"]) \
        .reset_index(drop=True)


def build_base(results: list[Result], out_dir: Path) -> tuple[dict[str, int], set]:
    """Write one GeoJSON per layer; return feature counts and the street cells."""
    out_dir.mkdir(parents=True, exist_ok=True)
    counts, street_cells = {}, set()
    for res in results:
        for layer, features in res.layers.items():
            kept = []
            for f in features:
                cells = grid.geometry_cells(f["geometry"])
                if not cells:
                    res.dropped["outside grid"] += 1
                    continue
                g = f["geometry"]
                pts = ([g["coordinates"]] if g["type"] == "Point"
                       else [p for line in g["coordinates"] for p in line])
                props = dict(f["properties"])
                props["lng"] = round(sum(p[0] for p in pts) / len(pts), 6)
                props["lat"] = round(sum(p[1] for p in pts) / len(pts), 6)
                if g["type"] == "Point":
                    props["cell_row"], props["cell_col"] = cells[0]
                else:
                    props["cells"] = cells
                kept.append({"type": "Feature", "geometry": g, "properties": props})
                if layer == "streets":
                    street_cells.update(map(tuple, cells))
            (out_dir / f"{layer}.geojson").write_text(json.dumps(
                {"type": "FeatureCollection", "name": layer, "source": res.name,
                 "grid": grid.describe(), "features": kept}))
            counts[layer] = len(kept)
            res.notes.append(f"{len(kept)} features -> base/{layer}.geojson")
    return counts, street_cells


def write_grid(street_cells: set, out_dir: Path) -> None:
    rows = ["".join("1" if (r, c) in street_cells else "0" for c in range(grid.SIZE))
            for r in range(grid.SIZE)]
    meta = grid.describe() | {
        "occupancy": "1 = cell contains a Boston street centerline, 0 = no street",
        "open_cells": len(street_cells),
        "rows_data": rows,
    }
    (out_dir / "grid.json").write_text(json.dumps(meta))


def sample_events(ev: pd.DataFrame, n: int = 50) -> list[dict]:
    """Round-robin across (source, type) so every kind of event shows up."""
    groups = [g.sample(frac=1, random_state=7) for _, g in ev.groupby(["source", "type"])]
    picked, i = [], 0
    while len(picked) < n and any(i < len(g) for g in groups):
        picked += [g.iloc[i] for g in groups if i < len(g)][: n - len(picked)]
        i += 1
    out = []
    for r in picked:
        rec = r.to_dict()
        rec["details"] = json.loads(rec["details"])
        out.append({k: (None if isinstance(v, float) and pd.isna(v) else v)
                    for k, v in rec.items()})
    return out


def write_report(results: list[Result], ev: pd.DataFrame, dens: pd.DataFrame,
                 base_counts: dict[str, int], open_cells: int) -> str:
    out_rows = Counter(ev["source"]) + Counter(dens["source"])
    lines = [
        "# Processed data report",
        "",
        f"Built {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC by `python pipeline/build.py`.",
        "",
        "## Grid",
        "",
        f"- {grid.SIZE} x {grid.SIZE} cells over lat {grid.MIN_LAT}..{grid.MAX_LAT}, "
        f"lng {grid.MIN_LNG}..{grid.MAX_LNG} (extent of `boston-streets`).",
        f"- Cell size ~{grid.CELL_HEIGHT_M:.1f} m (N-S) x {grid.CELL_WIDTH_M:.1f} m (E-W). "
        "Row 0 = north edge, col 0 = west edge.",
        f"- Occupancy (`base/grid.json`): {open_cells} cells contain a street.",
        "- The Moving AI `boston-map` was **not** used: it has no lat/lng bounds, and compared "
        "with the street raster it scored ~37% cell agreement in every orientation (no better "
        "than chance), so it is not a georeferenced map of this area.",
        "- **Occupancy covers the City of Boston only.** The grid box also takes in parts of "
        "Cambridge, Brookline, Somerville and Chelsea, but `boston-streets` has no streets "
        "there, so those cells read as blocked even though events (Cambridge crashes, the "
        "Eco-Totem) land in them.",
        "",
        "## Rows in vs out",
        "",
        "| Dataset | Kind | Rows in | Rows out | Dropped (reason: count) |",
        "|---|---|---:|---:|---|",
    ]
    for res in results:
        n_out = sum(base_counts[layer] for layer in res.layers) if res.kind == "base" \
            else out_rows[res.name]
        dropped = "; ".join(f"{k}: {v}" for k, v in res.dropped.items() if v) or "none"
        lines.append(f"| {res.name} | {res.kind} | {res.rows_in} | {n_out} | {dropped} |")
    lines += [
        "",
        "`mbta-alerts` can output more rows than it takes in: an alert without a named stop "
        "becomes one event per grid cell holding a stop on its routes (same "
        "`details.alert_id`).",
        "",
        "Duplicates are removed by source record. A few 311 events look identical in the "
        "output because separate cases were filed within the same second in the same ZIP; "
        "they are distinct source records (microsecond timestamps differ) and are kept.",
        "",
        "## Time range",
        "",
        "| Source | First | Last |",
        "|---|---|---|",
    ]
    for src, g in ev.groupby("source"):
        lines.append(f"| {src} (events) | {g['start_time'].min()} | {g['start_time'].max()} |")
    for src, g in dens.groupby("source"):
        lines.append(f"| {src} (density) | {g['time_bucket'].min()} | {g['time_bucket'].max()} |")
    lines += ["", "## Events by type", "", "| Type | Count | Sources |", "|---|---:|---|"]
    for etype in EVENT_TYPES:
        g = ev[ev["type"] == etype]
        lines.append(f"| {etype} | {len(g)} | {', '.join(sorted(g['source'].unique()))} |")
    lines += ["", "## Density by metric", "", "| Metric | Rows | Sources |", "|---|---:|---|"]
    for metric, g in dens.groupby("metric"):
        lines.append(f"| {metric} | {len(g)} | {', '.join(sorted(g['source'].unique()))} |")
    lines += ["", "## Severity (1-5) per source", ""]
    lines += [f"- **{r.name}**: {r.severity_rule}" for r in results if r.severity_rule]
    lines += [
        "",
        "Confidence: official / police / sensor feeds 0.9-0.95; 311 citizen reports 0.6. "
        "Location quality is separate: see `details.location_method` and "
        "`details.location_precision_m`.",
        "",
        "## Columns not mapped",
        "",
    ]
    lines += [f"- **{r.name}**: {', '.join(r.unmapped)}" for r in results if r.unmapped]
    lines += ["", "## Notes", ""]
    for r in results:
        lines += [f"- **{r.name}**: {n}" for n in r.notes]
    lines += ["", "## Excluded datasets (in `data/raw/_excluded/`)", ""]
    lines += [f"- **{k}**: {v}" for k, v in EXCLUDED.items()]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh-external", action="store_true",
                    help="re-download outside data (MBTA, ZIPs, NBI, NOAA, MassGIS)")
    args = ap.parse_args()
    if args.refresh_external:
        for p in sorted(external.EXTERNAL.glob("**/*.json")) + [external.EXTERNAL / "nbi_MA22.txt"]:
            p.unlink(missing_ok=True)

    results = []
    for mod in ADAPTERS:
        print(f"  {mod.NAME} ...", flush=True)
        results.append(mod.run())
    by_kind = {k: [r for r in results if r.kind == k] for k in ("base", "events", "density")}

    PROCESSED.mkdir(parents=True, exist_ok=True)
    base_counts, street_cells = build_base(by_kind["base"], PROCESSED / "base")
    write_grid(street_cells, PROCESSED / "base")
    ev = build_events(by_kind["events"])
    dens = build_density(by_kind["density"])
    ev.to_parquet(PROCESSED / "events.parquet", index=False)
    dens.to_parquet(PROCESSED / "density.parquet", index=False)
    (PROCESSED / "sample_events.json").write_text(
        json.dumps(sample_events(ev), indent=2, default=str) + "\n")
    (PROCESSED / "REPORT.md").write_text(
        write_report(results, ev, dens, base_counts, len(street_cells)))

    print(f"events: {len(ev)}  density: {len(dens)}  base layers: {base_counts}")
    print(f"wrote {PROCESSED}")


if __name__ == "__main__":
    main()
