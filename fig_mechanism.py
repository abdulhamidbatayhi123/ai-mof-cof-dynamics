"""Figure 5: what binds the error. The learned map, mode by mode, as materials are added.

Every series is read from `results/learning_curve_v2_verdict.json` (full design, five
folds, the learning curve's per-mode gradient-boosting regressors mapping material
parameters to the first 32 POD coefficients of c; not the L1 perceptron, B78). No model is evaluated here. Drawn at the printed width.

  A  held-out R^2 of the parameter-to-coefficient map for each of the first 32 modes,
     one curve per training-set size: the leading modes are learned first, and each
     doubling of the training materials lifts every mode.
  B  the number of modes whose map clears R^2 = 0.2 (and 0.5), against the number of
     training materials: still climbing at the largest size affordable.

The basis-size and decomposition results are in Figure 4 (both designs); this figure
is about the map itself.

    python fig_mechanism.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.ticker import NullFormatter

import figstyle as fs

OUT = "figures"
PENDING_RESULTS = ()


def main():
    fs.apply()
    rows = json.load(open("results/learning_curve_v2_verdict.json"))["axes"]["materials"]["rows"]
    n = np.array([r["n_materials"] for r in rows])

    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.subplots_adjust(wspace=0.32)

    cmap = matplotlib.colormaps["Blues"]
    for i, r in enumerate(rows):
        r2 = np.array(r["mode_r2"])
        k = np.arange(1, len(r2) + 1)
        col = cmap(0.35 + 0.65 * i / (len(rows) - 1))
        a.plot(k, r2, "-o", color=col, ms=2.4, lw=1.1, label=f"{int(r['n_materials'])}")
    a.axhline(0.2, color="0.45", lw=0.8, ls=":")
    a.axhline(0.0, color="k", lw=0.6)
    a.set_xlabel("POD mode index")
    a.set_ylabel("held-out $R^2$ of the learned map")
    a.set_xlim(0.5, len(rows[0]["mode_r2"]) + 0.5)
    a.set_ylim(min(-0.25, min(min(r["mode_r2"]) for r in rows) - 0.05), 1.0)
    a.set_title("A  Each mode, as materials are added")
    a.legend(title="training materials", loc="upper right", ncol=5, fontsize=7.2,
             title_fontsize=7.2, columnspacing=0.8, handlelength=1.4)
    a.text(len(rows[0]["mode_r2"]), 0.215, "$R^2$ = 0.2", ha="right", va="bottom",
           fontsize=7.2, color="0.45")

    m2 = np.array([r["modes_r2_gt_0.2"] for r in rows])
    m5 = np.array([r["modes_r2_gt_0.5"] for r in rows])
    b.plot(n, m2, "o-", color=fs.C["blue"], ms=3.5, label="$R^2$ > 0.2")
    b.plot(n, m5, "s--", color=fs.C["dark"], ms=3, lw=1.1, label="$R^2$ > 0.5")
    b.set_xscale("log")
    b.set_xticks(n); b.set_xticklabels([str(int(v)) for v in n])
    b.xaxis.set_minor_formatter(NullFormatter())
    b.set_xlabel("training materials $N_{mat}$")
    b.set_ylabel(f"modes above threshold (of {len(rows[0]['mode_r2'])})")
    b.set_ylim(0, max(m2) + 2)
    b.set_title("B  Predictable modes keep growing")
    b.legend(loc="upper left")

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig5_mechanism.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig5_mechanism.png/.pdf  (modes > 0.2: {list(m2)}; > 0.5: {list(m5)})")


if __name__ == "__main__":
    main()
