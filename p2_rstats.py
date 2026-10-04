"""Owner of results/p2_rstats.json: the ground-truth quantities H2a's R is built from.

PREREG_P2 §4.2: delta = max over the OBSERVED points of |q*(c, T) - q| / q_max, from
ground truth; eps_rec (O2 only) = RMS of (q_hat - q) / q_max of the mass-balance-
inverted uptake against ground truth, computed ONCE per cell from the noise-free O2
observation, over the probes the O2 pipeline uses (edges dropped: the inversion needs
neighbours in z). Neither involves any discovery method, so this runs before the freeze.
R per (cell, sigma, eps, observation) is then delta / sqrt(sigma^2 + eps^2 + eps_rec^2),
with eps_rec = 0 on O1 (p2/analysis.py builds it).

    .venv/Scripts/python.exe p2_rstats.py
"""
import json

import numpy as np

from p2.massbal import invert_uptake
from p2_observe import observe, physics_for

OUT = "results/p2_rstats.json"


def main():
    man = json.load(open("data/p2/manifest.json"))["cells"]
    out = {"_what": __doc__.splitlines()[0], "cells": {}}
    for name, rec in sorted(man.items()):
        if rec["iso"] == "langmuir_iso":
            continue
        o1 = observe(name, 0, 0.0, 0.0, "O1")                 # exact c, q, T at the probes
        c, q, T = (o1["channels"][k] for k in ("c", "q", "T"))
        qs = o1["qstar_meas"](c, T)                          # eps = 0: the TRUE isotherm
        delta = float(np.max(np.abs(qs - q)) / rec["q_max"])
        o2 = observe(name, 0, 0.0, 0.0, "O2")
        phys = physics_for(rec)
        phys.D_L = rec["D_L"]
        q_hat = invert_uptake(o2["channels"]["c"], o2["z"], o2["t"], phys, o2["c_in"])
        inner = slice(1, q_hat.shape[0] - 1)
        eps_rec = float(np.sqrt(np.mean((q_hat[inner] - q[inner]) ** 2)) / rec["q_max"])
        out["cells"][name] = {"delta": delta, "eps_rec": eps_rec, "Da": rec["Da"],
                              "iso": rec["iso"], "law": rec["law"], "pe_mult": rec["pe_mult"]}
        print(f"  {name:<34} delta {delta:.4f}  eps_rec {eps_rec:.4f}", flush=True)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"wrote {OUT}: {len(out['cells'])} cells")


if __name__ == "__main__":
    main()
