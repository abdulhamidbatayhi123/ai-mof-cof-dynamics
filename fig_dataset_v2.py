"""Figure: dataset v2 — what was sampled, what was held out, and what makes it testable.

Every series is read from `data/parametric_v2/manifest.json` and
`results/isotherm_space.json`. No model is evaluated and no field is loaded.

This figure replaces the legacy coverage figure, which carried defect **B27**: it
iterated over SAMPLES while plotting MATERIAL descriptors. Each material appears in
about seventeen samples, and the `novel_condition` split holds out *conditions* for
*training* materials, so every training material was drawn in blue and then
overplotted in orange. The shipped figure had a three-entry legend and not one blue
point in any panel — it told the reader the training set was tiny and the
novel-condition set huge, the reverse of the truth. **The rule this figure obeys: a
panel about materials plots one point per material.** The counts in each legend are
computed here, not typed, so the legend cannot disagree with the data again.

  A  the material space: the two parameters that set the isotherm's shape, one point
     per material, split by whether the material is held out.
  B  Damkohler per material, the axis rung L6's primary estimand is regressed on.
     The legacy design is shown for contrast: it could not test that estimand at all.
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

plt.rcParams.update({
    "figure.dpi": 160, "savefig.dpi": 600, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})
OUT = "figures"
ROOT_V2 = "data/parametric_v2"
C_TRAIN = "#3b6ea5"
C_HELD = "#e08b3a"
C_LEGACY = "0.72"

# Results files a run still in flight has not written (see validate.py's figure gate).
PENDING_RESULTS = ()


def main():
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    iso = json.load(open("results/isotherm_space.json"))
    mats = man["materials"]
    held = set(man["novel_materials"])

    # ONE POINT PER MATERIAL — this is the line B27 got wrong.
    mid = np.array([m["material_id"] for m in mats])
    is_held = np.array([int(m) in held or m in held for m in mid])
    n_held, n_train = int(is_held.sum()), int((~is_held).sum())
    assert n_held + n_train == len(mats), "material split does not partition the materials"
    assert n_held == len(held), f"manifest lists {len(held)} held-out materials, plotted {n_held}"

    step = np.array([m["step_rh"] for m in mats])
    shape = np.array([m["isotherm_n"] for m in mats])

    # Damkohler per material: the median over that material's own samples, exactly as
    # run_l6_v2.damkohler_per_material computes it for the slope test.
    by = {}
    for s in man["samples"]:
        if "Da" in s:
            by.setdefault(s["mat"], []).append(s["Da"])
    da = np.array([np.median(by[int(m)]) for m in mid])

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(12.2, 3.5))
    fig.subplots_adjust(wspace=0.34)

    # ---- A: the material space
    for mask, col, name, n in ((~is_held, C_TRAIN, "training", n_train),
                               (is_held, C_HELD, "held out", n_held)):
        a.scatter(100 * step[mask], shape[mask], s=16, alpha=0.75, color=col,
                  edgecolors="none", label=f"{name} ({n} materials)")
    a.set_xlabel("cooperative step position, % RH")
    a.set_ylabel("isotherm shape exponent $n$")
    a.set_title("A. the material space, one point per material", fontsize=9.5, loc="left")
    a.legend(fontsize=7.5, loc="upper right")
    a.text(0.02, 0.03, f"{len(mats)} materials x {len(man['conditions'])} conditions,\n"
                       f"Sobol; {man['n_rejected']} rejected before solving",
           transform=a.transAxes, fontsize=7, color="0.35", va="bottom")

    # ---- B: Damkohler, with the legacy design for contrast
    bins = np.logspace(np.log10(da.min()), np.log10(da.max()), 26)
    b.hist(da[~is_held], bins=bins, color=C_TRAIN, alpha=0.85, label="training")
    b.hist(da[is_held], bins=bins, color=C_HELD, alpha=0.85, label="held out")
    b.set_xscale("log")
    b.set_xlabel("Damkohler number (median per material)")
    b.set_ylabel("materials")
    b.set_title(f"B. Da spans {np.log10(da.max() / da.min()):.2f} decades — "
                f"why L6 is testable", fontsize=9.5, loc="left")
    b.legend(fontsize=7.5, loc="upper right")
    b.axvspan(5, 60, color="#6a994e", alpha=0.10, zorder=0)
    b.text(np.sqrt(5 * 60), b.get_ylim()[1] * 0.92, "informative band", ha="center",
           fontsize=7, color="#3f5e2f")
    frac = float(((da >= 5) & (da <= 60)).mean())
    b.text(0.02, 0.80, f"{100 * frac:.0f} % of materials in band\n"
                       f"median {np.median(da):.1f}",
           transform=b.transAxes, fontsize=7, color="0.35", va="top")

    # ---- C: the accessible Henry region per material
    lg = np.array([r["log10_c_henry_over_c_in_median"] for r in iso["rows"]])
    lg_plot = np.clip(lg, -20, None)          # the tail runs to -509; clip for display
    n_clipped = int((lg < -20).sum())
    c.hist(lg_plot, bins=30, color="#4a5c6a")
    c.axvline(-3, color="#b5423f", lw=1.2, ls="--")
    c.set_xlabel(r"$\log_{10}$(top of the Henry region / feed $c_{in}$)")
    c.set_ylabel("materials")
    c.set_title("C. Henry's law holds everywhere; the region does not",
                fontsize=9.5, loc="left")
    c.text(-3.15, c.get_ylim()[1] * 0.95, f"{iso['n_henry_region_below_1e3_of_feed']} materials "
           f"below\n$10^{{-3}}$ of the feed", ha="right", va="top", fontsize=7, color="#b5423f")
    c.text(0.02, 0.55, f"$n>1$ strictly for all {iso['n_materials']}, so $K_H$ is finite\n"
                       f"and positive everywhere; $K_H$ itself spans\n"
                       f"{iso['K_H']['decades']:.1f} decades"
                       + (f"\n({n_clipped} materials clipped at $10^{{-20}}$)" if n_clipped else ""),
           transform=c.transAxes, fontsize=7, color="0.35", va="top")

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig2_dataset.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/Fig2_dataset.png/.pdf  "
          f"({len(mats)} materials: {n_train} training, {n_held} held out; "
          f"Da {da.min():.1f}-{da.max():.0f}; {n_clipped} Henry outliers clipped)")


if __name__ == "__main__":
    main()
