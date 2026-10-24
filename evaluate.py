"""Held-out evaluation of all policies, plus a radio-range ablation."""
from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from fellowship import policies
from fellowship.maps import KINDS, EVAL_SEED_MIN
from fellowship.rollout import run_episode

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
MAPS_PER_KIND = 20  # 100 total


def eval_seeds():
    """20 held-out maps per kind; seeds >= 5000, disjoint from training."""
    jobs = []
    for ki, kind in enumerate(KINDS):
        for j in range(MAPS_PER_KIND):
            jobs.append((kind, EVAL_SEED_MIN + ki * 1000 + j))
    return jobs


def _load(name):
    p = os.path.join(RESULTS, f"weights_{name}.json")
    return np.asarray(json.load(open(p))["weights"])


def _run_one(args):
    policy_name, weights, kind, seed, comm = args
    pol = policies.get_policy(policy_name, weights)
    m, _ = run_episode(pol, kind, seed, comm=comm)
    return (policy_name, kind, m["rescued"], m["explored"], m["steps"])


def evaluate_policies():
    scratch_w = _load("scratch")
    warm_w = _load("warm")
    specs = {
        "random": ("random", None),
        "rule": ("rule", None),
        "scratch": ("linear", scratch_w),
        "warm-start": ("linear", warm_w),
    }
    jobs = eval_seeds()
    tasks = []
    for label, (pname, w) in specs.items():
        for kind, seed in jobs:
            tasks.append((label, pname, w, kind, seed))

    args = [(pname, w, kind, seed, None) for (label, pname, w, kind, seed) in tasks]
    labels = [t[0] for t in tasks]
    with ProcessPoolExecutor() as ex:
        results = list(ex.map(_run_one, args))
    # attach the display label (policy_name returned is the raw name)
    rows = []
    for (label, pname, w, kind, seed), res in zip(tasks, results):
        _, rkind, rescued, explored, steps = res
        rows.append((label, kind, rescued, explored, steps))
    return rows


def summarize(rows):
    """Return nested dict: label -> kind/overall -> (mean,std) per metric."""
    import collections
    buckets = collections.defaultdict(lambda: collections.defaultdict(list))
    for label, kind, rescued, explored, steps in rows:
        buckets[label][kind].append((rescued, explored, steps))
        buckets[label]["overall"].append((rescued, explored, steps))

    out = {}
    for label, kinds in buckets.items():
        out[label] = {}
        for kind, vals in kinds.items():
            arr = np.array(vals, dtype=float)
            out[label][kind] = {
                "rescued": (arr[:, 0].mean(), arr[:, 0].std()),
                "explored": (arr[:, 1].mean() * 100, arr[:, 1].std() * 100),
                "steps": (arr[:, 2].mean(), arr[:, 2].std()),
                "n": len(vals),
            }
    return out


def _fmt(ms):
    m, s = ms
    return f"{m:.2f} ± {s:.2f}"


def results_table_md(summary) -> str:
    labels = ["random", "rule", "scratch", "warm-start"]
    kinds = list(KINDS) + ["overall"]
    lines = []
    lines.append("### Rescued (of 8), mean ± std, 20 held-out maps/kind (100 total)\n")
    lines.append("| policy | " + " | ".join(kinds) + " |")
    lines.append("|" + "---|" * (len(kinds) + 1))
    for label in labels:
        cells = [_fmt(summary[label][k]["rescued"]) for k in kinds]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    lines.append("\n### Explored %, overall · Steps used, overall\n")
    lines.append("| policy | explored % (overall) | steps (overall) |")
    lines.append("|---|---|---|")
    for label in labels:
        e = _fmt(summary[label]["overall"]["explored"])
        s = _fmt(summary[label]["overall"]["steps"])
        lines.append(f"| {label} | {e} | {s} |")
    return "\n".join(lines)


def comms_ablation(best_label="warm-start"):
    w = _load("scratch" if best_label == "scratch" else "warm")
    jobs = eval_seeds()
    out = {}
    for comm in (3, 10, 100):
        args = [("linear", w, kind, seed, comm) for kind, seed in jobs]
        with ProcessPoolExecutor() as ex:
            res = list(ex.map(_run_one, args))
        rescued = np.array([r[2] for r in res], dtype=float)
        explored = np.array([r[3] for r in res], dtype=float)
        out[comm] = (rescued.mean(), rescued.std(), explored.mean() * 100)
    return out


def comms_png(ablation, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    comms = list(ablation.keys())
    means = [ablation[c][0] for c in comms]
    stds = [ablation[c][1] for c in comms]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([str(c) for c in comms], means, yerr=stds, capsize=5, color="#4C78A8")
    ax.set_xlabel("radio range COMM (Chebyshev cells)")
    ax.set_ylabel("survivors rescued (of 8)")
    ax.set_title("Fellowship — communication range ablation")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def pick_best(summary):
    cand = {k: summary[k]["overall"]["rescued"][0] for k in ("scratch", "warm-start")}
    return max(cand, key=cand.get)


def main():
    os.makedirs(RESULTS, exist_ok=True)
    rows = evaluate_policies()
    summary = summarize(rows)
    table = results_table_md(summary)

    best = pick_best(summary)
    ablation = comms_ablation(best)
    comms_png(ablation, os.path.join(RESULTS, "comms.png"))

    abl_lines = ["\n### Communication ablation (best policy: %s)\n" % best,
                 "| COMM | rescued (of 8) | explored % |",
                 "|---|---|---|"]
    for c, (m, s, e) in ablation.items():
        abl_lines.append(f"| {c} | {m:.2f} ± {s:.2f} | {e:.1f} |")
    abl = "\n".join(abl_lines)

    md = ("# Fellowship — Results\n\n"
          "All numbers are from **held-out maps** (eval seeds ≥ 5000), never used in "
          "training. 20 maps per kind, 100 total, same maps and seeds for every policy.\n\n"
          + table + "\n" + abl + "\n")
    with open(os.path.join(RESULTS, "results.md"), "w", encoding="utf-8") as f:
        f.write(md)

    # write a machine-readable copy for the README hook
    json.dump({"best": best}, open(os.path.join(RESULTS, "_eval_meta.json"), "w"))
    print(md)
    print("best trained policy:", best)


if __name__ == "__main__":
    main()
