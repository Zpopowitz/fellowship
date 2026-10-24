fellowship/maps.py        Boston grid loader and region cropping
fellowship/floorplans.py  procedural damaged-building generator (home, office, datacenter, factory)
fellowship/env.py         PettingZoo ParallelEnv
fellowship/comms.py       radio-range map sharing
fellowship/features.py    per-action features for the policy
fellowship/policies.py    random, rule-based, linear policies
train.py                  cross-entropy-method training
evaluate.py               held-out evaluation, results tables
render.py                 animated GIF comparisons
tests/                    unit + property-based tests
data/boston_map.csv       y,x,open (1 open, 0 blocked), 256x256
data/floorplans/<kind>/NNN.png   48x48, white = open floor, black = wall/rubble (optional pre-made pack)
results/                  weights, tables, charts, GIFs
docs/kiro_log.md          notes on bugs found by tests and how Kiro was used
