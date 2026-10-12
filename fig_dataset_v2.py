"""Figure 2: dataset v2. What was sampled, what was held out, and what makes it testable.

Every series is read from `data/parametric_v2/manifest.json` and
`results/isotherm_space.json`. No model is evaluated and no field is loaded. Drawn at
the printed width (7.2 in).

This figure replaces the legacy coverage figure, which carried defect B27: it
iterated over SAMPLES while plotting MATERIAL descriptors, so every training material
was drawn in blue and then overplotted in orange, and the shipped figure showed not
one training point. The rule this figure obeys: a panel about materials plots one
point per material. The counts in the legend are computed here, not typed.

  A  the material space: the two parameters that set the isotherm's shape, one point
     per material, split by whether the material is held out.
  B  Damkoehler per material, the axis rung L6's primary estimand is regressed on.
  C  the accessible Henry region per material, which varies over orders of magnitude
     even though Henry's law holds for every material (defect B57).

    python fig_dataset_v2.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import figstyle as fs

OUT = "figures"
ROOT_V2 = "data/parametric_v2"
C_TRAIN = fs.C["blue"]
C_HELD = fs.C["orange"]

# Results files a run still in flight has not written (see validate.py's figure gate).
PENDING_RESULTS = ()


def main():
    fs.apply()
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    iso = json.load(open("results/isotherm_space.json"))
    mats = man["materials"]
    held = set(man["novel_materials"])

    # ONE POINT PER MATERIAL: this is the line B27 got wrong.
    mid = np.array([m["material_id"] for m in mats])
    is_held = np.array([int(m) in held or m in held for m in mid])
    n_held, n_train = int(is_held.sum()), int((~is_held).sum())
    assert n_held + n_train == len(mats), "material split does not partition the materials"
    assert n_held == len(held), f"manifest lists {len(held)} held-out materials, plotted {n_held}"

    step = np.array([m["step_rh"] for m in mats])
    shape = np.array([m["isotherm_n"] for m in mats])

    # Damkoehler per material: the median over that material's own samples, exactly as
    # run_l6_v2.damkohler_per_material computes it for the slope test.
    by = {}
    for s in man["samples"]:
        if "Da" in s:
            by.setdefault(s["mat"], []).append(s["Da"])
    da = np.array([np.median(by[int(m)]) for m in mid])

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.2, 2.6))
    fig.subplots_adjust(wspace=0.45, top=0.80)

    # ---- A: the material space
    for mask, col in ((~is_held, C_TRAIN), (is_held, C_HELD)):
        a.scatter(100 * step[mask], shape[mask], s=6, alpha=0.8, color=col, edgecolors="none")
    a.set_xticks([10, 20, 30, 40])
    a.set_xlabel("step position (% RH)")
    a.set_ylabel("cooperativity exponent $n$")
    a.set_title("A  Material space")

    # ---- B: Damkoehler per material
    bins = np.logspace(np.log10(da.min()), np.log10(da.max()), 22)
    b.hist(da[~is_held], bins=bins, color=C_TRAIN, alpha=0.9)
    b.hist(da[is_held], bins=bins, color=C_HELD, histtype="step", lw=1.6)   # outline: training stays visible
    b.set_xscale("log")
    b.set_xlabel("Damköhler number")
    b.set_ylabel("materials")
    b.set_title("B  Damköhler range")
    b.axvspan(5, 60, color=fs.C["green"], alpha=0.10, zorder=0)
    b.set_ylim(0, b.get_ylim()[1] * 1.35)
    frac = float(((da >= 5) & (da <= 60)).mean())
    b.text(0.97, 0.97, f"shaded: informative band\n{100 * frac:.0f} % of materials in it\n"
                       f"{np.log10(da.max() / da.min()):.2f} decades in all",
           transform=b.transAxes, fontsize=7.2, color="0.25", va="top", ha="right")

    # ---- C: the accessible Henry region per material
    lg = np.array([r["log10_c_henry_over_c_in_median"] for r in iso["rows"]])
    lg_plot = np.clip(lg, -20, None)          # the tail runs to -509; clip for display
    n_clipped = int((lg < -20).sum())
    c.hist(lg_plot, bins=30, color="#4a5c6a")
    c.set_ylim(0, c.get_ylim()[1] * 1.55)
    c.axvline(-3, color=fs.C["red"], lw=1.0, ls="--")
    c.set_xlabel(r"$\log_{10}$(Henry-region top / feed)")
    c.set_ylabel("materials")
    c.set_title("C  Henry region per material")
    c.text(0.03, 0.97, f"all {iso['n_materials']} have $n>1$:\n$K_H$ finite, positive\n"
                       f"({iso['K_H']['decades']:.1f} decades)\n\n"
                       f"{iso['n_henry_region_below_1e3_of_feed']} left of the line\n"
                       f"(below $10^{{-3}}$ of feed)"
                       + (f"\n{n_clipped} clipped at $10^{{-20}}$" if n_clipped else ""),
           transform=c.transAxes, fontsize=7.2, color="0.25", va="top")

    handles = [Line2D([], [], marker="o", ls="", color=C_TRAIN, ms=4),
               Line2D([], [], marker="o", ls="", color=C_HELD, ms=4)]
    fig.legend(handles, [f"training ({n_train} materials)", f"held out ({n_held} materials)"],
               loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.0), fontsize=7.4)

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig2_dataset.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig2_dataset.png/.pdf  "
          f"({len(mats)} materials: {n_train} training, {n_held} held out; "
          f"Da {da.min():.1f}-{da.max():.0f}; {n_clipped} Henry outliers clipped)")


if __name__ == "__main__":
    main()
