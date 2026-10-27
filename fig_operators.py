"""Figure 4: basis size, on both designs, and why the legacy null was retracted (A29).

Every series is read from results files: `results/l5_merged.json`,
`results/l5_fno_verdict.json`, `results/l5_bottleneck.json` (legacy design, 12
held-out materials) and `results/l5_v2_verdict_24k.json`, `results/l5_bottleneck_v2.json`
(full design, 240 materials in five folds). No model is evaluated here. Drawn at the
printed width.

  A  legacy design: held-out error of each operator family against basis size, with
     the basis floor; the Fourier operator has no basis size and is a level.
  B  full design: DeepONet against basis size (one point per fold, line through the
     means), the per-mode gradient-boosting map, and the basis floor.
  C  the paired differences against p = 8 on both designs: the legacy intervals span
     zero; on the full design every larger basis is better. Per-pair intervals; the
     p = 128 comparison also survives the selection adjustment (PREREG_L5_v2 A3).

The mechanism figure (Figure 5) decomposes the error into its basis and map terms;
this one is about the arms and the basis-size verdict.

    python fig_operators.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullFormatter

import figstyle as fs

OUT = "figures"
PENDING_RESULTS = ()


def main():
    fs.apply()
    m = json.load(open("results/l5_merged.json"))
    fno = json.load(open("results/l5_fno_verdict.json"))
    bt = json.load(open("results/l5_bottleneck.json"))
    v2 = json.load(open("results/l5_v2_verdict_24k.json"))
    bt2 = json.load(open("results/l5_bottleneck_v2.json"))

    ps = sorted(int(p) for p in m["pod_floor"])
    floor = np.array([m["pod_floor"][str(p)] for p in ps])
    onet = np.array([m["selected"][f"deeponet_p{p}"]["mean"] for p in ps])
    okan = np.array([m["selected"][f"deepokan_p{p}"]["mean"] for p in ps])
    rows = {r["p"]: r for r in bt["rows"]}
    coef = np.array([rows[p]["coef_pred_novel"] for p in ps])

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.2, 3.1))
    fig.subplots_adjust(wspace=0.55, top=0.76, bottom=0.17)

    def xaxis(ax):
        ax.set_xscale("log")
        ax.set_xticks(ps); ax.set_xticklabels([str(p) for p in ps])
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel("basis size $p$")

    # ---- A: legacy design, the arms and the floor
    a.plot(ps, floor, "--", color=fs.C["dark"], marker="o", ms=3, lw=1.1)
    a.plot(ps, coef, "o-", color=fs.ARM_COLOUR["pod_reg"], ms=3)
    a.plot(ps, okan, "^-", color=fs.ARM_COLOUR["deepokan"], ms=3)
    a.plot(ps, onet, "s-", color=fs.ARM_COLOUR["deeponet"], ms=3)
    a.axhline(fno["fno_best"]["mean"], color=fs.ARM_COLOUR["fno"], lw=1.3, ls="-.")
    a.set_yscale("log"); xaxis(a)
    a.set_ylabel("held-out nRMSE (c)")
    a.set_title("A  Legacy (12 materials)")

    # ---- B: full design, DeepONet per fold, the per-mode map, the floor
    ps2 = sorted(int(p) for p in v2["pod_floor_pooled"])
    floor2 = np.array([v2["pod_floor_pooled"][str(p)] for p in ps2])
    on2 = np.array([v2["selected"][f"deeponet_p{p}"]["mean"] for p in ps2])
    folds = np.array([v2["selected"][f"deeponet_p{p}"]["per_fold"] for p in ps2])
    coef2 = np.array([bt2["summary"][str(p)]["coef_pred"] for p in ps2])
    b.plot(ps2, floor2, "--", color=fs.C["dark"], marker="o", ms=3, lw=1.1)
    b.plot(ps2, coef2, "o-", color=fs.ARM_COLOUR["pod_reg"], ms=3)
    for j in range(folds.shape[1]):
        b.plot(ps2, folds[:, j], "o", color=fs.ARM_COLOUR["deeponet"], ms=2.4, alpha=0.6, mec="none")
    b.plot(ps2, on2, "s-", color=fs.ARM_COLOUR["deeponet"], ms=3)
    b.set_yscale("log"); xaxis(b)
    b.set_ylabel("held-out nRMSE (c)")
    b.set_title("B  Smooth design (v2, 240 materials)")
    b.text(0.04, 0.04, f"DeepONet over\nthe floor:\n{on2[0] / floor2[0]:.1f}× at $p$ = 8\n"
                       f"{on2[-1] / floor2[-1]:.0f}× at $p$ = 128",
           transform=b.transAxes, ha="left", va="bottom", fontsize=7.2, color="0.25")

    # ---- C: paired differences against p = 8, both designs
    leg = m["paired_vs_smallest_p"]
    full = v2["paired_vs_smallest_p"]
    rows_c = [p for p in ps[1:]]
    for i, p in enumerate(rows_c):
        for off, src, col, mfc in ((-0.16, leg, "0.55", "white"), (0.16, full, fs.C["dark"], fs.C["dark"])):
            r = src.get(f"deeponet_p{p}")
            if r is None:
                continue
            base = (m["selected"]["deeponet_p8"]["mean"] if src is leg
                    else v2["selected"]["deeponet_p8"]["mean"])
            lo, hi, mu = (100 * r[k] / base for k in ("ci_low", "ci_high", "mean_diff"))
            y = len(rows_c) - 1 - i + off
            c.plot([lo, hi], [y, y], color=col, lw=2.0, solid_capstyle="butt")
            c.plot([mu], [y], "o", color=col, mfc=mfc, mew=1.2, ms=4.5, zorder=3)
    c.axvline(0, color="k", lw=0.8)
    c.set_yticks(range(len(rows_c))); c.set_yticklabels([f"$p$ = {p}" for p in rows_c[::-1]])
    c.set_xlabel("gain vs $p$ = 8 (%)")
    c.set_title("C  Gain vs $p$ = 8")
    c.grid(axis="y", visible=False)

    handles = [plt.Line2D([], [], color=fs.ARM_COLOUR["deeponet"], marker="s", ms=3, label="DeepONet"),
               plt.Line2D([], [], color=fs.ARM_COLOUR["deepokan"], marker="^", ms=3, label="DeepOKAN"),
               plt.Line2D([], [], color=fs.ARM_COLOUR["pod_reg"], marker="o", ms=3, label="POD + gradient boosting"),
               plt.Line2D([], [], color=fs.ARM_COLOUR["fno"], ls="-.", label="Fourier neural operator"),
               plt.Line2D([], [], color=fs.C["dark"], ls="--", marker="o", ms=3, label="basis floor"),
               plt.Line2D([], [], color="0.55", lw=2, marker="o", mfc="white", ms=4.5, label="C: legacy design"),
               plt.Line2D([], [], color=fs.C["dark"], lw=2, marker="o", ms=4.5, label="C: smooth design (v2)")]
    fig.legend(handles=handles, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.03),
               fontsize=7.2, columnspacing=1.0, handlelength=1.8)

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig4_operators.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig4_operators.png/.pdf  (legacy floor falls {floor[0] / floor[-1]:.1f}x; "
          f"full design DeepONet {on2[0]:.4f} -> {on2[-1]:.4f})")


if __name__ == "__main__":
    main()
