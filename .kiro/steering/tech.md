Python 3.11+. numpy, scipy, pettingzoo, gymnasium, matplotlib, pillow, pytest, hypothesis. No GPU, no deep learning framework.
The environment is a PettingZoo ParallelEnv and must pass pettingzoo.test.parallel_api_test.
Same seed -> same episode, everywhere.
Keep world logic in pure functions where possible so it can be property-tested.
BFS distances use numpy (repeated 4-neighbour dilation with a distance cap of 40), not Python loops over cells.
Target: one 160-step episode, 4 robots, 48x48 map, under 1 second on a laptop CPU. Use multiprocessing for batches of episodes.
Every entry point runs from the repo root as `python -m <module>`.
