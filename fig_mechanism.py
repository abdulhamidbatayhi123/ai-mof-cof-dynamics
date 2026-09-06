"""Figure: the mechanism — basis error vs coefficient-map error, and what binds.

Every series is read from results files (`results/l5_merged.json`,
`results/l5_fno_verdict.json`, `results/l5_bottleneck.json`); nothing is fitted or
synthesised. Legacy dataset, 128x128 encoding, 12 held-out materials, each family at
its own best learning rate (analyze_l5_merged, grid-boundary guard applied).

  A  held-out nRMSE vs basis size p: the POD floor falls 28.7x; POD + the strongest
     regressor, DeepONet and DeepOKAN are flat; FNO (no p) is the horizontal line.
  B  the two terms of a linear reconstruction, in the OPTIMAL basis: basis error
     (true coefficients) vs coefficient-map error (predicted coefficients).
  C  per-mode R2 of the coefficient map on held-out materials at p = 128.

    python fig_mechanism.py
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
    m = json.load(open("results/l5_merged.json"))
    fno = json.load(open("results/l5_fno_verdict.json"))
    bt = json.load(open("results/l5_bottleneck.json"))
    ps = sorted(int(p) for p in m["pod_floor"])
    floor = np.array([m["pod_floor"][str(p)] for p in ps])
    onet = np.array([m["selected"][f"deeponet_p{p}"]["mean"] for p in ps])
    okan = np.array([m["selected"][f"deepokan_p{p}"]["mean"] for p in ps])
    rows = {r["p"]: r for r in bt["rows"]}
    coef = np.array([rows[p]["coef_pred_novel"] for p in ps])
    basis = np.array([rows[p]["basis_floor_novel"] for p in ps])

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(12.5, 3.6))
    fig.subplots_adjust(wspace=0.45)

    a.loglog(ps, floor, "k--", lw=1.4, label="POD floor (n-width bound)")
    a.loglog(ps, coef, "o-", color="#e08b3a", lw=1.8, ms=5, label="POD + strongest regressor")
    a.loglog(ps, okan, "^-", color="#b5423f", lw=1.6, ms=5, label="DeepOKAN, best lr per p")
    a.loglog(ps, onet, "s-", color="#3b6ea5", lw=1.8, ms=5, label="DeepONet, best lr per p")
    a.axhline(fno["fno_best"]["mean"], color="#6a994e", lw=1.8, ls="-.",
              label=f"FNO, best (modes {fno['fno_best']['modes']}), no p")
    a.set_xticks(ps); a.set_xticklabels([str(p) for p in ps])
    a.set_xlabel("basis size p"); a.set_ylabel("held-out nRMSE (c), 12 materials")
    a.set_title("A. the floor falls 28.7x; every arm is flat")
    a.legend(fontsize=6.8, loc="lower left")
    a.text(ps[-1], floor[-1] * 1.6, f"{onet[-1] / floor[-1]:.0f}x above\nthe floor", fontsize=7, ha="right", color="0.3")

    b.loglog(ps, basis, "k--", lw=1.4, marker="o", ms=4, label="basis error (true coefficients)")
    b.loglog(ps, coef, "o-", color="#e08b3a", lw=1.8, ms=5, label="coefficient-map error (predicted)")
    b.set_xticks(ps); b.set_xticklabels([str(p) for p in ps])
    b.set_xlabel("basis size p"); b.set_ylabel("held-out nRMSE (c), optimal basis")
    b.set_title("B. what binds: the parameter → coefficient map")
    b.legend(fontsize=7, loc="lower left")
    for p, bv, cv in zip(ps, basis, coef):
        b.annotate("", xy=(p, cv), xytext=(p, bv), arrowprops=dict(arrowstyle="-", color="0.75", lw=0.8))

    r2 = np.array(rows[ps[-1]]["mode_r2_novel"])
    k = np.arange(1, len(r2) + 1)
    colors = np.where(r2 > 0.5, "#3b6ea5", np.where(r2 > 0.2, "#e08b3a", "0.75"))
    c.bar(k, np.clip(r2, -0.3, 1.0), color=colors, width=0.9)
    c.axhline(0.5, color="#3b6ea5", lw=0.8, ls=":"); c.axhline(0.2, color="#e08b3a", lw=0.8, ls=":")
    c.axhline(0.0, color="k", lw=0.6)
    c.set_xscale("log"); c.set_xlim(0.8, len(r2) + 1)
    c.set_ylim(-0.3, 1.0)
    c.set_xlabel(f"POD mode (p = {ps[-1]})"); c.set_ylabel("R² on held-out materials")
    n5, n2 = int((r2 > 0.5).sum()), int((r2 > 0.2).sum())
    c.set_title(f"C. per-mode R²: {n5} modes > 0.5, {n2} > 0.2")
    c.text(0.98, 0.92, "48 training materials\n(legacy); on v2 with 192\nmaterials: 3 and 13 of 32",
           transform=c.transAxes, ha="right", va="top", fontsize=7, color="0.3")

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig5_mechanism.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/Fig5_mechanism.png/.pdf")


if __name__ == "__main__":
    main()
