# Fellowship — hazard evaluation (held-out)

24 held-out maps per situation (seeds 5000+), the same maps and seeds for every policy. Mean ± std. Rescued of 8, drones lost of 4. 'Abandoned' = survivors left in fire or flood at the end. 'Burned' = fraction of open cells on fire at episode end.

## indoor

| Policy | Rescued /8 | Drones lost /4 | Abandoned | Firefighter score | Burned % |
|---|---|---|---|---|---|
| random | 0.6 ± 0.7 | 0.3 ± 0.9 | 1.8 ± 1.2 | -1.0 ± 10.4 | 12 ± 4 |
| blind | 4.4 ± 1.8 | 2.3 ± 1.2 | 1.2 ± 1.0 | 37.6 ± 18.6 | 11 ± 4 |
| rule | 4.5 ± 1.8 | 1.9 ± 1.3 | 1.4 ± 1.1 | 37.7 ± 20.2 | 12 ± 4 |
| hand-set (indoor) | 4.2 ± 1.6 | 2.0 ± 1.4 | 1.2 ± 1.1 | 36.4 ± 17.9 | 11 ± 4 |
| trained | 4.2 ± 2.0 | 2.0 ± 1.4 | 1.4 ± 1.1 | 34.7 ± 20.8 | 11 ± 4 |

## outdoor

| Policy | Rescued /8 | Drones lost /4 | Abandoned | Firefighter score | Burned % |
|---|---|---|---|---|---|
| random | 0.5 ± 0.6 | 1.0 ± 1.4 | 2.0 ± 1.8 | -4.0 ± 9.9 | 21 ± 11 |
| blind | 6.0 ± 2.1 | 2.6 ± 1.3 | 0.9 ± 1.3 | 54.2 ± 25.6 | 19 ± 11 |
| rule | 5.2 ± 2.0 | 2.4 ± 1.3 | 1.3 ± 1.5 | 45.6 ± 24.4 | 19 ± 11 |
| hand-set (outdoor) | 5.5 ± 2.1 | 2.1 ± 1.4 | 1.2 ± 1.6 | 48.4 ± 26.3 | 20 ± 11 |
| trained | 5.1 ± 2.2 | 2.0 ± 1.4 | 1.2 ± 1.5 | 44.9 ± 26.4 | 20 ± 11 |

## flood

| Policy | Rescued /8 | Drones lost /4 | Abandoned | Firefighter score | Burned % |
|---|---|---|---|---|---|
| random | 0.8 ± 1.4 | 0.9 ± 1.2 | 2.2 ± 1.5 | -1.9 ± 14.9 | 20 ± 7 |
| blind | 5.5 ± 2.3 | 2.2 ± 1.5 | 1.0 ± 1.2 | 49.9 ± 27.2 | 15 ± 8 |
| rule | 5.2 ± 2.6 | 2.1 ± 1.4 | 1.1 ± 1.1 | 46.6 ± 29.1 | 15 ± 8 |
| hand-set (flood) | 5.4 ± 2.5 | 2.0 ± 1.6 | 1.1 ± 1.1 | 48.1 ± 28.7 | 15 ± 7 |
| trained | 5.2 ± 2.4 | 1.9 ± 1.6 | 1.0 ± 1.1 | 46.7 ± 26.9 | 16 ± 8 |

