"""Figure: L5 — the operator rung, and why a bigger basis buys nothing.

Every series is read from `results/l5_merged.json`, `results/l5_fno_verdict.json` and
`results/l5_bottleneck.json`. No model is evaluated here.

This is deliberately NOT a second copy of the mechanism figure. That one decomposes
the error into its basis and coefficient-map terms; this one is about the ARMS: what
each family reaches, how flat they are in basis size, and where the Fourier operator
lands relative to a bound that falls out from under all of them.

  A  held-out error against basis size, with the proper-orthogonal-decomposition
     floor. The floor falls; nothing else does. The Fourier operator has no p and is
     drawn as a horizontal line.
  B  the paired comparisons against p = 8, which is what "flat" means here: four
     intervals, all spanning zero, while the bound beneath falls.
  C  the oracle calibration --- how many true coefficients each method is worth.

    python fig_operators.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "figure.dpi": 160, "savefig.dpi": 600, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})
OUT = "figures"
C_ONET, C_OKAN, C_FNO, C_COEF = "#3b6ea5", "#b5423f", "#6a994e", "#e08b3a"

PENDING_RESULTS = ()


def main():
    m = json.load(open("results/l5_merged.json"))
    fno = json.load(open("results/l5_fno_verdict.json"))
    bt = json.load(open("results/l5_bottleneck.json"))

    ps = sorted(int(p) for p in m["pod_floor"])
    floor = np.array([m["pod_floor"][str(p)] for p in ps])
    onet = np.array([m["selected"][f"deeponet_p{p}"]["mean"] for p in ps])
    okan = np.array([m["selected"][f"deepokan_p{p}"]["mean"] for p in ps])
    rows = {r["p"]: r for r in bt["rows"]}
    coef = np.array([rows[p]["coef_pred_novel"] for p in ps])

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(12.6, 3.6))
    fig.subplots_adjust(wspace=0.42)

    # ---- A: the arms, and the floor falling out from under them
    a.loglog(ps, floor, "k--", lw=1.5, marker="o", ms=4, label="POD floor (the n-width bound)")
    a.loglog(ps, coef, "o-", color=C_COEF, lw=1.7, ms=5, label="POD + strongest regressor")
    a.loglog(ps, okan, "^-", color=C_OKAN, lw=1.6, ms=5, label="DeepOKAN")
    a.loglog(ps, onet, "s-", color=C_ONET, lw=1.8, ms=5, label="DeepONet")
    fb = fno["fno_best"]
    a.axhline(fb["mean"], color=C_FNO, lw=1.8, ls="-.",
              label=f"FNO (modes {fb['modes']}, no p)")
    a.set_xticks(ps); a.set_xticklabels([str(p) for p in ps])
    a.set_xlabel("basis size $p$"); a.set_ylabel("held-out nRMSE (c), 12 materials")
    drop = floor[0] / floor[-1]
    a.set_title(f"A. the bound falls {drop:.0f}x; no arm follows it", fontsize=9.5, loc="left")
    a.legend(fontsize=6.6, loc="lower left")
    a.annotate("", xy=(ps[-1], floor[-1]), xytext=(ps[-1], onet[-1]),
               arrowprops=dict(arrowstyle="<->", color="0.45", lw=1.0))
    a.text(ps[-1] * 0.92, np.sqrt(floor[-1] * onet[-1]),
           f"{onet[-1] / floor[-1]:.0f}x", ha="right", fontsize=7.5, color="0.3")

    # ---- B: what "flat" means -- the paired comparisons against p = 8
    cmp_ = m["paired_vs_smallest_p"]
    keys = [f"deeponet_p{p}" for p in ps[1:] if f"deeponet_p{p}" in cmp_]
    y = np.arange(len(keys))[::-1]
    for yi, k in zip(y, keys):
        r = cmp_[k]
        col = "#8a8a8a" if not r["significant"] else C_ONET
        b.plot([r["ci_low"], r["ci_high"]], [yi, yi], color=col, lw=2.4,
               solid_capstyle="butt")
        b.plot([r["ci_low"], r["ci_high"]], [yi, yi], "|", color=col, ms=8)
        b.plot([r["mean_diff"]], [yi], "o", color=col, ms=7)
    b.axvline(0, color="k", lw=1.0)
    b.set_yticks(y); b.set_yticklabels([k.replace("deeponet_", "") + " vs p8" for k in keys],
                                       fontsize=8)
    b.set_xlabel("paired difference in nRMSE vs $p = 8$")
    n_null = sum(1 for k in keys if not cmp_[k]["significant"])
    b.set_title(f"B. {n_null}/{len(keys)} intervals span zero", fontsize=9.5, loc="left")
    b.set_ylim(-0.9, len(keys) - 0.1)
    b.text(0.5, 0.02, "a sixteenfold larger basis, and no detectable change",
           transform=b.transAxes, ha="center", va="bottom", fontsize=7, color="0.35")

    # ---- C: the oracle calibration
    r128 = rows[ps[-1]]
    r2 = np.array(r128["mode_r2_novel"])
    k = np.arange(1, len(r2) + 1)
    cols = np.where(r2 > 0.5, C_ONET, np.where(r2 > 0.2, C_COEF, "0.78"))
    c.bar(k, np.clip(r2, -0.3, 1.0), color=cols, width=0.9)
    c.axhline(0.5, color=C_ONET, lw=0.8, ls=":")
    c.axhline(0.2, color=C_COEF, lw=0.8, ls=":")
    c.axhline(0.0, color="k", lw=0.6)
    c.set_xscale("log"); c.set_xlim(0.8, len(r2) + 1); c.set_ylim(-0.3, 1.0)
    c.set_xlabel(f"POD mode index (at $p = {ps[-1]}$)")
    c.set_ylabel("$R^2$ of the coefficient map,\nheld-out materials")
    n5, n2 = int((r2 > 0.5).sum()), int((r2 > 0.2).sum())
    c.set_title(f"C. only {n5} of {len(r2)} modes clear $R^2>0.5$", fontsize=9.5, loc="left")
    c.text(0.98, 0.93, f"{n2} clear 0.2\nthe rest are worse than\npredicting the mean",
           transform=c.transAxes, ha="right", va="top", fontsize=7, color="0.35")

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig4_operators.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/Fig4_operators.png/.pdf  (floor falls {drop:.1f}x; "
          f"DeepONet {onet[-1]/floor[-1]:.0f}x above it; FNO {fb['mean']/floor[-1]:.0f}x; "
          f"{n_null}/{len(keys)} paired intervals span zero)")


if __name__ == "__main__":
    main()
