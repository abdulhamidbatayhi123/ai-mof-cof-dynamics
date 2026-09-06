"""Figure: the rungs that measure a curve — L1's arms, the learning curve, L2, L3.

Every series is read from a results file: `l1_v2_verdict.json`,
`learning_curve_v2_verdict.json`, `l2_v2_verdict.json` and `l3_merged.json`. No model
is evaluated here.

  A  L1-v2, the fixed-basis arms over 240 held-out materials, against the POD floor.
  B  the materials learning curve, refit basis vs basis fixed on all 192 — the two
     curves lie on top of each other, which is the whole point: none of the gain is
     in the basis.
  C  L2-v2, the capacity sweep. Held-out error is U-shaped in depth while training
     error falls monotonically; the optimum moved from where the smaller dataset
     left it (A26).
  D  L3, each family at its own best learning rate at three matched budgets. The
     families optimise three orders of magnitude apart, which is itself a result.

    python fig_rungs.py
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
C_MLP, C_XGB, C_RF, C_RIDGE = "#3b6ea5", "#e08b3a", "#6a994e", "#b5423f"
C_FLOOR = "0.35"

PENDING_RESULTS = ()


def main():
    l1 = json.load(open("results/l1_v2_verdict.json"))
    lc = json.load(open("results/learning_curve_v2_verdict.json"))
    l2 = json.load(open("results/l2_v2_verdict.json"))
    l3 = json.load(open("results/l3_merged.json"))

    fig, axes = plt.subplots(1, 4, figsize=(15.2, 3.6))
    a, b, c, d = axes
    fig.subplots_adjust(wspace=0.46)

    # ---- A: the L1 arms
    tab = l1["folds"]["table"]
    order = sorted(tab, key=lambda k: tab[k]["c"])
    cols = {"mlp": C_MLP, "xgb": C_XGB, "rf": C_RF, "ridge": C_RIDGE}
    x = np.arange(len(order))
    a.bar(x, [tab[k]["c"] for k in order],
          yerr=[tab[k].get("c_sd_seeds", 0.0) for k in order], capsize=3,
          color=[cols[k] for k in order], width=0.62)
    floor = l1["folds"]["pod_floor_pooled"]["c"]
    a.axhline(floor, color=C_FLOOR, lw=1.3, ls="--")
    a.text(len(order) - 0.5, floor * 1.5, f"POD floor {floor:.1e}", ha="right",
           fontsize=6.8, color=C_FLOOR)
    for xi, k in zip(x, order):
        a.text(xi, tab[k]["c"] * 1.04, f"{tab[k]['c']:.4f}", ha="center", fontsize=7)
    a.set_yscale("log")
    a.set_xticks(x); a.set_xticklabels(order, fontsize=8)
    a.set_ylabel("held-out nRMSE (c), 240 materials")
    best = l1["folds"]["best"]
    a.set_title(f"A. L1 arms: {best} is best, in every fold", fontsize=9.5, loc="left")
    a.text(0.02, 0.14, f"best arm is {tab[best]['x_floor']:.0f}x the floor",
           transform=a.transAxes, fontsize=7, color="0.35")

    # ---- B: the learning curve, refit vs fixed basis
    rows = lc["axes"]["materials"]["rows"]
    n = np.array([r["n_materials"] for r in rows])
    refit = np.array([r["refit"] for r in rows])
    fixed = np.array([r["fixed"] for r in rows])
    sd = np.array([r["refit_sd_seeds"] for r in rows])
    b.errorbar(n, refit, yerr=sd, marker="o", ms=5, lw=1.8, color=C_MLP, capsize=3,
               label="basis refit on the subset")
    b.plot(n, fixed, marker="s", ms=4, lw=1.2, ls="--", color="#b5423f", mfc="none",
           label="basis fixed on all 192")
    beta = lc["axes"]["materials"]["beta"]
    ci = lc["axes"]["materials"]["beta_ci"]
    b.plot(n, refit[0] * (n / n[0]) ** (-beta), lw=1.0, color="0.5", ls=":",
           label=f"$n^{{-{beta:.3f}}}$ [{ci[0]:.3f}, {ci[1]:.3f}]")
    b.set_xscale("log"); b.set_yscale("log")
    b.set_xticks(n); b.set_xticklabels([str(int(v)) for v in n])
    b.set_xlabel("training materials"); b.set_ylabel("held-out nRMSE (c)")
    b.set_title("B. every step significant, the last included", fontsize=9.5, loc="left")
    b.legend(fontsize=6.8, loc="upper right")
    b.text(0.03, 0.06, "the two curves coincide:\nnone of the gain is in the basis",
           transform=b.transAxes, fontsize=7, color="0.35")

    # ---- C: the capacity sweep
    dep = l2["families"]["mlp_depth"]["rows"]
    cap = np.array([r["capacity"] for r in dep])
    test = np.array([r["test_c"] for r in dep])
    train = np.array([r["train_c"] for r in dep])
    tsd = np.array([r["test_c_sd_seeds"] for r in dep])
    c.errorbar(cap, test, yerr=tsd, marker="o", ms=5, lw=1.8, color=C_MLP, capsize=3,
               label="held out")
    c.plot(cap, train, marker="s", ms=4, lw=1.4, color="0.55", ls="--", label="training")
    bi = int(np.argmin(test))
    c.plot([cap[bi]], [test[bi]], "o", ms=11, mfc="none", mec="#b5423f", mew=1.8)
    c.annotate(f"optimum {dep[bi]['label']}", (cap[bi], test[bi]),
               textcoords="offset points", xytext=(6, 14), fontsize=7.5, color="#b5423f")
    c.set_xlabel("MLP depth (hidden layers)"); c.set_ylabel("nRMSE (c)")
    c.set_yscale("log")
    c.set_title("C. L2: U-shaped; the optimum moved", fontsize=9.5, loc="left")
    c.legend(fontsize=7.5, loc="upper right")
    cross = l2.get("cross", {}).get("comparisons", {})
    key = next((k for k in cross if "L1 setting" in k), None)
    if key:
        r = cross[key]["relative_to_b"]
        c.text(0.03, 0.06, f"{r['pct']:+.1f} % vs the L1 setting\n"
                           f"[{r['pct_ci_low']:+.1f}, {r['pct_ci_high']:+.1f}]",
               transform=c.transAxes, fontsize=7, color="0.35")

    # ---- D: L3, each family at its own best learning rate
    budgets = sorted({int(k.split("_")[0]) for k in l3["table"]})
    fams = ["mlp", "rbf_kan", "cheby_kan"]
    fcol = {"mlp": C_MLP, "rbf_kan": C_XGB, "cheby_kan": C_RIDGE}
    w = 0.26
    xb = np.arange(len(budgets))
    for i, f in enumerate(fams):
        vals = [l3["table"][f"{bud}_{f}"]["novel"] for bud in budgets]
        lrs = [l3["table"][f"{bud}_{f}"]["lr"] for bud in budgets]
        d.bar(xb + (i - 1) * w, vals, width=w, color=fcol[f], label=f)
        for xi, v, lr in zip(xb + (i - 1) * w, vals, lrs):
            d.text(xi, v * 0.5, f"{lr:g}", ha="center", va="center", fontsize=6.0,
                   rotation=90, color="white")
    d.set_xticks(xb); d.set_xticklabels([f"{b // 1000}k" for b in budgets])
    d.set_xlabel("matched parameter budget"); d.set_ylabel("held-out nRMSE (c), 12 materials")
    d.set_title("D. L3: the MLP wins at every budget", fontsize=9.5, loc="left")
    d.set_ylim(0, max(l3["table"][k]["novel"] for k in l3["table"]) * 1.42)
    d.legend(fontsize=7.5, loc="upper left")
    # The note about the in-bar learning-rate labels lives in the manuscript caption:
    # at this width any in-figure placement collides with the legend or the bars.

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig3_rungs.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/Fig3_rungs.png/.pdf  "
          f"(L1 best {best} {tab[best]['c']:.4f}; beta {beta:.3f}; "
          f"L2 optimum {dep[bi]['label']}; L3 {len(budgets)} budgets)")


if __name__ == "__main__":
    main()
