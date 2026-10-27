"""Figure: does a surrogate rank materials correctly? Both designs, both breakthrough times.

Every series is read from results/dd_v3a1_verdict.json (PREREG_DD_V3 amendment A1, which
re-scores B1 and V4 with the converged arms and adds t90); no model is evaluated here.
  A, B  t50 (registered): Spearman correlation and top-10 % recall per operating condition
        (small points), with the mean and its cluster-bootstrap interval, for DeepONet, POD with
        gradient boosting and the coarse solve, on the smooth (v2) and MOF-like (v3) designs.
  C, D  the same for t90, the time the outlet reaches 90 % of the feed: set by the main,
        pore-filling front rather than the pre-step wave (amendment A1).
Dotted: the registered thresholds (0.90, 0.80). Dash-dotted: ranking by the stoichiometric time,
which needs no solve.

    python fig_screening.py
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
ARMS = [("don", "DeepONet"), ("hgb", "POD + boosting"), ("coarse", "coarse solve")]
COL = {"don": fs.ARM_COLOUR["deeponet"], "hgb": fs.ARM_COLOUR["pod_reg"], "coarse": fs.C["dark"]}
DESIGNS = (("v2", "smooth (v2)"), ("v3", "MOF-like (v3)"))


def main():
    fs.apply()
    v = json.load(open("results/dd_v3a1_verdict.json"))["screening"]
    fig, axs = plt.subplots(2, 2, figsize=(6.73, 4.9))
    fig.subplots_adjust(wspace=0.28, hspace=0.45, left=0.085, right=0.985, bottom=0.08, top=0.86)
    panels = (("t50", "spearman", 0.90, "A  Rank agreement, $t_{50}$"),
              ("t50", "recall", 0.80, "B  Top-10 % recall, $t_{50}$"),
              ("t90", "spearman", 0.90, "C  Rank agreement, $t_{90}$"),
              ("t90", "recall", 0.80, "D  Top-10 % recall, $t_{90}$"))
    for ax, (which, metric, thr, title) in zip(axs.ravel(), panels):
        for g, (d, _) in enumerate(DESIGNS):
            rec = v[d][which]
            for x, (k, _) in enumerate(ARMS):
                xx = g * 4 + x
                vals = np.asarray(rec[k][f"per_condition_{metric}"], float)
                ax.plot(np.full(len(vals), xx) + np.linspace(-0.18, 0.18, len(vals)), vals, "o", ms=2.6,
                        color=COL[k], alpha=0.6, mec="none")
                m = rec[k][metric]
                lo, hi = rec[k][f"{metric}_ci"]
                # the interval is drawn as computed, not clipped to the point: for the near-perfect
                # coarse solve it can lie just below the observed value, because a bootstrap draw
                # that repeats a material ties its ranks
                ax.vlines(xx, lo, hi, color=COL[k], lw=1.2, zorder=3)
                ax.hlines([lo, hi], xx - 0.12, xx + 0.12, color=COL[k], lw=1.0, zorder=3)
                ax.plot([xx], [m], "s", color=COL[k], ms=3.6, zorder=4)
            bl = rec["baseline_tstoich"][metric]
            ax.plot([g * 4 - 0.4, g * 4 + 2.4], [bl, bl], color="0.55", lw=0.9, ls="-.")
        ax.axhline(thr, color="0.4", lw=0.8, ls=":")
        ax.set_xticks([1, 5]); ax.set_xticklabels([lab for _, lab in DESIGNS])
        ax.set_xlim(-0.7, 6.7)
        ax.set_ylim(0.0, 1.04)
        ax.set_ylabel("Spearman, per condition" if metric == "spearman" else "recall, per condition")
        ax.set_title(title, loc="left")
    fig.legend(handles=[Line2D([], [], color=COL[k], marker="s", ls="", ms=4, label=lab) for k, lab in ARMS] +
               [Line2D([], [], color="0.4", ls=":", label="registered threshold"),
                Line2D([], [], color="0.55", ls="-.", label="no solve: rank by stoichiometric time")],
               loc="upper center", ncol=3, frameon=False, fontsize=7.3, bbox_to_anchor=(0.5, 0.995))
    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig_screening.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig_screening.png/.pdf")


if __name__ == "__main__":
    main()
