"""Table-of-contents graphic for Digital Discovery (8 cm x 4 cm), read from results files.

New artwork, not a panel of any figure in the paper.

  left   a surrogate as two steps, parameters -> coefficients (the map) -> field (the basis),
         each labelled with its share of DeepONet's squared held-out error at 16 modes on the
         MOF-like design (results/dd_v3a1_verdict.json, PREREG_DD_V3 amendment A1)
  right  held-out field error of the best surrogate (DeepONet) and of the coarse solve on both
         designs (results/dd_additions_verdict.json, results/dd_additions_verdict_v3.json)

    python fig_toc.py   -> figures/TOC.png (600 dpi) and figures/TOC.pdf
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import figstyle as fs

CM = 1 / 2.54
P = "16"


def _box(ax, x, y, w, h, text):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc="white", ec=fs.C["grey"], lw=0.7))
    ax.text(x, y, text, ha="center", va="center", fontsize=4.9, linespacing=1.1)


def _arrow(ax, x0, x1, y, colour, lw):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=6, lw=lw, color=colour,
                                 shrinkA=0, shrinkB=0))


def main():
    fs.apply()
    plt.rcParams["savefig.bbox"] = "standard"          # exactly 8 x 4 cm, not cropped
    sh = json.load(open("results/dd_v3a1_verdict.json"))["split_deeponet_own_floor"]["v3"]["by_p"][P]
    map_pct = 100 * sh["share_map"]
    b2 = json.load(open("results/dd_additions_verdict.json"))["b1"]
    b3 = json.load(open("results/dd_additions_verdict_v3.json"))["b1"]

    fig = plt.figure(figsize=(8 * CM, 4 * CM))
    a = fig.add_axes([0.01, 0.0, 0.58, 1.0])
    b = fig.add_axes([0.705, 0.2, 0.275, 0.6])

    a.set_xlim(0, 6); a.set_ylim(0, 3.2); a.axis("off")
    a.text(3.0, 2.9, "Where a surrogate's error comes from", ha="center", va="center", fontsize=6,
           weight="bold")
    y = 1.75
    _box(a, 0.85, y, 1.6, 0.8, "material +\nconditions")
    _box(a, 3.0, y, 1.6, 0.8, "basis\ncoefficients")
    _box(a, 5.15, y, 1.6, 0.8, "breakthrough\nfield")
    _arrow(a, 1.67, 2.18, y, fs.C["red"], 1.8)
    _arrow(a, 3.82, 4.33, y, fs.C["grey"], 0.9)
    a.text(1.9, y + 0.55, "coefficient map", ha="center", fontsize=5.2, color=fs.C["red"])
    a.text(4.1, y + 0.55, "basis", ha="center", fontsize=5.2, color=fs.C["dark"])
    a.text(1.9, y - 0.95, f"{map_pct:.0f} %", ha="center", fontsize=9, weight="bold", color=fs.C["red"])
    a.text(4.1, y - 0.95, f"{100 - map_pct:.0f} %", ha="center", fontsize=9, color=fs.C["dark"])
    a.text(3.0, 0.22, "share of held-out squared error, MOF-like isotherms", ha="center", fontsize=4.8,
           color=fs.C["dark"])

    x = [0, 1]
    w = 0.36
    don = [100 * b2["don"]["field_nrmse_mean"], 100 * b3["don"]["field_nrmse_mean"]]
    co = [100 * b2["coarse"]["field_nrmse_mean"], 100 * b3["coarse"]["field_nrmse_mean"]]
    b.bar([i - w / 2 for i in x], don, w, color=fs.ARM_COLOUR["deeponet"], label="best surrogate")
    b.bar([i + w / 2 for i in x], co, w, color=fs.C["dark"], label="coarse solve")
    b.set_xticks(x); b.set_xticklabels(["smooth", "MOF-like"], fontsize=5.2)
    b.set_ylabel("held-out error (%)", fontsize=5.5, labelpad=1)
    b.set_title("A coarse solve wins", fontsize=5.6, pad=4, weight="bold")
    b.tick_params(labelsize=5, length=2, pad=1)
    b.legend(fontsize=4.6, frameon=False, loc="upper left", handlelength=0.9, borderaxespad=0.1)
    b.set_ylim(0, 1.45 * max(don))
    b.grid(False, axis="x")
    for s in ("top", "right"):
        b.spines[s].set_visible(False)

    os.makedirs("figures", exist_ok=True)
    fig.savefig("figures/TOC.png", dpi=600)
    fig.savefig("figures/TOC.pdf")
    plt.close(fig)
    print(f"wrote figures/TOC.png/.pdf (8 x 4 cm); map share {map_pct:.1f} %")


if __name__ == "__main__":
    main()
