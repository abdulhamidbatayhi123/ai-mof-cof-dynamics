"""Paper 2 ground truth: noise-free solver fields over (Da, Pe, isotherm, law).

PREREG_P2_discoverability.md §4.1-4.2. Noise and isotherm error are applied AFTER
the solve (p2_observe.py, to be written), so ground truth is only these solves.
No discovery method is run here; generating ground truth does not look at outcomes.

Cells:
  Da = k * t_stoich    9 levels, log-spaced 1e-1 .. 1e3   (primary axis; pilot fact 1)
  Pe multiplier on D_L  x0.2, x1, x5
  isotherm              langmuir (default physics, c_in = 1)
                        step     (get_mof303_physics, c_in = 30 % RH)
  law                   L1 constant k; L2 k(q) dropping 80 % across the step
                        (step isotherm only)
Horizon 4 t_stoich (pilot fact 3), extended x2 until the outlet passes 0.95.
N_z = 400 (pilot fact 4).

Output: data/p2/<cell>.npz  (z, t, c, q, T  float32; parameters) and
        data/p2/manifest.json  (every parameter, t_stoich, horizon, checks).
Resumable: an existing cell file is skipped.

    python p2_generate.py            # all cells
    python p2_generate.py --list     # cells only
"""
from __future__ import annotations

import argparse
import json
import os
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

from fetch_real_mof_data import get_mof303_physics, rh_to_conc
from isotherm import q_star_np
from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data

OUT = "data/p2"
DA_LEVELS = np.logspace(-1, 3, 9)
PE_MULT = (0.2, 1.0, 5.0)
N_Z = 400
N_SNAP = 400
HORIZON = 4.0
L2_DROP, L2_WIDTH = 0.8, 0.05


def make_physics(iso):
    if iso == "langmuir":
        p, c_in = AdsorptionPhysicsConfig(), 1.0
    else:
        p = get_mof303_physics()
        c_in = rh_to_conc(0.30, p.T_in)
    return p, float(c_in)


def step_midpoint_fraction(p, c_in):
    """Fractional loading at the steepest point of the isotherm (feed temperature)."""
    c = np.linspace(1e-6, c_in, 4000)
    q = q_star_np(c, np.full_like(c, p.T_in), p)
    i = int(np.argmax(np.gradient(q, c)))
    return float(q[i] / p.q_max)


def cells():
    out = []
    for iso in ("langmuir", "step"):
        for law in (("L1",) if iso == "langmuir" else ("L1", "L2")):
            for pe in PE_MULT:
                for da in DA_LEVELS:
                    out.append((iso, law, pe, float(da)))
    return out


def name(iso, law, pe, da):
    return f"{iso}_{law}_pe{pe:g}_da{da:.3g}"


def solve_cell(iso, law, pe, da):
    p, c_in = make_physics(iso)
    t_st = float(p.stoichiometric_time(c_in, p.T_in))
    p.k_LDF = da / t_st
    p.D_L = p.D_L * pe
    theta = None
    if law == "L2":
        theta = step_midpoint_fraction(p, c_in)
        k0, qm = p.k_LDF, p.q_max
        p.k_of_q = lambda q: k0 * (1.0 - L2_DROP / (1.0 + np.exp(-((q / qm) - theta) / L2_WIDTH)))
    horizon = HORIZON
    for _ in range(4):
        t0 = time.time()
        z, t, y = generate_breakthrough_data(p, N_z=N_Z, t_final=horizon * t_st, c_in=c_in,
                                             n_snapshots=N_SNAP, verbose=False)
        c, q, T = y[:N_Z], y[N_Z:2 * N_Z], y[2 * N_Z:]
        if c[-1, -1] / c_in > 0.95:
            break
        horizon *= 2
    rec = {"iso": iso, "law": law, "pe_mult": pe, "Da": da, "k_LDF": p.k_LDF, "t_stoich_s": t_st,
           "horizon_t_stoich": horizon, "exit_final": float(c[-1, -1] / c_in),
           "breakthrough_95": bool(c[-1, -1] / c_in > 0.95), "c_in": c_in, "D_L": p.D_L,
           "Da_res": float(p.k_LDF * p.L / (p.v / p.eps_t)), "theta_step": theta,
           "q_max": p.q_max, "T_in": p.T_in, "sec": time.time() - t0}
    return rec, z, t, c, q, T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    todo = cells()
    if a.list:
        for c in todo:
            print(name(*c))
        print(len(todo), "cells")
        return
    os.makedirs(OUT, exist_ok=True)
    mpath = os.path.join(OUT, "manifest.json")
    man = json.load(open(mpath)) if os.path.exists(mpath) else {"cells": {}}
    for cell in todo:
        nm = name(*cell)
        f = os.path.join(OUT, nm + ".npz")
        if os.path.exists(f) and nm in man["cells"]:
            continue
        rec, z, t, c, q, T = solve_cell(*cell)
        np.savez_compressed(f, z=z, t=t, c=c.astype(np.float32), q=q.astype(np.float32),
                            T=T.astype(np.float32))
        man["cells"][nm] = rec
        json.dump(man, open(mpath + ".tmp", "w"), indent=1)
        os.replace(mpath + ".tmp", mpath)
        print(f"{nm:<34} exit {rec['exit_final']:.3f} horizon {rec['horizon_t_stoich']:g} "
              f"{rec['sec']:.0f}s", flush=True)
    bad = [k for k, v in man["cells"].items() if not v["breakthrough_95"]]
    print(f"done: {len(man['cells'])} cells; without 95 % breakthrough: {bad or 'none'}")


if __name__ == "__main__":
    main()
