# Processed data report

Built 2026-10-24 18:08 UTC by `python pipeline/build.py`.

## Grid

- 256 x 256 cells over lat 42.232..42.3956, lng -71.1847..-70.9633 (extent of `boston-streets`).
- Cell size ~71.1 m (N-S) x 71.1 m (E-W). Row 0 = north edge, col 0 = west edge.
- Occupancy (`base/grid.json`): 15883 cells contain a street.
- The Moving AI `boston-map` was **not** used: it has no lat/lng bounds, and compared with the street raster it scored ~37% cell agreement in every orientation (no better than chance), so it is not a georeferenced map of this area.
- **Occupancy covers the City of Boston only.** The grid box also takes in parts of Cambridge, Brookline, Somerville and Chelsea, but `boston-streets` has no streets there, so those cells read as blocked even though events (Cambridge crashes, the Eco-Totem) land in them.

## Rows in vs out

| Dataset | Kind | Rows in | Rows out | Dropped (reason: count) |
|---|---|---:|---:|---|
| boston-streets | base | 19440 | 18245 | no geometry in source: 1195 |
| colleges | base | 206 | 55 | outside grid: 151 |
| hospitals | base | 103 | 24 | outside grid: 79 |
| bridges | base | 5252 | 559 | outside grid: 4693 |
| mbta-stations | base | 170 | 135 | station name not matched to an MBTA stop: 3; duplicate station row: 14; outside grid: 18 |
| mbta-routes | base | 8 | 8 | none |
| vision-zero | events | 44986 | 44982 | outside grid: 4 |
| cambridge-crashes | events | 17230 | 8583 | no coordinates in source: 8352; unparseable or ambiguous (DST) time: 1; outside grid: 292; duplicate row: 2 |
| boston-311 | events | 5000 | 4273 | service type not street-level: 714; ZIP missing or not a Boston ZIP polygon: 13 |
| mbta-alerts | events | 130 | 1121 | no affected stop inside the grid: 41; effect not a disruption: PARKING_ISSUE: 5; effect not a disruption: EXTRA_SERVICE: 1; effect not a disruption: SCHEDULE_CHANGE: 3; effect not a disruption: NOTICE: 6; effect not a disruption: TRACK_CHANGE: 1 |
| tides | events | 744 | 1 | hourly reading below flood threshold: 743 |
| fire-incidents | events | 601721 | 4281 | category not a rescue incident: 597371; ZIP missing or not a Boston ZIP polygon: 68; outside grid: 1 |
| fema-declarations | events | 415 | 25 | incident type not water-related: 157; designated area does not cover Boston (Suffolk): 233 |
| numina | density | 245555 | 245555 | none |
| eco-totem | density | 17123 | 17120 | duplicate measurement: 3 |

`mbta-alerts` can output more rows than it takes in: an alert without a named stop becomes one event per grid cell holding a stop on its routes (same `details.alert_id`).

Duplicates are removed by source record. A few 311 events look identical in the output because separate cases were filed within the same second in the same ZIP; they are distinct source records (microsecond timestamps differ) and are kept.

## Time range

| Source | First | Last |
|---|---|---|
| boston-311 (events) | 2026-10-08T07:34:35Z | 2026-10-18T10:15:27Z |
| cambridge-crashes (events) | 2015-01-01T09:14:00Z | 2026-09-30T15:30:00Z |
| fema-declarations (events) | 1954-09-02T00:00:00Z | 2023-09-15T00:00:00Z |
| fire-incidents (events) | 2026-03-10T10:46:05Z | 2026-10-18T01:00:16Z |
| mbta-alerts (events) | 2026-07-22T00:46:13Z | 2026-10-18T20:14:02Z |
| tides (events) | 2024-08-20T04:00:00Z | 2024-08-20T04:00:00Z |
| vision-zero (events) | 2015-01-01T05:24:27Z | 2026-09-01T00:03:10Z |
| eco-totem (density) | 2024-01-01T05:00:00Z | 2024-07-01T03:45:00Z |
| numina (density) | 2020-07-10T04:00:00Z | 2021-05-01T03:00:00Z |

## Events by type

