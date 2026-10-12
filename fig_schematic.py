"""Figure 0: what a surrogate maps, and how a template model builds a field.

Reads results/schematic_sample.json (owner: schematic_sample.py, which picks a real
stored sample by a fixed rule) and, for the second row ("templates versus recipe",
internal referees' clarity item 4), results/schematic_modes.json (owner:
schematic_modes.py: POD templates, and one held-out field rebuilt with true and with
learned weights). Draws nothing it computes: the field and the outlet curve are the
stored solver output; the two front markers are placed at the outlet curve's own
features (the first stored sample above zero, and its steepest rise). Drawn at the
printed width (7.2 in).

    python fig_schematic.py
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

import figstyle as fs

SRC = "results/schematic_sample.json"
MODES = "results/schematic_modes.json"


def field_axes(ax, ylabel=True):
    ax.grid(False)
    ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
    ax.set_xlabel("time $t/t_{final}$")
    if ylabel:
        ax.set_ylabel("position $z/L$")


def main():
    fs.apply()
    d = json.load(open(SRC))
    m = json.load(open(MODES))
    field = np.array(d["c_field"])
    ex = np.array(d["exit_curve"])
    t = np.linspace(0.0, 1.0, ex.size)

    fig = plt.figure(figsize=(7.2, 4.9))
    top = fig.add_gridspec(1, 3, left=0.02, right=0.98, top=0.93, bottom=0.60, wspace=0.62,
                           width_ratios=[1.35, 1.0, 1.0])
    bot = fig.add_gridspec(1, 3, left=0.02, right=0.98, top=0.42, bottom=0.08, wspace=0.42,
                           width_ratios=[1.35, 1.0, 1.0])

    # A: the column and the parameter set
    ax = fig.add_subplot(top[0]); ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.add_patch(Rectangle((2.4, 2.2), 5.0, 1.4, fill=False, lw=1.3))
    for row, y in enumerate(np.linspace(2.4, 3.4, 4)):     # pellets, decoration only
        for x in np.arange(2.65 + 0.2 * (row % 2), 7.25, 0.4):
            ax.add_patch(Circle((x, y), 0.11, color="0.6"))
    ax.add_patch(FancyArrowPatch((0.6, 2.9), (2.3, 2.9), arrowstyle="-|>", mutation_scale=10, lw=1.1))
    ax.add_patch(FancyArrowPatch((7.5, 2.9), (9.3, 2.9), arrowstyle="-|>", mutation_scale=10, lw=1.1))
    ax.text(0.2, 3.75, "humid air\nRH, $v$, $T$", fontsize=7.2, va="bottom")
    ax.text(7.7, 3.75, "outlet\n$c(L,t)$", fontsize=7.2, va="bottom")
    ax.text(4.9, 2.0, "packed bed of adsorbent pellets, length $L$", fontsize=7.2, ha="center", va="top")
    ax.text(4.9, 5.9, "adsorbent: capacity, heat, step humidity,\ncooperativity, low-humidity fraction;\n"
                      "pellet size, density; bed porosity", fontsize=7.2, ha="center", va="top",
            color="0.25")
    ax.text(4.9, 0.9, "surrogate: these 11 numbers $\\rightarrow$ $c$, $q$, $T(z,t)$",
            fontsize=7.2, ha="center", style="italic")
    ax.set_title("A  The column and its parameters")

    # B: the stored concentration field
    ax = fig.add_subplot(top[1])
    im = ax.imshow(field, origin="lower", aspect="auto", extent=(0, 1, 0, 1), cmap="viridis", vmin=0, vmax=1)
    field_axes(ax)
    cb = fig.colorbar(im, ax=ax, fraction=0.06, pad=0.03, ticks=[0, 0.5, 1])
    cb.set_label("$c/c_{in}$", fontsize=7.2); cb.ax.tick_params(labelsize=6.5)
    ax.set_title("B  One stored solver field")

    # C: its outlet curve, with the two fronts marked at the curve's own features
    ax = fig.add_subplot(top[2])
    ax.plot(t, ex, color="k", lw=1.3)
    i_h = int(np.argmax(ex > 0.01))
    i_s = int(np.argmax(np.gradient(ex, t) * (t > t[i_h] + 0.02)))
    ax.annotate("Henry front", (t[i_h], ex[i_h]), (0.16, 0.10), fontsize=7.2,
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.annotate("pore-filling\nfront", (t[i_s], ex[i_s]), (0.40, 0.84), fontsize=7.2, ha="right",
                arrowprops=dict(arrowstyle="->", lw=0.7))
    ax.set_xlabel("time $t/t_{final}$"); ax.set_ylabel("outlet $c/c_{in}$")
    ax.set_xlim(0, 1); ax.set_ylim(-0.02, 1.05)
    ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
    ax.set_title("C  The breakthrough curve")

    # D: three stored templates (POD modes)
    gd = bot[0].subgridspec(1, 3, wspace=0.08)
    for k in range(3):
        ax = fig.add_subplot(gd[k])
        tk = np.array(m["templates"][k]); v = np.abs(tk).max()
        ax.imshow(tk, origin="lower", aspect="auto", extent=(0, 1, 0, 1), cmap="RdBu_r", vmin=-v, vmax=v)
        ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlabel(f"template {k + 1}", fontsize=7.2)
        if k == 0:
            ax.set_title(f"D  Stored templates (3 of {m['P']})")
    fig.text(0.215, 0.015, "field $\\approx$ $\\sum_k$ weight$_k$ $\\times$ template$_k$",
             fontsize=7.2, ha="center", style="italic")

    # E, F: one held-out field rebuilt with perfect and with learned weights
    for slot, key, err, title in (
            (1, "rebuilt_true_weights", m["nrmse_true_weights"], "E  Perfect weights"),
            (2, "rebuilt_learned_weights", m["nrmse_learned_weights"], "F  Learned weights")):
        ax = fig.add_subplot(bot[slot])
        ax.imshow(np.array(m[key]), origin="lower", aspect="auto", extent=(0, 1, 0, 1),
                  cmap="viridis", vmin=0, vmax=1)
        field_axes(ax, ylabel=(slot == 1))
        ax.set_title(title)
        ax.text(0.04, 0.95, f"nRMSE {100 * err:.1f} %", transform=ax.transAxes, fontsize=7.2,
                color="w", va="top")

    fig.savefig("figures/Fig0_schematic.pdf")
    fig.savefig("figures/Fig0_schematic.png")
    print("wrote figures/Fig0_schematic.pdf / .png")


if __name__ == "__main__":
    main()
