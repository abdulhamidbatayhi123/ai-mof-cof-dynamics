"""Figure 3: the rungs that measure a curve (L1's arms, the learning curve, L2, L3).

Every series is read from a results file: `l1_v2_verdict.json`,
`learning_curve_v2_verdict.json`, `l2_v2_verdict.json`, `l2_v2_selection.json`,
`l3_merged.json` and `l3_selection.json`. No model is evaluated here. Drawn at the
printed width (7.2 in) so the text is legible at journal size.

  A  L1-v2, the fixed-basis arms over 240 held-out materials, against the POD floor.
  B  the materials learning curve, basis refit on each subset vs fixed on all 192:
     the two curves lie on top of each other, so none of the gain is in the basis.
  C  L2-v2, the depth sweep: held-out error U-shaped while training error falls; the
     gain over the L1 setting is quoted with its selection-adjusted interval.
  D  L3, each family at its own best learning rate at three matched budgets, with the
     number of comparisons that stay significant once both choices are paid for.

    python fig_rungs.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter, LogLocator, NullFormatter

import figstyle as fs

OUT = "figures"
PENDING_RESULTS = ()


def log_ticks(ax, subs, fmt):
    ax.yaxis.set_major_locator(LogLocator(subs=subs))
    ax.yaxis.set_major_formatter(FormatStrFormatter(fmt))
    ax.yaxis.set_minor_formatter(NullFormatter())


def main():
    fs.apply()
    l1 = json.load(open("results/l1_v2_verdict.json"))
    lc = json.load(open("results/learning_curve_v2_verdict.json"))
    l2 = json.load(open("results/l2_v2_verdict.json"))
    l2s = json.load(open("results/l2_v2_selection.json"))
    l3 = json.load(open("results/l3_merged.json"))
    l3s = json.load(open("results/l3_selection.json"))

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.7))
    (a, b), (c, d) = axes
    fig.subplots_adjust(wspace=0.42, hspace=0.58)

    # ---- A: the L1 arms
    tab = l1["folds"]["table"]
    order = sorted(tab, key=lambda k: tab[k]["c"])
    x = np.arange(len(order))
    a.bar(x, [tab[k]["c"] for k in order],
          yerr=[tab[k].get("c_sd_seeds", 0.0) for k in order], capsize=2.5,
          color=[fs.ARM_COLOUR[k] for k in order], width=0.62)
    floor = l1["folds"]["pod_floor_pooled"]["c"]
    a.axhline(floor, color=fs.C["dark"], lw=1.0, ls="--")
    a.text(-0.4, floor * 1.35, f"basis floor {floor:.1e}", ha="left", fontsize=7, color=fs.C["dark"])
    for xi, k in zip(x, order):
        a.text(xi, tab[k]["c"] * 1.07, f"{tab[k]['c']:.4f}", ha="center", fontsize=6.8)
    a.set_yscale("log")
    a.set_ylim(floor * 0.6, max(tab[k]["c"] for k in order) * 2.2)
    a.set_xticks(x)
    a.set_xticklabels([fs.name(k).replace(" ", "\n", 1) if len(fs.name(k)) > 10 else fs.name(k)
                       for k in order])
    a.set_ylabel("held-out nRMSE (c)")
    best = l1["folds"]["best"]
    a.set_title(f"A  L1: the {fs.name(best)} is the best arm in every fold")

    # ---- B: the learning curve, refit vs fixed basis
    rows = lc["axes"]["materials"]["rows"]
    n = np.array([r["n_materials"] for r in rows])
    refit = np.array([r["refit"] for r in rows])
    fixed = np.array([r["fixed"] for r in rows])
    sd = np.array([r["refit_sd_seeds"] for r in rows])
    b.errorbar(n, refit, yerr=sd, marker="o", ms=4, color=fs.C["blue"], capsize=2.5,
               label="basis refit on each subset")
    b.plot(n, fixed, marker="s", ms=3.5, lw=1.0, ls="--", color=fs.C["red"], mfc="none",
           label="basis fixed on all 192")
    beta = lc["axes"]["materials"]["beta"]
    ci = lc["axes"]["materials"]["beta_ci"]
    b.plot(n, refit[0] * (n / n[0]) ** (-beta), lw=0.9, color="0.45", ls=":")
    b.set_xscale("log"); b.set_yscale("log")
    b.set_xticks(n); b.set_xticklabels([str(int(v)) for v in n])
    b.xaxis.set_minor_formatter(NullFormatter())
    log_ticks(b, (1, 2, 3, 4, 5, 6, 8), "%.2f")
    b.set_xlabel("training materials $N_{mat}$"); b.set_ylabel("held-out nRMSE (c)")
    b.set_title("B  L1: error keeps falling with materials")
    b.legend(loc="lower left")
    b.text(0.97, 0.95, f"dotted: fit $\\propto N_{{mat}}^{{-{beta:.3f}}}$ (CI {ci[0]:.3f} to {ci[1]:.3f})\n"
                       "the two curves coincide:\nnone of the gain is in the basis",
           transform=b.transAxes, ha="right", va="top", fontsize=6.8, color="0.3")

    # ---- C: the depth sweep
    dep = l2["families"]["mlp_depth"]["rows"]
    cap = np.array([r["capacity"] for r in dep])
    test = np.array([r["test_c"] for r in dep])
    train = np.array([r["train_c"] for r in dep])
    tsd = np.array([r["test_c_sd_seeds"] for r in dep])
    c.errorbar(cap, test, yerr=tsd, marker="o", ms=4, color=fs.C["blue"], capsize=2.5,
               label="held out")
    c.plot(cap, train, marker="s", ms=3.5, lw=1.1, color="0.5", ls="--", label="training")
    bi = int(np.argmin(test))
    c.plot([cap[bi]], [test[bi]], "o", ms=9, mfc="none", mec=fs.C["red"], mew=1.4)
    c.annotate(f"best: depth {int(cap[bi])}, {l2s['pct']:+.1f} % vs the L1 setting\n"
               f"selection-adjusted [{l2s['pct_sim_lo']:+.1f}, {l2s['pct_sim_hi']:+.1f}] %",
               (cap[bi], test[bi]), textcoords="axes fraction", xytext=(0.03, 0.03), ha="left",
               fontsize=6.6, color=fs.C["red"])
    c.set_xlabel("MLP depth (hidden layers)"); c.set_ylabel("nRMSE (c)")
    c.set_yscale("log")
    c.set_ylim(min(train) * 0.72, max(test) * 1.06)     # an empty band at the bottom for the note
    log_ticks(c, (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8), "%.3f")
    c.set_title("C  L2: held-out error is U-shaped in depth")
    c.legend(loc="upper right")

    # ---- D: L3, each family at its own best learning rate
    budgets = sorted({int(k.split("_")[0]) for k in l3["table"]})
    fams = ["mlp", "rbf_kan", "cheby_kan"]
    w = 0.26
    xb = np.arange(len(budgets))
    for i, f in enumerate(fams):
        vals = [l3["table"][f"{bud}_{f}"]["novel"] for bud in budgets]
        d.bar(xb + (i - 1) * w, vals, width=w, color=fs.ARM_COLOUR[f], label=fs.name(f))
    d.set_xticks(xb); d.set_xticklabels([f"{bb // 1000}k" for bb in budgets])
    d.set_xlabel("matched parameter budget"); d.set_ylabel("held-out nRMSE (c)")
    d.set_title("D  L3: the MLP leads at every budget")
    d.set_ylim(0, max(l3["table"][k]["novel"] for k in l3["table"]) * 1.75)
    d.legend(loc="upper left")
    d.text(0.98, 0.97, f"{l3s['n_sig_simultaneous']} of {l3s['n_pairs']} significant\n"
                       f"after selection,\nnone reversed",
           transform=d.transAxes, ha="right", va="top", fontsize=6.8, color="0.3")

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig3_rungs.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig3_rungs.png/.pdf  "
          f"(L1 best {best} {tab[best]['c']:.4f}; beta {beta:.3f}; "
          f"L2 best depth {int(cap[bi])}; L3 {len(budgets)} budgets)")


if __name__ == "__main__":
    main()
