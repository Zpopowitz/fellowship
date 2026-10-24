Fellowship is a multi-agent search-and-rescue training environment built from real places: the Boston street grid and procedurally generated damaged buildings (homes, offices, data centers, factory floors). It ships with baselines and a trained swarm policy.
Robots are decentralized: no global map, no central planner. Each robot knows only what it has sensed itself plus what reached it from teammates within radio range (relayed through chains of robots).
The world changes during an episode: aftershocks block random cells.
Every reported result must come from held-out maps the policy never trained on, with the number of episodes and the spread (std) stated.
Be honest about limits: grid world, not real physics; survivors placed at random; floorplans are procedural, not scanned buildings.
Data credit: Moving AI Boston_0_256 grid (Sturtevant, "Benchmarks for Grid-Based Pathfinding", IEEE TCIAIG 2012).