| Type | Count | Sources |
|---|---:|---|
| road.crash | 53565 | cambridge-crashes, vision-zero |
| road.pothole | 142 | boston-311 |
| road.construction | 105 | boston-311 |
| road.illegal_parking | 826 | boston-311 |
| road.signal_issue | 129 | boston-311 |
| road.sign_issue | 110 | boston-311 |
| road.markings_faded | 43 | boston-311 |
| street.debris | 1272 | boston-311 |
| street.fallen_tree | 48 | boston-311 |
| street.animal | 193 | boston-311 |
| street.emergency | 12 | boston-311 |
| sidewalk.blocked | 971 | boston-311 |
| sidewalk.damaged | 187 | boston-311 |
| streetlight.outage | 235 | boston-311 |
| transit.breakdown | 0 |  |
| transit.delay | 691 | mbta-alerts |
| transit.suspension | 5 | mbta-alerts |
| transit.shuttle | 0 |  |
| transit.detour | 361 | mbta-alerts |
| transit.stop_moved | 9 | mbta-alerts |
| transit.station_closure | 24 | mbta-alerts |
| transit.station_issue | 5 | mbta-alerts |
| transit.accessibility | 17 | mbta-alerts |
| transit.service_change | 9 | mbta-alerts |
| water.flood_risk | 1 | tides |
| hazard.fire | 4281 | fire-incidents |
| hazard.flood | 25 | fema-declarations |

## Density by metric

| Metric | Rows | Sources |
|---|---:|---|
| bikes | 66231 | eco-totem, numina |
| buses | 49111 | numina |
| cars | 49111 | numina |
| pedestrians | 49111 | numina |
| trucks | 49111 | numina |

## Severity (1-5) per source

- **vision-zero**: No injury field is published. Crashes involving a pedestrian or cyclist = 4, motor-vehicle only = 3.
- **cambridge-crashes**: No injury field is published. Base 3; 4 when a pedestrian or cyclist is involved.
- **boston-311**: Fixed severity per 311 service type (see SERVICE_MAP in pipeline/adapters/boston_311.py): e.g. litter 1, illegal parking 2, pothole 3, blocked sidewalk / fallen tree / signal knockdown 4, missing manhole cover / general emergency 5.
- **mbta-alerts**: MBTA publishes severity 0-10; mapped as ceil(mbta / 2), clamped to 1-5.
- **tides**: Peak level: NOAA minor flood = 3, moderate = 4, major = 5.
- **fire-incidents**: Fire category = 5, Rescue = 5, Hazardous Situation = 4. Other categories (Public Service, No Emergency, Law Enforcement Support, blank) are not rescue incidents and are dropped.
- **fema-declarations**: FEMA declaration: Flood / Hurricane / Tsunami = 5, Coastal Storm / Severe Storm = 4. County-level only; non-water incident types dropped.

Confidence: official / police / sensor feeds 0.9-0.95; 311 citizen reports 0.6. Location quality is separate: see `details.location_method` and `details.location_precision_m`.

## Columns not mapped

- **boston-streets**: cost_forward, cost_back (unitless SAM travel cost; only -1 = not traversable is kept), shape_length (degrees; replaced by length_m)
- **colleges**: zip, town (redundant with city / coordinates)
- **hospitals**: county (redundant with coordinates)
- **bridges**: county (redundant with coordinates)
- **vision-zero**: cross_street_2 (second cross street; kept only in source)
- **cambridge-crashes**: day (derivable from start_time)
- **boston-311**: case_topic (identical to service_name), city_council_district, ward (administrative areas)
- **fire-incidents**: incident_number, exposure_number (ids; folded into event_id), incident_type, incident_description, incident_detail (NFIRS code text), address, district, city_section (street address not geocoded; ZIP used), location_subtype, property_description (free text)
- **fema-declarations**: declarationTitle (free text, kept only in source), declarationType (DR/EM/FM declaration class)
- **numina**: metric (always 'count')
- **eco-totem**: entries, exits (sum to total; the city does not say which direction each is), day (derivable)

## Notes

