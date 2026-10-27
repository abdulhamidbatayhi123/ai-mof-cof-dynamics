"""Figure 1: the study at a glance, and its central question on one real held-out field.

  A  the workflow: two pre-registered designs -> verified reference solver -> breakthrough
     fields -> five folds by material -> reduced-basis surrogates -> the questions the
     Results answer, each with its section. Counts are read from results/dataset_summary.json
     and results/dataset_summary_v3.json, never typed.
  B-E one held-out field of the MOF-like design rebuilt by POD with 16 modes: the field, three
     basis modes, the rebuild with the best coefficients (the basis floor) and with the
     coefficients gradient boosting predicts from the material's parameters (floor + map
     error). Read from results/workflow_example_v3.json (owner: workflow_example.py).

Drawn at the printed width, 17.1 cm.

    python fig_workflow.py   -> figures/Fig_workflow.pdf / .png
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import figstyle as fs

W = 17.1 / 2.54
FS = 7.6           # body text at print size
GREY, INK = "0.45", "0.12"
MAP_C, FLOOR_C = fs.C["red"], fs.C["dark"]


def box(ax, x, y, w, h, title, body, fc="white", ec="0.55", tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.018",
                                fc=fc, ec=ec, lw=0.8, transform=ax.transAxes))
    ax.text(x + w / 2, y + h - 0.035, title, ha="center", va="top", fontsize=FS, weight="bold",
            color=tc, transform=ax.transAxes)
    ax.text(x + w / 2, y + h - 0.125, body, ha="center", va="top", fontsize=FS - 0.6, color=INK,
            linespacing=1.25, transform=ax.transAxes)


def arrow(ax, p0, p1, colour="0.35", lw=1.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=8, lw=lw, color=colour,
                                 transform=ax.transAxes, shrinkA=0, shrinkB=0))


def field_ax(ax, a, cmap="viridis", sym=False):
    a = np.asarray(a)
    v = np.abs(a).max() if sym else 1.0
    ax.imshow(a, origin="lower", aspect="auto", extent=(0, 1, 0, 1), cmap=cmap,
              vmin=-v if sym else 0.0, vmax=v)
    ax.grid(False)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_linewidth(0.6); s.set_color("0.4")


def main():
    fs.apply()
    v2 = json.load(open("results/dataset_summary.json"))
    v3 = json.load(open("results/dataset_summary_v3.json"))
    ex = json.load(open("results/workflow_example_v3.json"))

    fig = plt.figure(figsize=(W, 4.55))
    a = fig.add_axes([0.0, 0.47, 1.0, 0.53]); a.axis("off")
    a.text(0.005, 0.985, "A", fontsize=10, weight="bold", va="top", transform=a.transAxes)

    # top row: how the data and the surrogates are made
    y, h, w = 0.60, 0.36, 0.178
    xs = [0.03, 0.225, 0.42, 0.615, 0.81]
    box(a, xs[0], y, w, h, "Two designs",
        f"smooth isotherms:\n{v2['n_materials']} materials\nMOF-like isotherms:\n"
        f"{v3['n_materials']} materials\n× {v2['n_conditions']} conditions")
    box(a, xs[1], y, w, h, "Reference solver",
        "1-D packed bed,\nnon-isothermal, LDF\nverified on closed\nforms; checked on\na MOF-303 bed")
    box(a, xs[2], y, w, h, "Fields",
        f"breakthrough fields\nc(z, t), 128 × 128\n{v2['n_samples']} + {v3['n_samples']}\naccepted runs")
    box(a, xs[3], y, w, h, "Five folds",
        "split by material:\nevery material\nheld out once")
    box(a, xs[4], y, w, h, "Surrogates",
        "field ≈ Σ coefficient\n× basis mode\nPOD + boosting,\nDeepONet")
    for i in range(4):
        arrow(a, (xs[i] + w + 0.004, y + h / 2), (xs[i + 1] - 0.004, y + h / 2))

    # bottom row: what the Results ask, each pre-registered
    qy, qh, qw = 0.02, 0.36, 0.178
    qs = [("Seven explanations", "more data, capacity,\nphysics loss, operator,\n... (Section 3.1)"),
          ("Basis or map?", "basis floor against\ncoefficient-map error\n(Section 3.2)"),
          ("Worth building?", "accuracy and cost\nagainst a coarse solve\n(Section 3.3)"),
          ("Does it rank?", "Spearman and top-10 %\nrecall per condition\n(Section 3.4)"),
          ("Real frameworks?", "six published water-\nharvesting MOFs\n(Section 3.5)")]
    for x, (t, b) in zip(xs, qs):
        box(a, x, qy, qw, qh, t, b, fc="#f4f6f9", ec="0.7")
    bus = (y + qy + qh) / 2
    a.plot([xs[4] + w / 2, xs[4] + w / 2], [y, bus], color="0.35", lw=1.0, transform=a.transAxes)
    a.plot([xs[0] + qw / 2, xs[4] + qw / 2], [bus, bus], color="0.35", lw=1.0, transform=a.transAxes)
    for x in xs:
        arrow(a, (x + qw / 2, bus), (x + qw / 2, qy + qh + 0.004))

    # B-E: the central question on one real held-out field
    gy, gh = 0.085, 0.30
    cols = [0.035, 0.27, 0.53, 0.765]
    gw = 0.205
    b = fig.add_axes([cols[0], gy, gw, gh]); field_ax(b, ex["field"])
    b.set_title("B  held-out field", fontsize=FS + 0.4, loc="left")
    b.set_xlabel("time t/t$_\\mathrm{final}$", fontsize=FS); b.set_ylabel("position z/L", fontsize=FS)
    b.text(1.06, 0.5, "≈", fontsize=14, ha="center", va="center", transform=b.transAxes)

    sub = cols[1]
    sw = (gw - 0.02) / 3
    for k in range(3):
        m = fig.add_axes([sub + k * (sw + 0.01), gy, sw, gh])
        field_ax(m, ex["modes"][k], cmap="RdBu_r", sym=True)
        m.set_xlabel(f"mode {k + 1}", fontsize=FS - 0.4)
        if k == 0:
            m.set_title(f"C  basis modes (3 of {ex['P']})", fontsize=FS + 0.4, loc="left")

    for col, key, err, title, colour in (
            (cols[2], "rebuilt_best", ex["nrmse_best"], "D  best coefficients", FLOOR_C),
            (cols[3], "rebuilt_predicted", ex["nrmse_predicted"], "E  predicted coefficients", MAP_C)):
        e = fig.add_axes([col, gy, gw, gh]); field_ax(e, ex[key])
        e.set_title(title, fontsize=FS + 0.4, loc="left")
        e.text(0.05, 0.92, f"nRMSE {100 * err:.1f} %", fontsize=FS, color="white", va="top",
               transform=e.transAxes, weight="bold")
        e.set_xlabel("basis floor" if key == "rebuilt_best" else "basis floor + map error",
                     fontsize=FS, color=colour)
    fig.text(0.5, 0.005, f"MOF-like design, POD with {ex['P']} modes; median held-out sample of its fold "
                         f"(fold means {100 * ex['fold_mean_nrmse_best']:.1f} % and "
                         f"{100 * ex['fold_mean_nrmse_predicted']:.1f} %)",
             ha="center", fontsize=FS - 0.6, color=GREY)

    fig.savefig("figures/Fig_workflow.pdf")
    fig.savefig("figures/Fig_workflow.png", dpi=300)
    plt.close(fig)
    print("wrote figures/Fig_workflow.pdf / .png")


if __name__ == "__main__":
    main()
