# Fellowship — Results

All numbers are from **held-out maps** (eval seeds ≥ 5000), never used in training. 20 maps per kind, 100 total, same maps and seeds for every policy.

### Rescued (of 8), mean ± std, 20 held-out maps/kind (100 total)

| policy | boston | home | office | datacenter | factory | overall |
|---|---|---|---|---|---|---|
| random | 0.40 ± 0.58 | 0.20 ± 0.40 | 0.35 ± 0.65 | 0.35 ± 0.73 | 0.40 ± 0.80 | 0.34 ± 0.65 |
| rule | 6.55 ± 1.53 | 5.20 ± 1.54 | 6.15 ± 1.28 | 5.85 ± 2.06 | 7.15 ± 0.91 | 6.18 ± 1.65 |
| scratch | 6.50 ± 1.40 | 5.30 ± 1.55 | 5.85 ± 1.56 | 6.20 ± 1.33 | 7.15 ± 0.91 | 6.20 ± 1.50 |
| warm-start | 6.65 ± 1.49 | 5.40 ± 1.85 | 5.50 ± 1.24 | 5.75 ± 1.30 | 7.15 ± 1.01 | 6.09 ± 1.57 |

### Explored %, overall · Steps used, overall

| policy | explored % (overall) | steps (overall) |
|---|---|---|
| random | 9.07 ± 3.37 | 160.00 ± 0.00 |
| rule | 74.97 ± 12.83 | 152.62 ± 15.42 |
| scratch | 76.83 ± 11.78 | 156.47 ± 9.45 |
| warm-start | 75.28 ± 12.95 | 155.07 ± 11.78 |

### Communication ablation (best policy: scratch)

| COMM | rescued (of 8) | explored % |
|---|---|---|
| 3 | 5.69 ± 1.62 | 71.6 |
| 10 | 5.87 ± 1.71 | 76.6 |
| 100 | 6.33 ± 1.48 | 76.4 |
