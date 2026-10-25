"""Figure (Digital Discovery revision): screening and named frameworks (PREREG_DD_ADDITIONS).

Every series is read from results files written by dd_screening_frameworks.py; no model is
evaluated here.
  A  rank agreement (Spearman) of the half-breakthrough time, per condition, for each arm,
     with the mean and its cluster-bootstrap interval (results/dd_additions_verdict.json).
  B  top-10 % recall per condition, same layout.
  C  field nRMSE (c) on the six named frameworks, per arm, against the 95th percentile of the
     same arm's per-material held-out errors; frameworks outside the sampled design space are
     drawn hollow.

    python fig_screening.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import dd_screening_frameworks as dd
import figstyle as fs

OUT = "figures"
ARMS = [("don", "DeepONet", "deeponet_p16"), ("hgb", "POD + boosting", "hgb_p16"), ("coarse", "coarse solve", None)]


def per_condition():
    b1 = json.load(open(dd.OUT_B1)); co = json.load(open(dd.OUT_COARSE))
    rows = []
    for f, r in b1["folds"].items():
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
    v = json.load(open(dd.OUT_VERDICT))
    pc = per_condition()
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(6.73, 2.5), gridspec_kw={"width_ratios": [1, 1, 1.35]})
    fig.subplots_adjust(wspace=0.45, bottom=0.27, top=0.86)
    cols = {"don": fs.ARM_COLOUR["deeponet"], "hgb": fs.ARM_COLOUR["pod_reg"], "coarse": fs.C["dark"]}
    for ax, idx, key, title in ((a, 0, "spearman", "A  Rank agreement"), (b, 1, "top10_recall", "B  Top-10 % recall")):
        for x, (k, lab, _) in enumerate(ARMS):
            vals = pc[k][idx]
            ax.plot(np.full(len(vals), x) + np.linspace(-0.15, 0.15, len(vals)), vals, "o", ms=2.2,
                    color=cols[k], alpha=0.45, mec="none")
            m = v["b1"][k][f"{key}_mean"]; lo, hi = v["b1"][k][f"{key}_ci"]
            ax.errorbar([x], [m], yerr=[[max(m - lo, 0.0)], [max(hi - m, 0.0)]], fmt="s", color=cols[k], ms=4, capsize=3, zorder=3)
        ax.set_xticks(range(len(ARMS))); ax.set_xticklabels([l for _, l, _ in ARMS], rotation=25, ha="right")
        ax.set_title(title)
    a.set_ylabel("Spearman, per condition"); b.set_ylabel("recall, per condition")
    a.axhline(0.9, color="0.5", lw=0.8, ls=":"); b.axhline(0.8, color="0.5", lw=0.8, ls=":")

    fw = v.get("b2", {}).get("frameworks", {})
    names = list(fw)
    for x, nm in enumerate(names):
        rec = fw[nm]; outside = bool(rec["outside_box"])
        for dx, (k, lab, key) in zip((-0.2, 0.0, 0.2), ARMS):
            val = rec.get(key, {}).get("nrmse_c") if key else rec.get("coarse", {}).get("nrmse_c")
            if val is None:
                continue
            c.plot([x + dx], [val], "o", ms=4, color=cols[k], **({"mfc": "white", "mew": 1.2} if outside else {}))
    for k, key in (("don", "deeponet_p16"), ("hgb", "hgb_p16")):
        p95 = v.get("b2", {}).get("p95_heldout_material_nrmse", {}).get(key)
        if p95:
            c.axhline(p95, color=cols[k], lw=0.8, ls="--")
    c.set_yscale("log")
    c.set_xticks(range(len(names)))
    c.set_xticklabels([n.split(" (")[0].replace("Co2Cl2(BTDD)", "Co$_2$Cl$_2$(BTDD)") for n in names],
                      rotation=35, ha="right")
    c.set_ylabel("nRMSE (c)"); c.set_title("C  Named frameworks")
    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig_screening.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig_screening.png/.pdf")


if __name__ == "__main__":
    main()
