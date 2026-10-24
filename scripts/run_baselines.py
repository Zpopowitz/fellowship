"""Run the baseline policies on every task x map family and write LEADERBOARD.md.

Policies: random, rule, and the trained situation weights (the trained model for
the map family's situation; falls back to the hand-set situation mode if no
trained file exists). Held-out seeds only (5000+). One table per task.

Runtime is kept under ~10 minutes by using n_maps=12 (said so in the file).
Run:  python scripts/run_baselines.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fellowship import policies  # noqa: E402
from fellowship.benchmark import evaluate_policy  # noqa: E402
from fellowship.tasks import list_map_families, list_tasks  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_MAPS = 12  # keeps the whole sweep under ~10 min on a laptop CPU

# map family -> situation whose trained weights to use
FAMILY_SITUATION = {"streets_real": "outdoor", "streets_grid": "outdoor",
                    "buildings": "indoor"}


def _trained_for(maps: str):
    sit = FAMILY_SITUATION.get(maps, "balanced")
    w = policies.load_trained(sit)
    if w is not None:
        return policies.linear_policy_factory(w)
    return policies.get_policy(sit)  # hand-set fallback


def main():
    lines = ["# Fellowship Gym — baseline leaderboard", "",
             f"{N_MAPS} held-out maps per (task, map family), seeds 5000+, the same maps for "
             "every policy. Mean ± std. Rescued of 8, drones lost of 4. 'trained' = the CEM "
             "situation model for that family (outdoor for streets, indoor for buildings). "
             "n_maps is 12 to keep the full sweep under ~10 minutes.", ""]
    pol_defs = [("random", policies.get_policy("random")),
                ("rule", policies.get_policy("rule"))]
    for task in list_tasks():
        lines += [f"## {task}", "",
                  "| Policy | Map family | Rescued /8 | Explored | Drones lost /4 | In-hazard |",
                  "|---|---|---|---|---|---|"]
        for maps in list_map_families():
            defs = pol_defs + [("trained", _trained_for(maps))]
            for name, pol in defs:
                r = evaluate_policy(pol, task=task, maps=maps, n_maps=N_MAPS)
                lines.append(
                    f"| {name} | {maps} | {r['rescued'][0]:.1f} ± {r['rescued'][1]:.1f} "
                    f"| {r['explored'][0]*100:.0f}% ± {r['explored'][1]*100:.0f} "
                    f"| {r['drones_lost'][0]:.1f} ± {r['drones_lost'][1]:.1f} "
                    f"| {r['survivors_in_hazard'][0]:.1f} ± {r['survivors_in_hazard'][1]:.1f} |")
                print(f"[{task}/{maps}] {name}: rescued {r['rescued'][0]:.1f}", flush=True)
        lines.append("")
    out = os.path.join(ROOT, "LEADERBOARD.md")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
