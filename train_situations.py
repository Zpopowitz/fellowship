"""Train one 9-weight decision model PER SITUATION, optimised for the
firefighter objective (save savable lives; risk a drone for a life, not for
nothing).

Situations and their layouts:
    indoor   -> home, office, datacenter, factory floorplans (rooms + corridors)
    outdoor  -> real Boston street-grid regions (kind='sar')
    flood    -> same street regions, flood-heavy

Each model is a linear policy over 9 features
    [new area, frontier, survivor, crowding, revisits, stay,
     fire danger, flood danger, survivor urgency]
trained by the cross-entropy method with hazards ON and thermal-IR + gas
sensing, scored by env.score_firefighter().

Run:  python -m train_situations            (full)
      python -m train_situations --smoke     (1 iteration, quick check)

Memory-careful: a small worker pool, situations one at a time, weights saved to
results/weights_<situation>.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from fellowship import policies
from fellowship.rollout import run_episode

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

SITUATION_LAYOUTS = {
    "indoor": [("home", [0, 1]), ("office", [0, 1]),
               ("datacenter", [0, 1]), ("factory", [0, 1])],
    "outdoor": [("sar", [0, 1, 2, 3, 4, 5])],
    "flood": [("sar", [10, 11, 12, 13, 14, 15])],
}

SITUATION_ENV = {
    "indoor": dict(hazards=True, sensing="ir_gas", n_fire_seeds=2, flood_frac=0.0,
                   fire_spread_p=0.08),
    "outdoor": dict(hazards=True, sensing="ir_gas", n_fire_seeds=3, flood_frac=0.03,
                    fire_spread_p=0.08),
    "flood": dict(hazards=True, sensing="ir_gas", n_fire_seeds=1, flood_frac=0.12,
                  fire_spread_p=0.06),
}

WARM_START = {"indoor": "indoor", "outdoor": "outdoor", "flood": "flood"}

N_ITERS = 8
N_CANDIDATES = 14
N_ELITE = 4
STD_FLOOR = 0.15
MAX_WORKERS = 4


def _score_weights(args):
    w, situation = args
    pol = policies.linear_policy_factory(np.asarray(w))
    env_kwargs = SITUATION_ENV[situation]
    total, n = 0.0, 0
    for kind, seeds in SITUATION_LAYOUTS[situation]:
        for seed in seeds:
            m, _ = run_episode(pol, kind, seed, **env_kwargs)
            total += m.get("firefighter_score", m["score"])
            n += 1
    return total / max(1, n)


def cem(situation, mean, std, n_iters, log_lines):
    best_curve, mean_curve = [], []
    rng = np.random.default_rng(777 + hash(situation) % 1000)
    best_w, best_s = mean.copy(), -1e9
    for it in range(n_iters):
        cands = rng.normal(mean, std, size=(N_CANDIDATES, len(mean)))
        args = [(c, situation) for c in cands]
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
            scores = np.array(list(ex.map(_score_weights, args)))
        elite = cands[np.argsort(scores)[-N_ELITE:]]
        mean = elite.mean(axis=0)
        std = np.maximum(elite.std(axis=0), STD_FLOOR)
        it_best, it_mean = float(scores.max()), float(scores.mean())
        best_curve.append(it_best); mean_curve.append(it_mean)
        if it_best > best_s:
            best_s, best_w = it_best, cands[int(np.argmax(scores))].copy()
        line = f"[{situation}] iter {it:2d} best {it_best:.2f} mean {it_mean:.2f}"
        print(line, flush=True); log_lines.append(line)
    return best_w, best_curve, mean_curve


def learning_curve_png(curves, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, (best, mean) in curves.items():
        ax.plot(best, lw=2, label=f"{label} best")
        ax.plot(mean, ls="--", lw=1, label=f"{label} mean")
    ax.set_xlabel("CEM iteration"); ax.set_ylabel("firefighter score")
    ax.set_title("Fellowship -- per-situation training (firefighter objective)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3); fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=120); plt.close(fig)


def main(n_iters=N_ITERS, situations=None):
    os.makedirs(RESULTS, exist_ok=True)
    situations = situations or list(SITUATION_LAYOUTS)
    log_lines, curves, out = [], {}, {}
    for situation in situations:
        warm = policies.MODES[WARM_START[situation]].copy()
        std = np.full(len(warm), 0.8)
        t = time.time()
        w, b, m = cem(situation, warm, std, n_iters, log_lines)
        dt = time.time() - t
        json.dump({"situation": situation, "weights": w.tolist(),
                   "objective": "firefighter", "trained_s": round(dt, 1)},
                  open(os.path.join(RESULTS, f"weights_{situation}.json"), "w"), indent=2)
        curves[situation] = (b, m); out[situation] = w
        print(f"[{situation}] done in {dt:.1f}s  weights={w.round(2).tolist()}", flush=True)
    learning_curve_png(curves, os.path.join(RESULTS, "situation_curves.png"))
    with open(os.path.join(RESULTS, "train_situations_log.txt"), "w") as f:
        f.write("\n".join(log_lines) + "\n")
    return out


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        main(n_iters=1, situations=["indoor"])
    else:
        main()
