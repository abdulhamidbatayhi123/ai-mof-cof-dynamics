"""Exploratory (NOT pre-registered): does a strong primary site fix the anchor's early leak?

The MOF-303 anchor (PREREG_LASSITTER.md, compare_lassitter.py) reproduces the half-breakthrough
time but leaks far too early, and the paper attributes that to the weak primary sites of the
smooth design (b_H = b_C/20). A second-round internal reviewer asked for the one-solve test.
This script re-solves the pre-registered primary configuration with the primary-site affinity
log10(b_H/b_C) in {-1.3 (smooth design), 0.1 (MOF-like design median), 1.0} and the Henry-site
fraction f_H in {0.06 (the cited MOF-303 form), 0.17 (the below-step fraction its source
reports)}; nothing else changes and nothing is fitted. Labelled exploratory in the paper.

    python anchor_strong_sites.py   -> results/anchor_strong_sites.json
"""
from __future__ import annotations

import json

import numpy as np

import compare_lassitter as cl
from fetch_real_mof_data import rh_to_conc
from v2_common import write_atomic

AFFINITY = (-1.30103, 0.1, 1.0)
FH = (0.06, 0.17)
OUT = "results/anchor_strong_sites.json"


def main():
    eff, _, _ = cl.load_digitised()
    c_in = rh_to_conc(cl.RH_IN, cl.T_K)
    tt = np.linspace(0, cl.HORIZON_MIN, cl.N_SNAP)
    exp = cl.describe(tt, np.interp(tt, eff[:, 0], eff[:, 1]) / (cl.RH_IN * 100.0), eff)
    out = {"_what": __doc__.split("\n\n")[0], "experiment": exp, "runs": {}}
    for a in AFFINITY:
        for fh in FH:
            p = cl.physics(*cl.PRIMARY[:2], 1e4, 1000.0)
            p.henry_fraction = fh
            p.b_H0 = p.b0 * 10.0 ** a
            p.b_H_ratio = 10.0 ** (-a)
            t_min, frac, _ = cl.solve(p, c_in, 500)
            d = cl.describe(t_min, frac, eff)
            idx = np.linspace(0, len(t_min) - 1, 400).astype(int)         # the curve, for the figure
            out["runs"][f"aff{a:+.1f}_fh{fh:.2f}"] = {"affinity_log10": a, "f_H": fh, **d,
                                                    "t_min": t_min[idx].round(3).tolist(),
                                                    "exit_frac": frac[idx].round(5).tolist()}
            print(f"  affinity {a:+.2f} f_H {fh:.2f}: t05 {d['t05_min']:.1f}  t50 {d['t50_min']:.1f}  "
                  f"plateau {d['plateau_150_250_frac']:.3f}  nRMSE {d['nrmse_vs_effluent']:.4f}", flush=True)
    print(f"  experiment: t05 {exp['t05_min']:.1f}  t50 {exp['t50_min']:.1f}  plateau {exp['plateau_150_250_frac']:.3f}")
    write_atomic(out, OUT)


if __name__ == "__main__":
    main()
