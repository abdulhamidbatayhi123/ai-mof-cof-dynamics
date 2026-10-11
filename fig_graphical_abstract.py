"""Graphical abstract for the CMAME submission.

The journal's guide (read 2026-10-11) asks for an image of at least 531 x 1328 pixels
(h x w), readable at 5 x 13 cm, as TIFF, EPS or PDF. This draws it at exactly
13 x 5 cm, so every font size below is the printed size.

Three parts, left to right: the question; the seven pre-registered candidates with the
verdict each received; and the measurement behind the main conclusion (the basis floor
falls with basis size while the learned map's error does not move). Every number is
read from paper/numbers.json (written by paper/numbers.py from the results files) or
from the results file itself; none is typed here.

    python fig_graphical_abstract.py   -> figures/graphical_abstract.{pdf,png,tiff}
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import figstyle as fs

CM = 1 / 2.54
N = json.load(open("paper/numbers.json", encoding="utf-8"))["values"]
B = json.load(open("results/l5_bottleneck_v2.json", encoding="utf-8"))

# One line per rung: what was proposed, what it received. The verdict words are the
# paper's own (Figure 1, Section 6); the numbers are macros' values.
LADDER = [
    ("L1", "more materials", True, f"still helps (error ∝ $N^{{-{N['LCbeta']}}}$)"),
    ("L2", "more capacity", True, "not eliminated"),
    ("L3", "KAN basis", False, "eliminated"),
    ("L4", "physics as a loss", True, f"helps {N['LfourbMatGainPct']} %, small weight"),
    ("L5", "bigger basis", True, f"helps {N['LfiveVtwoGainPct']} %, early"),
    ("L6", "separate kinetics", False, "no Damköhler effect"),
    ("L7", "closed form", False, f"eliminated, {N['BfitRatio']}× worse"),
]


def main():
    fs.apply()
    plt.rcParams.update({"font.size": 6.4, "axes.labelsize": 6.2, "xtick.labelsize": 5.6,
                         "ytick.labelsize": 5.6, "legend.fontsize": 5.6})
    fig = plt.figure(figsize=(13 * CM, 5 * CM))

    # ---- left: the question
    q = fig.add_axes([0.0, 0.0, 0.25, 1.0]); q.axis("off")
    q.text(0.06, 0.90, "What limits\nmachine-learning\nsurrogates on\nunseen MOFs?",
           fontsize=8.0, fontweight="bold", va="top", color=fs.C["dark"], linespacing=1.15)
    steps = ["isotherm and pellet\nparameters", "surrogate", "breakthrough\nfield"]
    ys = [0.42, 0.27, 0.12]
    for y, s in zip(ys, steps):
        q.text(0.45, y, s, ha="center", va="center", fontsize=5.8, linespacing=1.05,
               bbox=dict(boxstyle="round,pad=0.35", fc="#eef3f8", ec=fs.C["blue"], lw=0.6))
    for y0, y1 in zip(ys[:-1], ys[1:]):
        q.annotate("", xy=(0.45, y1 + 0.05), xytext=(0.45, y0 - 0.06),
                   arrowprops=dict(arrowstyle="-|>", lw=0.7, color=fs.C["dark"], mutation_scale=6))

    # ---- middle: the ladder
    m = fig.add_axes([0.24, 0.0, 0.44, 1.0]); m.axis("off")
    m.text(0.02, 0.93, "Seven explanations, named in advance", fontsize=6.9, fontweight="bold",
           color=fs.C["dark"], va="top")
    m.text(0.02, 0.835, f"tested on {N['NclustFolds']} held-out materials", fontsize=5.8,
           color="0.35", va="top")
    for i, (rung, hyp, kept, verdict) in enumerate(LADDER):
        y = 0.70 - i * 0.098
        col = fs.C["green"] if kept else fs.C["grey"]
        m.text(0.02, y, "✓" if kept else "✗", color=col, fontsize=7.2, fontweight="bold", va="center")
        m.text(0.085, y, rung, color="0.45", fontsize=5.6, va="center")
        m.text(0.15, y, hyp, color=fs.C["dark"], fontsize=6.0, va="center")
        m.text(0.50, y, verdict, color=col, fontsize=5.6, va="center", ha="left")

    # ---- right: what binds
    ps = [int(p) for p in sorted(B["summary"], key=int)]
    floor = [B["summary"][str(p)]["basis_floor"] for p in ps]
    coef = [B["summary"][str(p)]["coef_pred"] for p in ps]
    a = fig.add_axes([0.77, 0.21, 0.21, 0.52])
    a.plot(ps, coef, "o-", color=fs.C["blue"], ms=2.6, lw=1.3, label="learned map's error")
    a.plot(ps, floor, "s--", color=fs.C["grey"], ms=2.4, lw=1.0, label="basis floor")
    a.set_xscale("log", base=2); a.set_yscale("log")
    a.set_xticks(ps); a.set_xticklabels([str(p) for p in ps])
    a.set_xlabel("basis size $p$"); a.set_ylabel("held-out error")
    a.minorticks_off()
    # direct labels: a legend box would cross the falling floor line
    a.text(ps[-1], coef[-1] * 0.55, "learned map's error", color=fs.C["blue"], fontsize=5.6, ha="right", va="top")
    a.text(ps[2] * 1.15, floor[2] * 2.2, "basis floor", color="0.4", fontsize=5.6, ha="left", va="bottom")
    fig.text(0.70, 0.93, "The map binds, not the basis", fontsize=6.5, fontweight="bold",
             color=fs.C["dark"], va="top")
    fig.text(0.70, 0.835, f"basis {N['LfiveVtwoFloorDrop']}× better, error moves "
             f"{N['LfiveVtwoCoefChangePct']} %", fontsize=5.8, color="0.35", va="top")

    box = matplotlib.transforms.Bbox([[0, 0], [13 * CM, 5 * CM]])
    for ext in ("pdf", "png", "tiff"):
        kw = {"pil_kwargs": {"compression": "tiff_lzw"}} if ext == "tiff" else {}
        fig.savefig(f"figures/graphical_abstract.{ext}", dpi=600, bbox_inches=box, **kw)
    print("wrote figures/graphical_abstract.{pdf,png,tiff} at 13 x 5 cm, 600 dpi")


if __name__ == "__main__":
    main()
