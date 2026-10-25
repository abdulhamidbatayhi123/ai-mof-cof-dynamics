"""Figure: screening and named frameworks, on both isotherm designs (PREREG_DD_ADDITIONS, PREREG_DD_V3).

Every series is read from results files; no model is evaluated here.
  A  Spearman correlation of the half-breakthrough time, per condition (small points), with the
     mean and its cluster-bootstrap interval, for each arm on v2 and v3; dotted: the registered
     threshold. The zero-solve baseline (ranking by stoichiometric time) is marked.
  B  top-10 % recall, same layout.
  C  field error on the six named frameworks, v2 rule; hollow = outside the v2 design space.
     Bars span the three training seeds (results/dd_seed_robustness.json).
  D  the same frameworks inside the v3 design space (all inside).
Dashed lines in C and D: the 95th percentile of each surrogate's per-material held-out error.

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

import dd_screening_frameworks as dd
import figstyle as fs

OUT = "figures"
ARMS = [("don", "DeepONet", "deeponet_p16"), ("hgb", "POD + boosting", "hgb_p16"), ("coarse", "coarse solve", None)]
COL = {"don": fs.ARM_COLOUR["deeponet"], "hgb": fs.ARM_COLOUR["pod_reg"], "coarse": fs.C["dark"]}
FILES = {"v2": ("results/dd_b1_predictions.json", "results/dd_coarse_all.json", "results/dd_additions_verdict.json"),
         "v3": ("results/dd_b1_predictions_v3.json", "results/dd_coarse_all_v3.json",
                "results/dd_additions_verdict_v3.json")}
SHORT = {"Al-fumarate (Basolite A520)": "Al fumarate", "Co2Cl2(BTDD)": "Co$_2$Cl$_2$(BTDD)"}


def per_condition(design):
    b1p, cop, _ = FILES[design]
    b1, co = json.load(open(b1p)), json.load(open(cop))
    rows = []
    for r in b1["folds"].values():
        for i, (m, c) in enumerate(zip(r["material_ids"], r["condition_ids"])):
            cc = co["cells"].get(f"m{m:04d}_c{c:04d}", {}); tf = r["t_final"][i]
            tt = r["t50_true_norm"][i] * tf
            rows.append((c, tt, r["deeponet_p16"]["t50_norm"][i] * tf, r["hgb_p16"]["t50_norm"][i] * tf,
                         cc["t50_norm"] * tf if cc.get("accepted") else tt))
    a = np.array(rows, float)
    out = {k: ([], []) for k, _, _ in ARMS}
    for c in np.unique(a[:, 0]):
        j = a[:, 0] == c
        for k, col in (("don", 2), ("hgb", 3), ("coarse", 4)):
            out[k][0].append(dd.spearman(a[j, 1], a[j, col])); out[k][1].append(dd.topk_recall(a[j, 1], a[j, col]))
    return out


def main():
    fs.apply()
    base = json.load(open("results/dd_v3_verdict.json"))["baseline_tstoich"]
    seeds = json.load(open("results/dd_seed_robustness.json"))["summary"]["b2"]["deeponet_p16"]
    fig, ((a, b), (c, d)) = plt.subplots(2, 2, figsize=(6.73, 5.0))
    fig.subplots_adjust(wspace=0.28, hspace=0.62, left=0.085, right=0.985, bottom=0.14, top=0.86)

    for ax, idx, key, title, thr, bkey in (
            (a, 0, "spearman", "A  Rank agreement", 0.9, "spearman_mean"),
            (b, 1, "top10_recall", "B  Top-10 % recall", 0.8, "top10_recall_mean")):
        for g, design in enumerate(("v2", "v3")):
            v = json.load(open(FILES[design][2]))["b1"]
            pc = per_condition(design)
            for x, (k, lab, _) in enumerate(ARMS):
                xx = g * 4 + x
                vals = pc[k][idx]
                ax.plot(np.full(len(vals), xx) + np.linspace(-0.18, 0.18, len(vals)), vals, "o", ms=1.8,
                        color=COL[k], alpha=0.4, mec="none")
                m = v[k][f"{key}_mean"]; lo, hi = v[k][f"{key}_ci"]
                ax.errorbar([xx], [m], yerr=[[max(m - lo, 0)], [max(hi - m, 0)]], fmt="s", color=COL[k], ms=3.6,
                            capsize=2.5, zorder=3)
            bl = base[design]["t_stoich"][bkey]
            ax.plot([g * 4 - 0.4, g * 4 + 2.4], [bl, bl], color="0.55", lw=0.9, ls="-.")
        ax.axhline(thr, color="0.4", lw=0.8, ls=":")
        ax.set_xticks([1, 5]); ax.set_xticklabels(["smooth (v2)", "MOF-like (v3)"])
        ax.set_xlim(-0.7, 6.7)
        ax.set_title(title, loc="left")
    a.set_ylabel("Spearman, per condition"); b.set_ylabel("recall, per condition")
    a.set_ylim(0.3, 1.02); b.set_ylim(0.0, 1.04)

    for ax, design, title in ((c, "v2", "C  Named frameworks, v2 design"), (d, "v3", "D  Same frameworks, v3 design")):
        vv = json.load(open(FILES[design][2]))["b2"]
        fw = vv["frameworks"]
        names = list(fw)
        for x, nm in enumerate(names):
            rec = fw[nm]; outside = bool(rec["outside_box"])
            for dx, (k, lab, key) in zip((-0.22, 0.0, 0.22), ARMS):
                val = rec.get(key, {}).get("nrmse_c") if key else rec.get("coarse", {}).get("nrmse_c")
                if val is None:
                    continue
                if design == "v2" and k == "don":
                    s = seeds[nm]
                    ax.plot([x + dx] * 2, [s["min"], s["max"]], color=COL[k], lw=1.0, alpha=0.7)
                ax.plot([x + dx], [val], "o", ms=3.8, color=COL[k], **({"mfc": "white", "mew": 1.1} if outside else {}))
        for k, key in (("don", "deeponet_p16"), ("hgb", "hgb_p16")):
            ax.axhline(vv["p95_heldout_material_nrmse"][key], color=COL[k], lw=0.8, ls="--")
        ax.set_yscale("log"); ax.set_ylim(2.5e-3, 0.7)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels([SHORT.get(n, n) for n in names], rotation=35, ha="right")
        ax.set_ylabel("field nRMSE (c)"); ax.set_title(title, loc="left")

    fig.legend(handles=[Line2D([], [], color=COL[k], marker="s", ls="", ms=4, label=lab) for k, lab, _ in ARMS] +
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
