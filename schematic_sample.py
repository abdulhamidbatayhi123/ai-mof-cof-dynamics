"""Owner of results/schematic_sample.json: the stored sample drawn in the schematic figure.

The schematic (fig_schematic.py, referee minor 15) shows what a surrogate maps: a
parameter set to a space--time field and its outlet curve. It must draw a REAL stored
field, not an illustration, and the figure gate requires figure scripts to read a
recorded results file rather than compute their series. This script makes that choice
once, by a rule, and records it.

Selection rule (fixed here, not tuned by eye): among the larger dataset's accepted
samples whose second front completes inside the window (outlet at 0.95 of feed by
85 % of the run), the one whose outlet curve spends the largest fraction of its time
between the two fronts -- outlet concentration in [0.10, 0.80] of feed with a slope
below 20 % of its maximum -- i.e. the clearest complete two-wave breakthrough. Ties break on the
lowest (material, condition) id.

    python schematic_sample.py
"""
import json
import os

import numpy as np

from ladder_data import param_keys_for
from v2_common import ROOT_V2

OUT = "results/schematic_sample.json"
RES = 96          # the field is recorded at 96 x 96 for drawing; the outlet curve at full time resolution


def plateau_fraction(exit_curve):
    t = np.linspace(0.0, 1.0, exit_curve.size)
    # the second front must COMPLETE inside the window (0.95 of feed by 85 % of the
    # run): a first version of this rule picked a curve whose step was cut off by
    # the horizon, the clearest plateau and the worst illustration of two fronts
    done = np.nonzero(exit_curve >= 0.95)[0]
    if done.size == 0 or t[done[0]] > 0.85:
        return -1.0
    d = np.gradient(exit_curve, t)
    mask = (exit_curve > 0.10) & (exit_curve < 0.80) & (np.abs(d) < 0.2 * np.abs(d).max())
    return float(mask.mean())


def main():
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    keys = param_keys_for(man)
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    best = None
    for s in sorted(man["samples"], key=lambda s: (s["mat"], s["cond"])):
        f = os.path.join(ROOT_V2, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not s.get("ok", True) or not os.path.exists(f):
            continue
        ex = np.load(f, mmap_mode="r")[0, -1, :].astype(float)
        score = plateau_fraction(ex)
        if best is None or score > best[0]:
            best = (score, s, f)
    score, s, f = best
    arr = np.load(f)
    zi = np.linspace(0, arr.shape[1] - 1, RES).astype(int)
    ti = np.linspace(0, arr.shape[2] - 1, RES).astype(int)
    vec = {k: (mats[s["mat"]] if k in mats[s["mat"]] else conds[s["cond"]])[k] for k in keys}
    out = {"_what": __doc__.splitlines()[0], "rule": "max plateau fraction of the outlet curve",
           "mat": s["mat"], "cond": s["cond"], "plateau_fraction": score, "t_final_s": s["t_final"],
           "params": vec, "c_field": arr[0][np.ix_(zi, ti)].tolist(),
           "exit_curve": arr[0, -1, :].tolist()}
    json.dump(out, open(OUT, "w"))
    print(f"selected m{s['mat']:04d}_c{s['cond']:04d}: plateau fraction {score:.3f}; wrote {OUT}")


if __name__ == "__main__":
    main()
