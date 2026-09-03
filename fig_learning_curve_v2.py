"""Figure: the materials learning curve on dataset v2 — L1's load-bearing measurement.

Every series is read from `results/learning_curve_v2.json` (5 folds x 3 seeds per
size); nothing is fitted or synthesised here. Panel A is the honest (refit-basis)
curve with the fixed-basis curve on top of it — they coincide, which is the point;
panel B is how many coefficient-map modes become predictable; panel C is the
conditions axis at the full 192 materials.

    python fig_learning_curve_v2.py
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


def main():
    v = json.load(open("results/learning_curve_v2_verdict.json"))
    mat = v["axes"]["materials"]
    con = v["axes"]["conditions"]
    n = np.array([r["n_materials"] for r in mat["rows"]])
    refit = np.array([r["refit"] for r in mat["rows"]])
    fixed = np.array([r["fixed"] for r in mat["rows"]])
    sd = np.array([r["refit_sd_seeds"] for r in mat["rows"]])
    m05 = np.array([r["modes_r2_gt_0.5"] for r in mat["rows"]])
    m02 = np.array([r["modes_r2_gt_0.2"] for r in mat["rows"]])
    r2hi = np.array([r["r2_t_hi"] for r in mat["rows"]])

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(12.5, 3.6))
    fig.subplots_adjust(wspace=0.55)

    # A — the curve
    a.errorbar(n, refit, yerr=sd, fmt="o-", color="#3b6ea5", lw=1.8, ms=5, capsize=3,
               label="basis refit on the subset (honest)")
    a.plot(n, fixed, "s--", color="#e08b3a", lw=1.2, ms=4, mfc="none",
           label="basis fixed on all 192 materials")
    beta, (lo, hi) = mat["beta"], mat["beta_ci"]
    nn = np.array([n[0] * 0.8, n[-1] * 1.25])
    a.plot(nn, refit[0] * (nn / n[0]) ** (-beta), ":", color="0.35", lw=1,
           label=r"$n^{-%.3f}$  (CI %.3f–%.3f)" % (beta, lo, hi))
    a.set_xscale("log"); a.set_yscale("log")
    a.set_xticks(n); a.set_xticklabels([str(int(x)) for x in n])
    a.set_xlabel("training materials"); a.set_ylabel("held-out nRMSE (c), 240 materials")
    a.set_title("A. more materials: still falling at 192")
    a.legend(fontsize=7, loc="upper right")
    a.annotate("last step\nsignificant", xy=(n[-1], refit[-1]), xytext=(n[-2] * 0.75, refit[-1] * 0.93),
               fontsize=7, color="#3b6ea5", ha="center",
               arrowprops=dict(arrowstyle="-", color="#3b6ea5", lw=0.6))

    # B — what becomes predictable
    b.plot(n, m02, "o-", color="#b5423f", lw=1.8, label="modes with R² > 0.2")
    b.plot(n, m05, "s-", color="#3b6ea5", lw=1.8, label="modes with R² > 0.5")
    b.set_xscale("log"); b.set_xticks(n); b.set_xticklabels([str(int(x)) for x in n])
    b.set_xlabel("training materials"); b.set_ylabel("coefficient-map modes (of 32)")
    b.set_title("B. all of the gain is in the coefficient map")
    b2 = b.twinx()
    b2.plot(n, r2hi, "^:", color="0.4", lw=1.2, label="R² of the shock arrival $t_{hi}(z)$")
    b2.set_ylim(0.7, 0.95); b2.set_ylabel("R² ($t_{hi}$)", color="0.4")
    b2.grid(False)
    h1, l1 = b.get_legend_handles_labels(); h2, l2 = b2.get_legend_handles_labels()
    b.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper left")

    # C — conditions axis
    fr = np.array([r["size"] for r in con["rows"]])
    nt = np.array([r["n_train"] for r in con["rows"]])
    cr = np.array([r["refit"] for r in con["rows"]])
    csd = np.array([r["refit_sd_seeds"] for r in con["rows"]])
    c.errorbar(nt, cr, yerr=csd, fmt="o-", color="#3b6ea5", lw=1.8, ms=5, capsize=3,
               label="fraction of conditions per material")
    for x, y, f in zip(nt, cr, fr):
        c.text(x, y * 1.04, f"{f:.2f}", fontsize=7, ha="center")
    cb, (clo, chi) = con["beta"], con["beta_ci"]
    c.plot(nt, cr[0] * (nt / nt[0]) ** (-cb), ":", color="0.35", lw=1,
           label=r"$n^{-%.3f}$  (CI %.3f–%.3f)" % (cb, clo, chi))
    c.set_xscale("log"); c.set_yscale("log")
    c.set_xlabel("training conditions (all 192 materials)"); c.set_ylabel("held-out nRMSE (c)")
    c.set_title("C. more conditions: half the exponent")
    c.legend(fontsize=7, loc="upper right")
    c.set_ylim(refit.min() * 0.9, refit.max() * 1.1)

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig8_learning_curve_v2.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/Fig8_learning_curve_v2.png/.pdf")


if __name__ == "__main__":
    main()
