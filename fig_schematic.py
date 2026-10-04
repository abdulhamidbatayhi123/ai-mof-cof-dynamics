"""Figure 0 -- what a surrogate maps (referee minor 15: a schematic for non-specialists).

Reads results/schematic_sample.json (owner: schematic_sample.py, which picks a real
stored sample by a fixed rule). Draws nothing it computes: the field and the outlet
curve are the stored solver output; the two front markers are placed at the outlet
curve's own features (the first stored sample above zero, and its steepest rise).

    python fig_schematic.py
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

SRC = "results/schematic_sample.json"


def main():
    d = json.load(open(SRC))
    field = np.array(d["c_field"])
    ex = np.array(d["exit_curve"])
    t = np.linspace(0.0, 1.0, ex.size)

    fig = plt.figure(figsize=(12.5, 3.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 1.0], wspace=0.55)

    # A: the column and the parameter set
    ax = fig.add_subplot(gs[0]); ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.add_patch(Rectangle((2.2, 2.0), 5.2, 1.6, fill=False, lw=1.6))
    for row, y in enumerate(np.linspace(2.2, 3.4, 5)):   # pellets: a staggered lattice, decoration only
        for x in np.arange(2.45 + 0.17 * (row % 2), 7.25, 0.34):
            ax.add_patch(Circle((x, y), 0.09, color="0.55"))
    ax.add_patch(FancyArrowPatch((0.5, 2.8), (2.1, 2.8), arrowstyle="-|>", mutation_scale=14, lw=1.4))
    ax.add_patch(FancyArrowPatch((7.5, 2.8), (9.3, 2.8), arrowstyle="-|>", mutation_scale=14, lw=1.4))
    ax.text(0.2, 3.25, "humid feed\nRH, v, T", fontsize=8.5, va="bottom")
    ax.text(7.7, 3.25, "outlet\nc(L, t)", fontsize=8.5, va="bottom")
    ax.text(4.8, 1.55, "packed bed of MOF pellets, length L", fontsize=8.5, ha="center", va="top")
    ax.text(4.8, 5.6, "adsorbent: capacity, heat of adsorption,\nstep humidity, cooperativity, Henry fraction,\n"
            "pellet size and density, bed porosity", fontsize=8, ha="center", va="top")
    ax.text(4.8, 0.55, "surrogate: these 11 numbers  →  the fields c, q, T(z, t)",
            fontsize=8.5, ha="center", style="italic")
    ax.set_title("A   the column and its parameters", fontsize=9.5, loc="left")

    # B: the stored concentration field
    ax = fig.add_subplot(gs[1])
    im = ax.imshow(field, origin="lower", aspect="auto", extent=(0, 1, 0, 1), cmap="viridis", vmin=0, vmax=1)
    ax.set_xlabel("time  t / t$_{final}$", fontsize=8.5); ax.set_ylabel("position  z / L", fontsize=8.5)
    ax.tick_params(labelsize=7.5)
    cb = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.02); cb.set_label("c / c$_{in}$", fontsize=8); cb.ax.tick_params(labelsize=7)
    ax.set_title("B   one stored solver field", fontsize=9.5, loc="left")

    # C: its outlet curve, with the two fronts marked at the curve's own features
    ax = fig.add_subplot(gs[2])
    ax.plot(t, ex, color="k", lw=1.6)
    i_h = int(np.argmax(ex > 0.01))
    i_s = int(np.argmax(np.gradient(ex, t) * (t > t[i_h] + 0.02)))
    ax.annotate("Henry front", (t[i_h], ex[i_h]), (0.10, 0.12), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.annotate("cooperative\npore-filling front", (t[i_s], ex[i_s]), (0.35, 0.86), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_xlabel("time  t / t$_{final}$", fontsize=8.5); ax.set_ylabel("outlet  c / c$_{in}$", fontsize=8.5)
    ax.set_xlim(0, 1); ax.set_ylim(-0.02, 1.05); ax.tick_params(labelsize=7.5)
    ax.set_title("C   the breakthrough curve", fontsize=9.5, loc="left")

    fig.savefig("figures/Fig0_schematic.pdf", bbox_inches="tight")
    fig.savefig("figures/Fig0_schematic.png", dpi=200, bbox_inches="tight")
    print("wrote figures/Fig0_schematic.pdf / .png")


if __name__ == "__main__":
    main()
