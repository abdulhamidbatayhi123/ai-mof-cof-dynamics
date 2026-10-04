"""Figure: real water-harvesting MOFs against the sampled design space (referee M10).

Reads results/water_mofs.json (owner: water_mofs.py, from the sourced literature
values in research/water_mof_parameters.json). Each MOF is drawn as the SPAN of its
reported values across sources (a bar from min to max on each axis, a point if one
source); the shaded boxes are the design's sampled ranges.

    python fig_water_mofs.py
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

SRC = "results/water_mofs.json"
MARK = ["o", "s", "D", "^", "v", "P"]


def mid(v):
    return 0.5 * (v["lo"] + v["hi"])


def draw(ax, d, xk, yk, xlab, ylab, title):
    (x0, x1), (y0, y1) = sorted(d["design"][xk]), sorted(d["design"][yk])
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, color="0.88", zorder=0))
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="0.45", lw=1.0, ls="--", zorder=1))
    for (name, m), mk in zip(d["materials"].items(), MARK):
        x, y = m.get(xk), m.get(yk)
        if x is None or y is None:
            continue
        ax.errorbar(mid(x), mid(y), xerr=[[mid(x) - x["lo"]], [x["hi"] - mid(x)]],
                    yerr=[[mid(y) - y["lo"]], [y["hi"] - mid(y)]], fmt=mk, ms=6, capsize=3,
                    lw=1.1, label=name.split(" (")[0].replace("Co2Cl2", "Co$_2$Cl$_2$"), zorder=3)
    ax.set_xlabel(xlab, fontsize=9); ax.set_ylabel(ylab, fontsize=9)
    ax.tick_params(labelsize=8); ax.set_title(title, fontsize=9.5, loc="left")


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))
    draw(axes[0], d, "RH_step", "q_max", "step position (relative humidity)",
         "capacity  q$_{max}$ (mol kg$^{-1}$)", "A   where the step sits, and how much it holds")
    draw(axes[1], d, "henry_fraction", "dH", "Henry-site fraction (uptake below the step / at saturation)",
         "heat of adsorption (kJ mol$^{-1}$)", "B   the low-humidity branch and its heat")
    axes[0].legend(fontsize=7.5, loc="upper right", framealpha=0.95)
    fig.tight_layout()
    fig.savefig("figures/FigS2_water_mofs.pdf", bbox_inches="tight")
    fig.savefig("figures/FigS2_water_mofs.png", dpi=200, bbox_inches="tight")
    print("wrote figures/FigS2_water_mofs.pdf / .png")


if __name__ == "__main__":
    main()
