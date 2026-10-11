"""Figure 6: the two-wave coordinate change. Modes per frame, and the verdict.

Every series is read from `results/comoving.json`, `results/comoving2.json` and
`results/warp_verdict.json`. Legacy dataset, 128x128 c-channel, 12 held-out
materials. Nothing is fitted or synthesised here. Drawn at the printed width.

  A  modes needed for 99.9 % of training variance, per frame: original, single-front
     alignment at three levels, two-wave alignment at three level pairs (the 0.20-0.80
     pair is excluded by its interpolation floor and drawn hatched).
  B  the verdict, 3 seeds, paired cluster bootstrap: fixed frame, two-wave with the
     PREDICTED warp (no difference), two-wave with the ORACLE warp (an upper bound
     that is handed the true fronts; drawn hollow). The headroom quoted is the fixed
     frame over the oracle, the quantity the text uses.

    python fig_warp.py
"""
from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import figstyle as fs

OUT = "figures"


def bracket(ax, x0, x1, y, text, col="0.25"):
    ax.plot([x0, x0, x1, x1], [y * 0.97, y, y, y * 0.97], color=col, lw=0.8)
    ax.text((x0 + x1) / 2, y * 1.02, text, ha="center", va="bottom", fontsize=6.6, color=col)


def main():
    fs.apply()
    c1 = json.load(open("results/comoving.json"))
    c2 = json.load(open("results/comoving2.json"))
    v = json.load(open("results/warp_verdict.json"))

    frames = [("original", c1["spectrum_original"]["0.999"], fs.C["dark"], False)]
    for lev in ("0.1", "0.5", "0.9"):
        frames.append((lev, c1["levels_detail"][lev]["spectrum"]["0.999"], fs.C["red"], False))
    for pair in ("0.10-0.90", "0.05-0.95", "0.20-0.80"):
        d = c2["pairs_detail"][pair]
        lo, hi = pair.split("-")
        frames.append((f"{lo}/\n{hi}", d["spectrum"]["0.999"], fs.C["blue"], d["contaminated"]))

    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.55, 1]})
    fig.subplots_adjust(wspace=0.32)

    x = np.arange(len(frames))
    for i, (name, n, col, bad) in enumerate(frames):
        a.bar(i, n, color=col if not bad else "white", edgecolor=col, hatch="///" if bad else None,
              width=0.68, lw=1.0)
        a.text(i, n + 2, str(n) + ("\nexcluded" if bad else ""), ha="center", va="bottom", fontsize=6.6)
    a.set_xticks(x); a.set_xticklabels([f[0] for f in frames], fontsize=6.6)
    for xc, lab in ((2, "one front aligned"), (5, "two fronts aligned")):
        a.annotate(lab, (xc, 0), xycoords=("data", "axes fraction"), xytext=(0, -26),
                   textcoords="offset points", ha="center", va="top", fontsize=6.8, color="0.25")
    a.set_ylabel("POD modes for 99.9 % of variance")
    a.set_title("A  One shift inflates the mode count; two collapse it")
    a.set_ylim(0, max(f[1] for f in frames) * 1.22)
    gap = c1["two_wave_gap"]
    a.text(0.98, 0.97, f"the two fronts reach the outlet\n{gap['min']:.3f} to {gap['max']:.3f} of the run apart",
           transform=a.transAxes, va="top", ha="right", fontsize=6.4, color="0.3")

    arms = [("fixed\nframe", "fixed", fs.C["blue"], True),
            ("two fronts,\npredicted", "two_wave", fs.C["orange"], True),
            ("two fronts,\noracle", "two_wave_oracle", fs.C["green"], False)]
    for i, (name, key, col, filled) in enumerate(arms):
        mean, sd = v["means"][key], v["sds"][key]
        b.bar(i, mean, yerr=sd, capsize=3, width=0.6, color=col if filled else "white", edgecolor=col, lw=1.3)
        b.text(i, mean + sd + 0.0012, f"{mean:.4f}", ha="center", va="bottom", fontsize=6.6)
    b.set_xticks(range(3)); b.set_xticklabels([a_[0] for a_ in arms])
    b.set_ylabel("held-out nRMSE (c)")
    b.set_title("B  Predicted fronts: no detectable gain")
    top = v["means"]["fixed"]
    bracket(b, 0, 1, top * 1.22, "no difference")
    headroom = v["means"]["fixed"] / v["means"]["two_wave_oracle"]
    bracket(b, 0, 2, top * 1.48, f"{headroom:.2f}× with true fronts (upper bound)")
    b.set_ylim(0, top * 1.78)

    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/Fig6_warp.{ext}")
    plt.close(fig)
    print(f"wrote {OUT}/Fig6_warp.png/.pdf  (headroom fixed/oracle {headroom:.2f}x)")


if __name__ == "__main__":
    main()
