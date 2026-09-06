"""Figure: the two-wave warp — n-width per frame, and the powered verdict.

Every series is read from `results/comoving.json`, `results/comoving2.json` and
`results/warp_verdict.json`. Legacy dataset, 128x128 c-channel, 12 held-out
materials. Nothing is fitted or synthesised here.

  A  modes needed for 99.9 % of training variance, per frame: original, single-front
     alignment at three levels, two-wave alignment at two level pairs (the 0.20–0.80
     pair is excluded by its interpolation floor and drawn hatched).
  B  the verdict, 3 seeds, paired cluster bootstrap: fixed frame, two-wave with the
     PREDICTED warp (the honest arm: no difference), two-wave with the ORACLE warp
     (an upper bound that leaks the answer; drawn hollow).

    python fig_warp.py
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
    c1 = json.load(open("results/comoving.json"))
    c2 = json.load(open("results/comoving2.json"))
    v = json.load(open("results/warp_verdict.json"))

    frames = [("original", c1["spectrum_original"]["0.999"], "0.35", False)]
    for lev in ("0.1", "0.5", "0.9"):
        frames.append((f"single, L = {lev}", c1["levels_detail"][lev]["spectrum"]["0.999"], "#b5423f", False))
    for pair in ("0.10-0.90", "0.05-0.95", "0.20-0.80"):
        d = c2["pairs_detail"][pair]
        frames.append((f"two-wave, {pair}", d["spectrum"]["0.999"], "#3b6ea5", d["contaminated"]))

    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 3.6), gridspec_kw={"width_ratios": [1.35, 1]})
    fig.subplots_adjust(wspace=0.35)

    x = np.arange(len(frames))
    for i, (name, n, col, bad) in enumerate(frames):
        a.bar(i, n, color=col if not bad else "white", edgecolor=col, hatch="//" if bad else None, width=0.7)
        a.text(i, n + 2, str(n) + ("\nexcluded" if bad else ""), ha="center", fontsize=7)
    a.set_xticks(x); a.set_xticklabels([f[0] for f in frames], rotation=30, ha="right", fontsize=7.5)
    a.set_ylabel("POD modes for 99.9 % of training variance")
    a.set_title("A. one shift inflates the n-width; two shifts collapse it")
    a.set_ylim(0, max(f[1] for f in frames) * 1.18)
    gap = c1["two_wave_gap"]
    a.text(0.02, 0.95, f"outlet separation of the two waves:\n{gap['min']:.3f}–{gap['max']:.3f} of the run ({gap['max'] / gap['min']:.0f}×)",
           transform=a.transAxes, va="top", fontsize=7, color="0.3")

    arms = [("fixed frame", "fixed", "#3b6ea5", True), ("two-wave,\npredicted warp", "two_wave", "#e08b3a", True),
            ("two-wave,\noracle warp", "two_wave_oracle", "#6a994e", False)]
    for i, (name, key, col, filled) in enumerate(arms):
        mean, sd = v["means"][key], v["sds"][key]
        b.bar(i, mean, yerr=sd, capsize=4, width=0.6, color=col if filled else "white", edgecolor=col, lw=1.5)
        b.text(i, mean + sd + 0.002, f"{mean:.4f}", ha="center", fontsize=7.5)
    b.set_xticks(range(3)); b.set_xticklabels([a_[0] for a_ in arms], fontsize=8)
    b.set_ylabel("held-out nRMSE (c), 3 seeds")
    r1, r2 = v["fixed_vs_two_wave"], v["fixed_vs_oracle"]
    b.set_title("B. the gain is entirely front-location error")
    b.text(0.5, 0.97,
           f"fixed vs predicted: diff {r1['mean_diff']:+.4f}, CI [{r1['ci_low']:+.4f}, {r1['ci_high']:+.4f}] — no difference\n"
           f"fixed vs oracle: diff {r2['mean_diff']:+.4f}, CI [{r2['ci_low']:+.4f}, {r2['ci_high']:+.4f}] — significant\n"
           f"headroom {v['headroom_to_oracle']:.2f}×; the oracle is handed the true fronts and is an upper bound, not a result",
           transform=b.transAxes, ha="center", va="top", fontsize=6.6, color="0.25")
    b.set_ylim(0, v["means"]["fixed"] * 1.9)

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig6_warp.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}/Fig6_warp.png/.pdf")


if __name__ == "__main__":
    main()
