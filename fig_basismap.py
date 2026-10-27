"""Figure: basis error against map error, measured apart, on both isotherm designs.

Every series is read from results files; no model is evaluated here.
  A  results/l5_mapterm_v2.json, results/l5_mapterm_v3.json: the two terms of eq. (split) for
     POD with per-mode gradient boosting (seed 42), against basis size p, pooled out of fold.
  B  results/dd_v3a1_deeponet.json (PREREG_DD_V3 amendment A1): DeepONet's held-out error and its
     own floor (trained trunk kept, coefficients fitted per sample by the converged solver), against p.
  C  results/dd_v3_verdict.json (POD + boosting) and results/dd_v3a1_verdict.json (DeepONet, A1):
     the share of squared error carried by the map, with its cluster-bootstrap interval.
  D  results/learning_curve_v2_verdict.json: modes whose map clears R^2 = 0.2 and 0.5, against
     the number of training materials (design v2).

    python fig_basismap.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import NullFormatter

import figstyle as fs

OUT = "figures"
PS = [8, 16, 32, 64, 128]
DES = {"v2": ("smooth isotherms (v2)", fs.C["blue"]), "v3": ("MOF-like isotherms (v3)", fs.C["red"])}


def mapterm(path):
    res = json.load(open(path))["cells"]
    out = {}
    for p in sorted({c["p"] for c in res.values()}):
        cs = [c for c in res.values() if c["p"] == p and c["seed"] == 42]
        out[p] = (np.mean(np.concatenate([c["floor"] for c in cs])),
                  np.mean(np.concatenate([c["map_hgb"] for c in cs])))
    return out


def deeponet(data):
    """Amendment A1 cells (converged own floor), seed 42, every registered basis size."""
    cells = json.load(open("results/dd_v3a1_deeponet.json"))["cells"]
    out = {}
    for p in (8, 16, 128):
        cs = [c for k, c in cells.items() if k.startswith(f"{data}|p{p}|s42|")]
        if len(cs) == 5:
            out[p] = (np.mean(np.concatenate([c["nrmse_c"] for c in cs])),
                      np.mean(np.concatenate([c["trunk_floor_c"] for c in cs])))
    return out


def logx(ax, xs):
    ax.set_xscale("log", base=2)
    ax.set_xticks(xs); ax.set_xticklabels([str(x) for x in xs])
    ax.xaxis.set_minor_formatter(NullFormatter())


def main():
    fs.apply()
    v = json.load(open("results/dd_v3_verdict.json"))["split"]          # POD + boosting (V1)
    a1 = json.load(open("results/dd_v3a1_verdict.json"))["split_deeponet_own_floor"]   # DeepONet (A1)
    for d in v:
        v[d]["deeponet_own_floor"] = a1[d]
    lc = json.load(open("results/learning_curve_v2_verdict.json"))["axes"]["materials"]["rows"]
    fig, ((a, b), (c, d)) = plt.subplots(2, 2, figsize=(6.73, 4.9))
    fig.subplots_adjust(wspace=0.3, hspace=0.55, left=0.09, right=0.985, bottom=0.09, top=0.88)

    for data, path in (("v2", "results/l5_mapterm_v2.json"), ("v3", "results/l5_mapterm_v3.json")):
        col = DES[data][1]
        mt = mapterm(path)
        ps = sorted(mt)
        a.plot(ps, [mt[p][1] for p in ps], "o-", color=col, ms=3, lw=1.2)
        a.plot(ps, [mt[p][0] for p in ps], "s--", color=col, ms=2.6, lw=1.0)
        dn = deeponet(data)
        pd = sorted(dn)
        b.plot(pd, [dn[p][0] for p in pd], "o-", color=col, ms=3, lw=1.2)
        b.plot(pd, [dn[p][1] for p in pd], "s--", color=col, ms=2.6, lw=1.0)
        for model, mk, ls, off in (("hgb", "o", "-", -0.07), ("deeponet_own_floor", "s", "--", 0.07)):
            bp = v[data].get(model, {}).get("by_p", {})
            pp = sorted(int(p) for p in bp)
            y = np.array([100 * bp[str(p)]["share_map"] for p in pp])
            lo = np.array([100 * bp[str(p)]["ci"][0] for p in pp])
            hi = np.array([100 * bp[str(p)]["ci"][1] for p in pp])
            c.errorbar(np.array(pp) * 2 ** off, y, yerr=[y - lo, hi - y], fmt=mk + ls, color=col, ms=3,
                       lw=1.0, capsize=1.8, mfc=col if model == "hgb" else "white", mew=1.0)

    for ax in (a, b):
        ax.set_yscale("log"); logx(ax, PS)
        ax.set_xlabel("basis size $p$"); ax.set_ylabel("held-out nRMSE of c")
    a.set_title("A  POD + gradient boosting", loc="left")
    b.set_title("B  DeepONet", loc="left")
    a.set_ylim(top=0.4); a.text(9, 0.13, "map term (solid)", fontsize=7, color="0.3")
    a.text(20, 1.5e-4, "basis floor (dashed)", fontsize=7, color="0.3")
    b.set_ylim(4e-4, 0.12)
    b.text(9, 0.06, "total error (solid)", fontsize=7, color="0.3")
    b.text(24, 5.2e-4, "its own floor (dashed)", fontsize=7, color="0.3")

    logx(c, PS)
    c.set_ylim(90, 100.5)
    c.set_xlabel("basis size $p$"); c.set_ylabel("map share of squared error (%)")
    c.set_title("C  Share of the error carried by the map", loc="left")
    c.legend(handles=[Line2D([], [], color="0.35", marker="o", ls="-", ms=3, label="POD + boosting"),
                      Line2D([], [], color="0.35", marker="s", ls="--", ms=3, mfc="white", label="DeepONet")],
             loc="lower right", fontsize=7, frameon=False)

    n = np.array([r["n_materials"] for r in lc])
    col = DES["v2"][1]
    d.plot(n, [r["modes_r2_gt_0.2"] for r in lc], "o-", color=col, ms=3, lw=1.2)
    d.plot(n, [r["modes_r2_gt_0.5"] for r in lc], "s--", color=col, ms=2.6, lw=1.0)
    d.set_xscale("log"); d.set_xticks(n); d.set_xticklabels([str(int(x)) for x in n])
    d.xaxis.set_minor_formatter(NullFormatter())
    d.set_yticks(range(0, 15, 2))
    d.set_xlabel("training materials"); d.set_ylabel("modes predicted (of 32)")
    d.set_title("D  Modes the map predicts (v2)", loc="left")
    d.text(13, 10.5, "held-out $R^2 > 0.2$", fontsize=7, color="0.3")
    d.text(50, 4.2, "$R^2 > 0.5$", fontsize=7, color="0.3")

    fig.legend(handles=[Line2D([], [], color=DES[k][1], lw=2, label=DES[k][0]) for k in ("v2", "v3")],
               loc="upper center", ncol=2, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 0.995))
    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig_basismap.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig_basismap.png/.pdf")


if __name__ == "__main__":
    main()