- **boston-streets**: 18245 features -> base/streets.geojson
- **colleges**: 55 features -> base/colleges.geojson
- **hospitals**: 24 features -> base/hospitals.geojson
- **bridges**: 559 features -> base/bridges.geojson
- **mbta-stations**: unmatched station: Airport Terminal B2
- **mbta-stations**: unmatched station: Airport Terminal B1
- **mbta-stations**: unmatched station: 88 Black Falcon Ave
- **mbta-stations**: 135 features -> base/transit_stations.geojson
- **mbta-routes**: 8 features -> base/transit_routes.geojson
- **boston-311**: Service types dropped as not street-level: Other (151), Illegal Graffiti (86), Park Groundskeeping (71), New / Modified Sign Request (63), Pruning Request (59), Sticker Request (42), Broken Park Equipment (39), Unauthorized Signage (36), Tree or Stump Removal (34), Request New Markings (20), Install New Signal (19), Overgrown Weeds (17), Parks General Request (14), Parking Meter Repairs (13), Ballfield Issue (11), Code Enforcement Collection (7), Request New Crosswalk (7), Planting Request (6), Lost Pet (5), Locked Gates (4), Park Suggestions (3), OPC Public Inquiry (2), Illegal Yard Parking (2), Moving Permits (1), Fences/Guardrails/Bollards (1), Park Overflowing Trash Can (1).
- **boston-311**: No case id or close date in the slice: event_id is a row hash and end_time is null.
- **mbta-alerts**: start_time is the alert's last-updated time; the snapshot has no active period, so end_time is null.
- **tides**: Thresholds (m above MLLW): minor 3.757, moderate 4.025, major 4.425. The gauge sits on the harbor; flood risk applies to the waterfront, not just its one grid cell.
- **fire-incidents**: Placed at ZIP centroid (no coordinates in the feed), same method as boston-311. Fire density per ZIP is real; exact street location is not available, so the SAR builder treats this as a per-ZIP fire rate.
- **fire-incidents**: Duplicate incident rows (same incident reported on several NFIRS lines) collapse to one event by (incident_number, exposure_number, alarm_date).
- **fema-declarations**: COUNTY-LEVEL ONLY: declarations carry no coordinates, so every flood event sits at the grid centre with location_method='county_declaration'. Used as a regional flood baseline, never an exact flood cell.
- **fema-declarations**: Kept water incident types: Flood, Hurricane, Coastal Storm, Severe Storm, Tsunami; areas covering Boston (Suffolk) or statewide.
- **numina**: Sensor sites: Jackson Sq (Centre St / Lamartine St), Northern Ave (Seaport), Tremont St / Boylston St. Coverage 2020-07 to 2021-04.
- **eco-totem**: Location approximate (+/-150 m): Approximate: Broadway between Ames St and Galileo Galilei Way.

## Excluded datasets (in `data/raw/_excluded/`)

- **boston-map**: Not georeferenced: no lat/lng bounds, and it did not match the street network in any orientation. Grid occupancy is built from boston-streets.
- **bluebikes**: Monthly station-pair totals only; no time of day (coarse density dropped).
- **cambridge-bikes**: Date + AM/PM only; no 15-minute timing (coarse density dropped).
- **somerville-counts**: Year + AM/PM only (coarse density dropped); mostly north of the grid.
- **permits**: Building permits (roofing, interior work) with ZIP-level location only.
- **violations**: Property code violations with ZIP-level location only.
- **fresh-pond**: Park visitor counts, not street traffic.
- **ndbc**: Offshore buoy, outside the grid.
- **charles**: River gauge in Waltham, outside the grid.
- **berdo**: Building energy reporting.
- **bridge-v2**: Tabletop robot-arm demonstrations, not street data.
- **droid**: Tabletop robot-arm demonstrations, not street data.
- **oxe**: Index of robot-learning datasets, not street data.
- **cms-hospitals**: Hospital quality ratings.
- **readmissions**: Hospital readmission rates.
- **trials**: Clinical trials.
- **places**: County health survey estimates.
- **places-sleep**: County health survey estimates.
- **openalex**: Research institutions.
- **openalex-works**: Research papers.
- **pubmed**: Research papers.
- **emolt**: Offshore ocean temperature.
- **ej**: Block-group demographics without geometry.
- **neighborhoods**: Neighborhood demographics without geometry.
- **fish**: Fish monitoring stations without coordinates.
- **landfills**: Landfill solar projects without coordinates.
- **utilities**: Electric utility per town.
- **transmission**: Transmission lines without geometry.
- **qcew**: Statewide employment statistics.
- **onet**: Occupation descriptions.
- **scorecard**: College cost and outcome statistics.
- **ipeds**: Duplicates colleges.
