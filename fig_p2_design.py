"""Paper 2, Stage 1, Figure 1: the study design (schematic, no results).

(a) The column and the three observation models (O1, O2: 20 interior probes; O3: outlet).
(b) What H2b compares, drawn with ILLUSTRATIVE logistic curves (not data): the probability
    of discovering the law and of identifying k, both against log10 Da, their 50 %
    crossings, and the three pre-declared verdicts set by the gap between them.

    python fig_p2_design.py  -> paper2/fig_design.pdf (+ .png for review)
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

import figstyle

figstyle.apply()
C = figstyle.C
OUT = "paper2/fig_design"

fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.15, 1.0]})

# (a) column schematic -------------------------------------------------------------------
a.set_xlim(0, 10)
a.set_ylim(0, 6)
a.axis("off")
a.add_patch(Rectangle((1.6, 2.2), 6.4, 1.6, facecolor="#f2efe8", edgecolor=C["dark"], lw=1.0))
for x in np.linspace(1.9, 7.7, 20):                        # 20 interior probes
    a.plot([x, x], [3.8, 4.25], color=C["blue"], lw=0.9)
    a.plot(x, 4.32, "o", ms=2.6, color=C["blue"])
a.add_artist(FancyArrowPatch((0.2, 3.0), (1.55, 3.0), arrowstyle="-|>", mutation_scale=10, color=C["dark"]))
a.text(0.2, 3.35, "feed\n$c_{in}$, $T_{in}$", fontsize=8, va="bottom")
a.add_artist(FancyArrowPatch((8.05, 3.0), (9.4, 3.0), arrowstyle="-|>", mutation_scale=10, color=C["dark"]))
a.plot(8.7, 3.0, "s", ms=5, color=C["orange"])
a.text(4.8, 3.0, r"$\partial q/\partial t = k\,(q^{*}(c,T) - q)$", ha="center", va="center", fontsize=8.5)
a.text(4.8, 4.75, "20 interior probes", ha="center", fontsize=8, color=C["blue"])
a.text(4.8, 1.55, "O1: $c$, $q$, $T$ at the probes (ceiling)\n"
                  "O2: $c$, $T$ at the probes ($q$ reconstructed)\n"
                  "O3: outlet $c(t)$, $T(t)$ only (realistic)",
       ha="center", va="top", fontsize=7.8, linespacing=1.35)
a.text(8.7, 3.45, "O3", ha="center", fontsize=8, color=C["orange"])
a.set_title("a  Column and what is observed", loc="left")

# (b) illustrative H2b curves ------------------------------------------------------------
x = np.linspace(-1, 3, 400)
pd_ = 1 / (1 + np.exp(3 * (x - 1.0)))
pi_ = 1 / (1 + np.exp(3 * (x - 1.8)))
b.plot(x, pd_, color=C["blue"], lw=2)
b.plot(x, pi_, color=C["orange"], lw=2, ls="--")
b.axhline(0.5, color=C["grey"], lw=0.8)
for xc, col in ((1.0, C["blue"]), (1.8, C["orange"])):
    b.plot([xc, xc], [0, 0.5], color=col, lw=0.9, ls=":")
b.annotate("", xy=(1.8, 0.08), xytext=(1.0, 0.08),
           arrowprops=dict(arrowstyle="<->", color=C["dark"], lw=0.9))
b.text(1.4, 0.11, "gap", ha="center", fontsize=8)
b.text(-0.85, 0.80, "discovering the law", color=C["blue"], fontsize=8)
b.text(1.95, 0.62, "identifying $k$", color=C["orange"], fontsize=8)
b.text(0.60, 0.53, r"$Da^{*}_{disc}$", ha="right", fontsize=8, color=C["blue"])
b.text(1.85, 0.53, r"$Da^{*}_{ident}$", ha="left", fontsize=8, color=C["orange"])
b.set_xlabel(r"$\log_{10}$ Damköhler number")
b.set_ylabel("probability")
b.set_ylim(-0.02, 1.02)
b.set_xlim(-1, 3)
b.grid(False)
b.text(-0.92, 0.45, "gap $\\leq -0.25$: fails before\n|gap| $< 0.25$: fails with\n"
                  "gap $\\geq +0.25$: outlives\n(decade; illustrative curves)",
       ha="left", va="top", fontsize=6.9, linespacing=1.3, color=C["dark"])
b.set_title("b  What H2b compares", loc="left")

fig.tight_layout(w_pad=1.5)
fig.savefig(OUT + ".pdf")
fig.savefig(OUT + ".png", dpi=200)
print("wrote", OUT + ".pdf")
