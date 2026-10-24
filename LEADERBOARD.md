# Fellowship Gym — baseline leaderboard

12 held-out maps per (task, map family), seeds 5000+, the same maps for every policy. Mean ± std. Rescued of 8, drones lost of 4. 'trained' = the CEM situation model for that family (outdoor for streets, indoor for buildings). n_maps is 12 to keep the full sweep under ~10 minutes.

## explore

| Policy | Map family | Rescued /8 | Explored | Drones lost /4 | In-hazard |
|---|---|---|---|---|---|
| random | streets_real | 0.8 ± 0.6 | 11% ± 6 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| rule | streets_real | 7.2 ± 0.6 | 88% ± 6 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| trained | streets_real | 7.4 ± 0.9 | 89% ± 5 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| random | streets_grid | 0.5 ± 0.5 | 11% ± 4 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| rule | streets_grid | 6.4 ± 1.8 | 77% ± 14 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| trained | streets_grid | 6.4 ± 1.7 | 80% ± 14 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| random | buildings | 0.6 ± 0.6 | 9% ± 3 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| rule | buildings | 6.2 ± 1.3 | 70% ± 15 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| trained | buildings | 6.2 ± 1.3 | 69% ± 15 | 0.0 ± 0.0 | 0.0 ± 0.0 |

## rescue

| Policy | Map family | Rescued /8 | Explored | Drones lost /4 | In-hazard |
|---|---|---|---|---|---|
| random | streets_real | 0.8 ± 0.6 | 11% ± 6 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| rule | streets_real | 7.2 ± 0.6 | 88% ± 6 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| trained | streets_real | 7.4 ± 0.9 | 89% ± 5 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| random | streets_grid | 0.5 ± 0.5 | 11% ± 4 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| rule | streets_grid | 6.4 ± 1.8 | 77% ± 14 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| trained | streets_grid | 6.4 ± 1.7 | 80% ± 14 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| random | buildings | 0.6 ± 0.6 | 9% ± 3 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| rule | buildings | 6.2 ± 1.3 | 70% ± 15 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| trained | buildings | 6.2 ± 1.3 | 69% ± 15 | 0.0 ± 0.0 | 0.0 ± 0.0 |

## rescue_fire

| Policy | Map family | Rescued /8 | Explored | Drones lost /4 | In-hazard |
|---|---|---|---|---|---|
| random | streets_real | 0.7 ± 0.6 | 8% ± 6 | 0.8 ± 1.5 | 2.2 ± 1.7 |
| rule | streets_real | 5.0 ± 2.2 | 60% ± 22 | 2.7 ± 1.2 | 1.2 ± 1.3 |
| trained | streets_real | 5.4 ± 2.4 | 64% ± 26 | 2.7 ± 1.2 | 1.2 ± 1.3 |
| random | streets_grid | 0.4 ± 0.5 | 10% ± 4 | 1.0 ± 1.4 | 2.1 ± 1.0 |
| rule | streets_grid | 4.8 ± 1.5 | 62% ± 15 | 2.3 ± 1.2 | 1.4 ± 0.6 |
| trained | streets_grid | 5.1 ± 1.5 | 64% ± 17 | 2.2 ± 1.6 | 1.2 ± 0.6 |
| random | buildings | 0.7 ± 0.7 | 8% ± 3 | 0.5 ± 1.0 | 1.7 ± 1.5 |
| rule | buildings | 4.4 ± 1.3 | 57% ± 14 | 1.9 ± 1.4 | 1.3 ± 1.2 |
| trained | buildings | 4.0 ± 1.3 | 57% ± 12 | 1.9 ± 1.3 | 1.4 ± 1.3 |

## rescue_flood

| Policy | Map family | Rescued /8 | Explored | Drones lost /4 | In-hazard |
|---|---|---|---|---|---|
| random | streets_real | 0.7 ± 0.6 | 8% ± 6 | 0.8 ± 1.5 | 2.0 ± 1.6 |
| rule | streets_real | 5.2 ± 2.4 | 62% ± 23 | 2.3 ± 1.3 | 1.1 ± 1.4 |
| trained | streets_real | 5.6 ± 2.5 | 66% ± 26 | 2.3 ± 1.4 | 1.1 ± 1.4 |
| random | streets_grid | 0.5 ± 0.5 | 10% ± 4 | 0.2 ± 0.6 | 1.2 ± 0.6 |
| rule | streets_grid | 5.4 ± 1.6 | 68% ± 12 | 0.3 ± 0.8 | 1.2 ± 0.6 |
| trained | streets_grid | 5.2 ± 1.5 | 67% ± 12 | 0.3 ± 0.7 | 1.2 ± 0.6 |
| random | buildings | 0.5 ± 0.6 | 9% ± 3 | 0.0 ± 0.0 | 1.3 ± 0.7 |
| rule | buildings | 5.0 ± 1.2 | 59% ± 17 | 0.6 ± 0.9 | 1.2 ± 0.9 |
| trained | buildings | 5.0 ± 1.2 | 59% ± 16 | 0.8 ± 1.2 | 1.2 ± 0.9 |

