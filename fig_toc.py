"""Table-of-contents graphic for Digital Discovery (8 cm x 4 cm), read from results files.

New artwork, not a panel of any figure in the paper. Printed at exactly 8 x 4 cm, so no text
is smaller than 6.5 pt.

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
T = 6.6            # smallest text, in points, at the printed size


def _box(ax, x, y, w, h, text):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc="white", ec=fs.C["grey"], lw=0.7))
    ax.text(x, y, text, ha="center", va="center", fontsize=T, linespacing=1.05)


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
    a = fig.add_axes([0.0, 0.0, 0.6, 1.0])
    b = fig.add_axes([0.70, 0.25, 0.28, 0.58])

    a.set_xlim(0, 6); a.set_ylim(0, 3.2); a.axis("off")
    a.text(3.0, 2.92, "Where the error comes from", ha="center", va="center", fontsize=T + 0.6,
           weight="bold")
    y = 1.85
    _box(a, 0.9, y, 1.7, 0.78, "material")
    _box(a, 3.0, y, 1.85, 0.78, "coefficients")
    _box(a, 5.1, y, 1.7, 0.78, "field")
    _arrow(a, 1.76, 2.06, y, fs.C["red"], 1.8)
    _arrow(a, 3.94, 4.24, y, fs.C["grey"], 0.9)
    a.text(1.92, y + 0.52, "map", ha="center", fontsize=T, color=fs.C["red"], weight="bold")
    a.text(4.08, y + 0.52, "basis", ha="center", fontsize=T, color=fs.C["dark"])
    a.text(1.92, y - 1.05, f"{map_pct:.0f} %", ha="center", fontsize=10, weight="bold", color=fs.C["red"])
    a.text(4.08, y - 1.05, f"{100 - map_pct:.0f} %", ha="center", fontsize=10, color=fs.C["dark"])
    a.text(3.0, 0.22, "of the held-out error", ha="center", fontsize=T, color=fs.C["dark"])

    don = [100 * b2["don"]["field_nrmse_mean"], 100 * b3["don"]["field_nrmse_mean"]]
    co = [100 * b2["coarse"]["field_nrmse_mean"], 100 * b3["coarse"]["field_nrmse_mean"]]
    w = 0.38
    b.bar([-w / 2, 1 - w / 2], don, w, color=fs.ARM_COLOUR["deeponet"])
    b.bar([w / 2, 1 + w / 2], co, w, color=fs.C["dark"])
    b.text(1 - w / 2, don[1] * 1.03, "surrogate", ha="center", va="bottom", fontsize=T,
           color=fs.ARM_COLOUR["deeponet"])
    b.text(w / 2, co[0] + 0.3, "coarse\nsolve", ha="center", va="bottom", fontsize=T,
           color=fs.C["dark"], linespacing=1.0)
    b.set_xticks([0, 1]); b.set_xticklabels(["smooth", "MOF-like"], fontsize=T)
    b.set_ylabel("error (%)", fontsize=T, labelpad=1)
    b.set_title("Coarse solve wins", fontsize=T + 0.6, pad=4, weight="bold", loc="right")
    b.tick_params(labelsize=T, length=2, pad=1)
    b.set_ylim(0, 1.25 * max(don))
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
