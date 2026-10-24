"""Held-out evaluation of the hazard work.

Every number here comes from maps the policies never trained on (seeds 5000+).
For each situation (indoor / outdoor / flood) we run the same 24 held-out maps
for every policy and report mean +/- std of:
  - survivors rescued (of 8)
  - drones lost (of 4)
  - survivors left in fire/flood (abandoned)
  - firefighter score (env.score_firefighter)
  - fraction of the map burned at episode end

Policies compared: random, blind (hazard features zeroed), rule, the hand-set
situation mode, and the CEM-trained situation weights.

Run:  python -m evaluate_hazards
Writes results/hazards.md (synced into the README HAZARDS section).
"""
from __future__ import annotations

import os

import numpy as np

from fellowship import policies
from fellowship.rollout import run_episode
from train_situations import SITUATION_ENV

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
N_MAPS = 24
EVAL_SEED0 = 5000

# held-out layouts per situation (seeds 5000+, never trained on)
SITUATION_EVAL = {
    "indoor": [("home", "office", "datacenter", "factory")],  # cycle kinds
    "outdoor": [("sar",)],
    "flood": [("sar",)],
}
FLOOD_SEED0 = 5100  # keep flood eval maps disjoint from outdoor eval maps


def _eval_maps(situation):
    """List of (kind, seed) held-out maps for a situation."""
    if situation == "indoor":
        kinds = ["home", "office", "datacenter", "factory"]
        return [(kinds[i % 4], EVAL_SEED0 + i) for i in range(N_MAPS)]
    if situation == "flood":
        return [("sar", FLOOD_SEED0 + i) for i in range(N_MAPS)]
    return [("sar", EVAL_SEED0 + i) for i in range(N_MAPS)]


def _burned_frac(env):
    open0 = int(env.open_grid.sum()) + int(env.fire.sum())
    return float(env.fire.sum()) / max(1, open0)


def _policies_for(situation):
    sit_mode = situation  # 'indoor'/'outdoor'/'flood' are also mode names
    trained_w = policies.load_trained(situation)
    out = {
        "random": policies.get_policy("random"),
        "blind": policies.get_policy("blind"),
        "rule": policies.get_policy("rule"),
        f"hand-set ({sit_mode})": policies.get_policy(sit_mode),
    }
    if trained_w is not None:
        out["trained"] = policies.linear_policy_factory(trained_w)
    return out


def _run_policy(pol, situation, maps):
    """Single pass: run each held-out map once, collect all metrics + burned."""
    from fellowship.env import SwarmEnv
    env_kwargs = SITUATION_ENV[situation]
    rescued, lost, abandoned, ff, burned = [], [], [], [], []
    for kind, seed in maps:
        env = SwarmEnv(kind=kind, seed=seed, **env_kwargs)
        obs, _ = env.reset(seed=seed)
        rng = np.random.default_rng(seed ^ 0x5DEECE66D & 0xFFFFFFFF)
        while env.agents:
            acts = {a: pol(obs[a]["features"], np.asarray(obs[a]["mask"], bool), rng)
                    for a in env.agents}
            obs, _, term, _, _ = env.step(acts)
            if not env.agents:
                break
        m = env.episode_metrics()
        rescued.append(m["rescued"]); lost.append(m.get("disabled", 0))
        abandoned.append(m.get("abandoned", 0)); ff.append(m.get("firefighter_score", 0.0))
        burned.append(_burned_frac(env))

    def ms(a):
        a = np.asarray(a, dtype=float)
        return a.mean(), a.std()
    return {"rescued": ms(rescued), "lost": ms(lost), "abandoned": ms(abandoned),
            "ff": ms(ff), "burned": ms(burned)}


def main():
    os.makedirs(RESULTS, exist_ok=True)
    lines = ["# Fellowship — hazard evaluation (held-out)", "",
             f"{N_MAPS} held-out maps per situation (seeds {EVAL_SEED0}+), the same maps and "
             "seeds for every policy. Mean ± std. Rescued of 8, drones lost of 4. "
             "'Abandoned' = survivors left in fire or flood at the end. 'Burned' = "
             "fraction of open cells on fire at episode end.", ""]
    for situation in ["indoor", "outdoor", "flood"]:
        maps = _eval_maps(situation)
        lines += [f"## {situation}", "",
                  "| Policy | Rescued /8 | Drones lost /4 | Abandoned | Firefighter score | Burned % |",
                  "|---|---|---|---|---|---|"]
        for name, pol in _policies_for(situation).items():
            r = _run_policy(pol, situation, maps)
            bmean, bstd = r["burned"]
            lines.append(
                f"| {name} | {r['rescued'][0]:.1f} ± {r['rescued'][1]:.1f} "
                f"| {r['lost'][0]:.1f} ± {r['lost'][1]:.1f} "
                f"| {r['abandoned'][0]:.1f} ± {r['abandoned'][1]:.1f} "
                f"| {r['ff'][0]:.1f} ± {r['ff'][1]:.1f} "
                f"| {bmean*100:.0f} ± {bstd*100:.0f} |")
            print(f"[{situation}] {name}: rescued {r['rescued'][0]:.1f} "
                  f"lost {r['lost'][0]:.1f} burned {bmean*100:.0f}%", flush=True)
        lines.append("")
    out = os.path.join(RESULTS, "hazards.md")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
