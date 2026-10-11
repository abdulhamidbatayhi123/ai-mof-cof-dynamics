"""Figure S2: real water-harvesting MOFs against the sampled design space (referee M10).

Reads results/water_mofs.json (owner: water_mofs.py, from the sourced literature
values in research/water_mof_parameters.json). Each MOF is drawn as the SPAN of its
reported values across sources (a bar from min to max on each axis, a point if one
source) and labelled directly; the shaded boxes are the design's sampled ranges.
Capacity is shown in mol/kg with g/g on the right axis (x 0.018015 kg/mol, the molar
mass of water); step position in % relative humidity. Drawn at the printed width.

    python fig_water_mofs.py
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import figstyle as fs

SRC = "results/water_mofs.json"
M_WATER = 0.018015          # kg/mol
COL = {"MOF-303": fs.C["blue"], "MOF-801": fs.C["orange"], "CAU-10-H": fs.C["green"],
       "Al-fumarate": fs.C["red"], "MIL-160(Al)": fs.C["purple"], "Co2Cl2(BTDD)": fs.C["teal"]}
MARK = {"MOF-303": "o", "MOF-801": "s", "CAU-10-H": "D", "Al-fumarate": "^", "MIL-160(Al)": "v",
        "Co2Cl2(BTDD)": "P"}
# label offsets in points, chosen so labels do not cover points or bars
OFFSET = {
    ("RH_step", "MOF-303"): (6, 6), ("RH_step", "MOF-801"): (8, -14), ("RH_step", "CAU-10-H"): (6, -10),
    ("RH_step", "Al-fumarate"): (6, 5), ("RH_step", "MIL-160(Al)"): (6, 34), ("RH_step", "Co2Cl2(BTDD)"): (6, -3),
    ("henry_fraction", "MOF-303"): (6, 4), ("henry_fraction", "MOF-801"): (6, 2),
    ("henry_fraction", "CAU-10-H"): (6, -3), ("henry_fraction", "Al-fumarate"): (6, -13),
    ("henry_fraction", "MIL-160(Al)"): (6, 3), ("henry_fraction", "Co2Cl2(BTDD)"): (6, 4),
}


def mid(v):
    return 0.5 * (v["lo"] + v["hi"])


def short(name):
    return name.split(" (")[0] if "Basolite" in name else name


def draw(ax, d, xk, yk, sx=1.0):
    (x0, x1), (y0, y1) = sorted(d["design"][xk]), sorted(d["design"][yk])
    ax.add_patch(Rectangle((sx * x0, y0), sx * (x1 - x0), y1 - y0, color="0.92", zorder=0))
    ax.add_patch(Rectangle((sx * x0, y0), sx * (x1 - x0), y1 - y0, fill=False, ec="0.55", lw=0.8,
                           ls="--", zorder=1))
    ax.text(sx * x1, y1, "sampled range ", ha="right", va="bottom", fontsize=6.4, color="0.4")
    for name, m in d["materials"].items():
        key = short(name)
        x, y = m.get(xk), m.get(yk)
        if x is None or y is None:
            continue
        col, mk = COL.get(key, "0.3"), MARK.get(key, "o")
        ax.errorbar(sx * mid(x), mid(y), xerr=[[sx * (mid(x) - x["lo"])], [sx * (x["hi"] - mid(x))]],
                    yerr=[[mid(y) - y["lo"]], [y["hi"] - mid(y)]], fmt=mk, ms=4.5, capsize=2,
                    lw=0.9, color=col, zorder=3)
        ax.annotate(key.replace("Co2Cl2", "Co$_2$Cl$_2$"), (sx * mid(x), mid(y)), textcoords="offset points",
                    xytext=OFFSET.get((xk, key), (6, 4)), fontsize=6.6, color=col,
                    # a label moved far from a crowded point gets a leader line
                    arrowprops=(dict(arrowstyle="-", lw=0.5, color=col, shrinkA=1, shrinkB=3)
                                if max(map(abs, OFFSET.get((xk, key), (6, 4)))) > 20 else None),
                    ha="right" if OFFSET.get((xk, key), (6, 4))[0] < 0 else "left")


def main():
    fs.apply()
    d = json.load(open(SRC, encoding="utf-8"))
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9))
    fig.subplots_adjust(wspace=0.55)

    draw(a, d, "RH_step", "q_max", sx=100.0)
    a.set_xlabel("step position (% RH)")
    a.set_ylabel("capacity (mol kg$^{-1}$)")
    a.set_title("A  Step position and capacity")
    lo, hi = a.get_ylim()
    sec = a.twinx()
    sec.set_ylim(lo * M_WATER, hi * M_WATER)
    sec.set_ylabel("capacity (g g$^{-1}$)")
    sec.grid(False)
    sec.spines["right"].set_visible(True)

    draw(b, d, "henry_fraction", "dH")
    b.set_xlabel("fraction of capacity below the step")
    b.set_ylabel("heat of adsorption $\\Delta H$ (kJ mol$^{-1}$)")
    b.set_title("B  Low-humidity uptake and heat")

    fig.savefig("figures/FigS2_water_mofs.pdf")
    fig.savefig("figures/FigS2_water_mofs.png")
    print("wrote figures/FigS2_water_mofs.pdf / .png")


if __name__ == "__main__":
    main()
