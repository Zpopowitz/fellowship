"""Fellowship Gym demo: one 3-panel hazard episode, no training needed.

    python -m demo

Runs random / rule / trained swarms on the SAME office floorplan with fire on,
and writes results/demo.gif (three panels side by side). Finishes in well under
a minute on a laptop CPU. Prints where the file went.
"""
from __future__ import annotations

import os

import numpy as np

import fellowship
from fellowship import policies

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "results", "demo.gif")

TASK, MAPS, SEED = "rescue_fire", "buildings", 1  # buildings seed 1 -> office

PANELS = [
    ("random", policies.get_policy("random")),
    ("rule", policies.get_policy("rule")),
    ("trained", policies.get_policy("trained", kind="office")),
]


def _run_frames(pol):
    env = fellowship.make_env(task=TASK, maps=MAPS, seed=SEED)
    obs, _ = env.reset(seed=SEED)
    rng = np.random.default_rng(SEED)
    frames = [_snapshot(env)]
    while env.agents:
        acts = {a: pol(obs[a]["features"], np.asarray(obs[a]["mask"], bool), rng)
                for a in env.agents}
        obs, _, term, _, _ = env.step(acts)
        frames.append(_snapshot(env))
        if not env.agents:
            break
    return frames, env.episode_metrics()


def _snapshot(env):
    return {
        "open": env.open_grid.copy(),
        "fire": env.fire.copy() if env.hazards else np.zeros_like(env.open_grid),
        "flood": env.flood.copy() if env.hazards else np.zeros_like(env.open_grid),
        "pos": list(env.positions),
        "disabled": env.disabled.copy() if env.hazards else np.zeros(env.n_robots, bool),
        "surv": list(env.survivor_cells),
        "rescued": env.rescued.copy(),
    }


def _render(frames_by_panel, labels, metrics):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import animation

    n = max(len(f) for f in frames_by_panel)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))

    def draw(ax, fr, label, m):
        ax.clear(); ax.set_xticks([]); ax.set_yticks([])
        g = fr["open"]
        ax.imshow(np.where(g, 0.9, 0.15), cmap="gray", vmin=0, vmax=1)
        for (fy, fx) in np.argwhere(fr["fire"]):
            ax.add_patch(plt.Rectangle((fx - .5, fy - .5), 1, 1, color="#f85149"))
        for (fy, fx) in np.argwhere(fr["flood"]):
            ax.add_patch(plt.Rectangle((fx - .5, fy - .5), 1, 1, color="#388bfd", alpha=.6))
        for sid, (sy, sx) in enumerate(fr["surv"]):
            ax.plot(sx, sy, "o", ms=7, color="#3fb950" if fr["rescued"][sid] else "#e3b341")
        for i, (py, px) in enumerate(fr["pos"]):
            if fr["disabled"][i]:
                ax.plot(px, py, "x", ms=8, color="#8b949e")
            else:
                ax.plot(px, py, "s", ms=6, color="white", mec="#1f6feb", mew=1.5)
        ax.set_title(f"{label}\nrescued {int(fr['rescued'].sum())}/8", fontsize=11)

    def animate(i):
        for ax, frames, label, m in zip(axes, frames_by_panel, labels, metrics):
            draw(ax, frames[min(i, len(frames) - 1)], label, m)
        return []

    fig.suptitle("Fellowship Gym — rescue under fire (office)", fontsize=13)
    anim = animation.FuncAnimation(fig, animate, frames=n, interval=120)
    anim.save(OUT, writer=animation.PillowWriter(fps=8), dpi=80)
    plt.close(fig)


def main():
    frames_by_panel, labels, metrics = [], [], []
    for label, pol in PANELS:
        fr, m = _run_frames(pol)
        frames_by_panel.append(fr); labels.append(label); metrics.append(m)
        print(f"  {label}: rescued {m['rescued']}/8, drones lost {m.get('disabled', 0)}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    _render(frames_by_panel, labels, metrics)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
