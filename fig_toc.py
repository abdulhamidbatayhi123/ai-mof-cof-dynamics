"""Table-of-contents graphic for Digital Discovery (8 cm x 4 cm), read from results files.

  left   results/l5_mapterm_v2.json: basis floor against map error, against basis size p
  right  results/dd_additions_verdict.json: held-out field error of the best surrogate and
         of the coarse solve, over all samples

    python fig_toc.py   -> figures/TOC.png (600 dpi) and figures/TOC.pdf
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

import figstyle as fs

CM = 1 / 2.54


def main():
    fs.apply()
    mt = json.load(open("results/l5_mapterm_v2.json"))["summary"]
    v = json.load(open("results/dd_additions_verdict.json"))["b1"]
    ps = sorted(int(p) for p in mt)

    fig, (a, b) = plt.subplots(1, 2, figsize=(8 * CM, 4 * CM), gridspec_kw={"width_ratios": [1.35, 1]})
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.2, top=0.84, wspace=0.55)

    a.plot(ps, [mt[str(p)]["map_hgb"] for p in ps], "o-", color=fs.C["blue"], ms=2.4, lw=1.2)
    a.plot(ps, [mt[str(p)]["floor"] for p in ps], "s--", color=fs.C["dark"], ms=2.2, lw=1.0)
    a.set_yscale("log"); a.set_xscale("log", base=2)
    a.set_xticks(ps); a.set_xticklabels([str(p) for p in ps]); a.xaxis.set_minor_formatter(NullFormatter())
    a.set_ylim(top=0.09); a.text(8.5, 0.013, "map error", color=fs.C["blue"], fontsize=6)
    a.text(20, 1.2e-4, "basis error", color=fs.C["dark"], fontsize=6)
    a.set_xlabel("basis size", fontsize=6, labelpad=1); a.set_ylabel("error", fontsize=6, labelpad=1)
    a.set_title("The map, not the basis", fontsize=6.5, pad=3)
    a.tick_params(labelsize=5, length=2, pad=1)

    vals = [100 * v["don"]["field_nrmse_mean"], 100 * v["coarse"]["field_nrmse_mean"]]
    b.bar([0, 1], vals, width=0.6, color=[fs.ARM_COLOUR["deeponet"], fs.C["dark"]])
    b.set_xticks([0, 1]); b.set_xticklabels(["best\nsurrogate", "coarse\nsolve"], fontsize=5.5)
    b.set_ylabel("held-out error (%)", fontsize=6, labelpad=1)
    b.set_title("A coarse solve wins", fontsize=6.5, pad=3)
    b.tick_params(labelsize=5, length=2, pad=1)

    os.makedirs("figures", exist_ok=True)
    fig.savefig("figures/TOC.png", dpi=600)
    fig.savefig("figures/TOC.pdf")
    plt.close(fig)
    print("wrote figures/TOC.png/.pdf (8 x 4 cm)")


if __name__ == "__main__":
    main()
