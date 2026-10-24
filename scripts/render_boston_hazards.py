"""Render the georeferenced Boston street grid with real fire/flood density,
for the README. Writes results/boston_hazard_density.png.

    python scripts/render_boston_hazards.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from fellowship import sar_dataset  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    grid = sar_dataset.load_street_grid()
    haz = sar_dataset.load_hazard_field()
    fig, ax = plt.subplots(figsize=(7, 7))
    # streets in grey
    ax.imshow(np.where(grid, 0.78, 0.12), cmap="gray", vmin=0, vmax=1)
    # fire density in warm, flood in cool, only where present
    fire = np.ma.masked_where(haz.fire <= 0, haz.fire)
    flood = np.ma.masked_where(haz.flood <= 0, haz.flood)
    ax.imshow(fire, cmap="autumn_r", alpha=0.9)
    ax.imshow(flood, cmap="winter_r", alpha=0.9)
    ax.set_title("Boston street grid with real fire (warm) and flood (cool) density")
    ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout()
    out = os.path.join(ROOT, "results", "boston_hazard_density.png")
    fig.savefig(out, dpi=110); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
