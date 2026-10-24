"""PettingZoo ParallelEnv API conformance."""
from pettingzoo.test import parallel_api_test

from fellowship.env import SwarmEnv


def test_parallel_api():
    env = SwarmEnv(kind="mixed", seed=3)
    parallel_api_test(env, num_cycles=100)
