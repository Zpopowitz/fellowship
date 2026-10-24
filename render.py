"""Render 3-panel comparison GIFs and the learned-weights chart."""
from __future__ import annotations

import json
import os

import numpy as np

from fellowship import policies
from fellowship.rollout import run_episode

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

UNKNOWN, OPEN, BLOCKED = 0, 1, 2
FEATURE_LABELS = ["new area", "frontier\nprogress", "survivor\nprogress",
                  "crowding", "revisits", "stay"]


def _load(name):
    return np.asarray(json.load(open(os.path.join(RESULTS, f"weights_{name}.json")))["weights"])


def _panel_image(frame, size):
    """Build an RGB image [H,W,3] for one panel frame."""
    H, W = frame["open_grid"].shape
    img = np.full((H, W, 3), 0.15, dtype=float)  # dark = unexplored
    known = frame["known"]
    img[known == OPEN] = (0.90, 0.90, 0.90)     # explored open: light
    img[known == BLOCKED] = (0.30, 0.20, 0.20)  # discovered wall
    # true walls the team hasn't seen stay dark (unexplored)
    # survivors
    for sid, (sy, sx) in enumerate(frame["survivors"]):
        img[sy, sx] = (0.1, 0.8, 0.1) if frame["rescued"][sid] else (0.9, 0.1, 0.1)
    # robots
    for (ry, rx) in frame["positions"]:
        img[ry, rx] = (0.1, 0.4, 1.0)
    return img


def swarm_gif(kind: str, seed: int, path: str, best_label="scratch"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import animation

    best_w = _load(best_label)
    runs = [
        ("random", policies.random_policy),
        ("rule-based", policies.rule_policy),
        (f"trained ({best_label})", policies.linear_policy_factory(best_w)),
    ]
    frame_sets = []
    for _, pol in runs:
        _, frames = run_episode(pol, kind, seed, collect_frames=True)
        frame_sets.append(frames)

    n_frames = min(len(fs) for fs in frame_sets)
    size = frame_sets[0][0]["open_grid"].shape[0]

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.8))
    ims = []
    for ax, (title, _) in zip(axes, runs):
        ax.set_title(title, fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
        im = ax.imshow(_panel_image(frame_sets[0][0], size), interpolation="nearest")
        ims.append(im)
    txts = [ax.text(1, 3, "", color="white", fontsize=8,
                    bbox=dict(facecolor="black", alpha=0.5, pad=1)) for ax in axes]
    fig.suptitle(f"Fellowship — {kind} (seed {seed})", fontsize=11)
    fig.tight_layout()

    def update(f):
        for p in range(3):
            fr = frame_sets[p][min(f, len(frame_sets[p]) - 1)]
            ims[p].set_data(_panel_image(fr, size))
            txts[p].set_text(f"step {fr['step']}  rescued {fr['n_rescued']}/8")
        return ims + txts

    anim = animation.FuncAnimation(fig, update, frames=n_frames, interval=80, blit=False)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    anim.save(path, writer=animation.PillowWriter(fps=12))
    plt.close(fig)
    return path


def weights_png(path: str, best_label="scratch"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    learned = _load(best_label)
    rule = policies.RULE_WEIGHTS
    x = np.arange(len(FEATURE_LABELS))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, rule, 0.4, label="rule-based", color="#B0B0B0")
    ax.bar(x + 0.2, learned, 0.4, label=f"trained ({best_label})", color="#4C78A8")
    ax.set_xticks(x)
    ax.set_xticklabels(FEATURE_LABELS, fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("weight")
    ax.set_title("Fellowship — what the swarm learned")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def main():
    os.makedirs(RESULTS, exist_ok=True)
    best = "scratch"
    meta = os.path.join(RESULTS, "_eval_meta.json")
    if os.path.exists(meta):
        best = json.load(open(meta)).get("best", "scratch")

    weights_png(os.path.join(RESULTS, "weights.png"), best)
    print("weights.png done")

    # main hero GIF: a boston region
    swarm_gif("boston", 5000, os.path.join(RESULTS, "swarm.gif"), best)
    print("swarm.gif (boston) done")
    for kind in ("home", "office", "datacenter", "factory"):
        p = os.path.join(RESULTS, f"swarm_{kind}.gif")
        swarm_gif(kind, 5000, p, best)
        print(f"swarm_{kind}.gif done")


if __name__ == "__main__":
    main()
