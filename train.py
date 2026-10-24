"""Cross-entropy-method training of the 6 linear policy weights."""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from fellowship import policies
from fellowship.maps import KINDS
from fellowship.rollout import run_episode

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

N_ITERS = 20
N_CANDIDATES = 16
N_ELITE = 4
MAPS_PER_KIND = 2
STD_FLOOR = 0.1
TRAIN_SEED_BASE = 0


def train_maps():
    """Fixed training maps: 2 per kind from the training seed range."""
    out = []
    for ki, kind in enumerate(KINDS):
        for j in range(MAPS_PER_KIND):
            out.append((kind, TRAIN_SEED_BASE + ki * 100 + j))
    return out


def _score_weights(args):
    w, maps_list = args
    pol = policies.linear_policy_factory(np.asarray(w))
    total = 0.0
    for kind, seed in maps_list:
        m, _ = run_episode(pol, kind, seed)
        total += m["score"]
    return total / len(maps_list)


def cem(mean, std, label, log_lines):
    maps_list = train_maps()
    best_curve, mean_curve = [], []
    rng = np.random.default_rng(12345 + hash(label) % 1000)
    best_w = mean.copy()
    best_s = -1e9

    for it in range(N_ITERS):
        cands = rng.normal(mean, std, size=(N_CANDIDATES, len(mean)))
        args = [(c, maps_list) for c in cands]
        with ProcessPoolExecutor() as ex:
            scores = list(ex.map(_score_weights, args))
        scores = np.array(scores)
        elite_idx = np.argsort(scores)[-N_ELITE:]
        elite = cands[elite_idx]
        mean = elite.mean(axis=0)
        std = np.maximum(elite.std(axis=0), STD_FLOOR)

        it_best = float(scores.max())
        it_mean = float(scores.mean())
        best_curve.append(it_best)
        mean_curve.append(it_mean)
        if it_best > best_s:
            best_s = it_best
            best_w = cands[int(np.argmax(scores))].copy()
        line = (f"[{label}] iter {it:2d} best {it_best:.3f} mean {it_mean:.3f} "
                f"w=[{', '.join(f'{v:.2f}' for v in mean)}]")
        print(line, flush=True)
        log_lines.append(line)

    return mean, best_w, best_curve, mean_curve


def learning_curve_png(curves: dict, path: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, (best, mean) in curves.items():
        ax.plot(best, label=f"{label} best", lw=2)
        ax.plot(mean, label=f"{label} mean", ls="--", lw=1)
    ax.set_xlabel("CEM iteration")
    ax.set_ylabel("score (2 maps/kind)")
    ax.set_title("Fellowship — CEM learning curves")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main():
    os.makedirs(RESULTS, exist_ok=True)
    log_lines = []
    curves = {}

    # scratch
    mean_scratch, best_scratch, b1, m1 = cem(np.zeros(6), np.full(6, 1.5), "scratch", log_lines)
    json.dump({"weights": mean_scratch.tolist(),
               "best_sample_weights": best_scratch.tolist(), "saved": "cem_mean"},
              open(os.path.join(RESULTS, "weights_scratch.json"), "w"), indent=2)
    curves["scratch"] = (b1, m1)

    # warm-start from rule weights
    mean_warm, best_warm, b2, m2 = cem(policies.RULE_WEIGHTS.copy(), np.full(6, 0.6), "warm", log_lines)
    json.dump({"weights": mean_warm.tolist(),
               "best_sample_weights": best_warm.tolist(), "saved": "cem_mean"},
              open(os.path.join(RESULTS, "weights_warm.json"), "w"), indent=2)
    curves["warm"] = (b2, m2)

    learning_curve_png(curves, os.path.join(RESULTS, "learning_curve.png"))
    with open(os.path.join(RESULTS, "train_log.txt"), "w") as f:
        f.write("\n".join(log_lines) + "\n")

    print("\nscratch mean weights:", mean_scratch.round(3).tolist())
    print("warm    mean weights:", mean_warm.round(3).tolist())
    print("rule    weights:", policies.RULE_WEIGHTS.tolist())


def smoke(n_iter=1):
    """1-iteration smoke on 1 map/kind (used by the train.py save hook)."""
    import time
    global N_ITERS, MAPS_PER_KIND
    N_ITERS, MAPS_PER_KIND = n_iter, 1
    t = time.time()
    log = []
    _mean, _best, b, m = cem(np.zeros(6), np.full(6, 1.5), "smoke", log)
    print(f"smoke best score {b[-1]:.3f} in {time.time()-t:.2f}s")


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        smoke()
    else:
        main()
