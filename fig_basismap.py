"""Figure (Digital Discovery revision): basis error against map error, measured apart.

Every series is read from results files; no model is evaluated here.
  A  results/l5_mapterm_v2.json: the two terms of eq. (split) for POD with per-mode gradient
     boosting and with ridge, against basis size p, plus the basis floor. 240 materials,
     five folds, three seeds, pooled out of fold.
  B  results/l5_v2_verdict_24k.json: DeepONet (basis and coefficients trained together)
     against p, one faint point per fold, with its pooled basis floor.
  C  results/learning_curve_v2_verdict.json: modes whose map clears R^2 = 0.2 and 0.5,
     against the number of training materials.

    python fig_basismap.py
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


def main():
    fs.apply()
    mt = json.load(open("results/l5_mapterm_v2.json"))["summary"]
    v2 = json.load(open("results/l5_v2_verdict_24k.json"))
    lc = json.load(open("results/learning_curve_v2_verdict.json"))["axes"]["materials"]["rows"]

    ps = sorted(int(p) for p in mt)
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.2, 2.6))
    fig.subplots_adjust(wspace=0.5, bottom=0.2, top=0.86)

    def logx(ax, xs):
        ax.set_xscale("log", base=2)
        ax.set_xticks(xs); ax.set_xticklabels([str(x) for x in xs])
        ax.xaxis.set_minor_formatter(NullFormatter())

    floor = [mt[str(p)]["floor"] for p in ps]
    a.plot(ps, floor, "s--", color=fs.C["dark"], ms=3, lw=1.1, label="basis floor")
    a.plot(ps, [mt[str(p)]["map_hgb"] for p in ps], "o-", color=fs.C["blue"], ms=3.2,
           label="map, gradient boosting")
    a.plot(ps, [mt[str(p)]["map_ridge"] for p in ps], "^-", color=fs.C["orange"], ms=3.2,
           label="map, ridge")
    a.set_yscale("log"); logx(a, ps)
    a.set_xlabel("basis size $p$"); a.set_ylabel("held-out nRMSE (c)")
    a.set_title("A  Basis floor and map error")
    a.set_ylim(top=0.15)
    a.text(9, 0.068, "map (ridge)", color=fs.C["orange"], fontsize=7.2)
    a.text(9, 0.021, "map (gradient boosting)", color=fs.C["blue"], fontsize=7.2)
    a.text(34, 1.7e-3, "basis floor", color=fs.C["dark"], fontsize=7.2)

    sel = v2["selected"]
    on = [sel[f"deeponet_p{p}"]["mean"] for p in ps]
    folds = np.array([sel[f"deeponet_p{p}"]["per_fold"] for p in ps])
    fl2 = [v2["pod_floor_pooled"][str(p)] for p in ps]
    for j in range(folds.shape[1]):
        b.plot(ps, folds[:, j], "o", color=fs.ARM_COLOUR["deeponet"], ms=2.2, alpha=0.5, mec="none")
    b.plot(ps, on, "o-", color=fs.ARM_COLOUR["deeponet"], ms=3.2, label="DeepONet")
    b.plot(ps, fl2, "s--", color=fs.C["dark"], ms=3, lw=1.1, label="basis floor")
    b.set_yscale("log"); logx(b, ps)
    b.set_xlabel("basis size $p$"); b.set_ylabel("held-out nRMSE (c)")
    b.set_title("B  DeepONet, trained jointly")
    b.text(9, 0.0135, "DeepONet", color=fs.ARM_COLOUR["deeponet"], fontsize=7.2)
    b.text(34, 1.7e-3, "basis floor", color=fs.C["dark"], fontsize=7.2)

    n = np.array([r["n_materials"] for r in lc])
    c.plot(n, [r["modes_r2_gt_0.2"] for r in lc], "o-", color=fs.C["blue"], ms=3.2, label="$R^2$ > 0.2")
    c.plot(n, [r["modes_r2_gt_0.5"] for r in lc], "s--", color=fs.C["dark"], ms=3, lw=1.1, label="$R^2$ > 0.5")
    c.set_xscale("log"); c.set_xticks(n); c.set_xticklabels([str(int(x)) for x in n])
    c.xaxis.set_minor_formatter(NullFormatter())
    c.set_xlabel("training materials"); c.set_ylabel("modes predicted (of 32)")
    c.set_title("C  More materials, more modes")
    c.legend(loc="upper left", fontsize=7)

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig_basismap.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig_basismap.png/.pdf  (map/floor at p={ps[0]}: "
          f"{mt[str(ps[0])]['map_hgb'] / floor[0]:.1f}x; at p={ps[-1]}: {mt[str(ps[-1])]['map_hgb'] / floor[-1]:.0f}x)")


if __name__ == "__main__":
    main()
