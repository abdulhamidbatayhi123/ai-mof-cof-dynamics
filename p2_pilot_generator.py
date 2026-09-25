"""Paper 2 PILOT -- the data generator only. No discovery method is run here.

Paper 2 (RESEARCH_PROGRAM.md) maps when the adsorption rate law is discoverable
across Damkohler number. Before its pre-registration is frozen, one thing must be
known that is NOT an outcome: can the verified solver produce trustworthy fields
across the whole Da range the map needs (1e-1 .. 1e3), at what grid, and at what
cost? At high Da the front sharpens (near equilibrium, shock-like for a favourable
isotherm); at low Da the run must be long enough for breakthrough. Either end can
break grid convergence or the integrator.

For each k_LDF on a log grid, with everything else at the default physics:
  * Da_res = k * (L / u_interstitial)   residence-time Damkohler (primary candidate)
  * Da_run = k * t_final                 the definition dataset v2 records
  * exit-curve change between N_z = 400 and N_z = 800 (the grid-convergence test the
    harness applies, relative to the curve's range), and wall-clock per solve.

Declared as a pilot in the pre-registration and excluded from every confirmatory
analysis. Output: results/p2_pilot_generator.json
"""
import json
import os
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")   # share the machine with the L4b queue

import numpy as np

from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data

K_GRID = np.logspace(-4, 1, 11)      # 1/s
GRIDS = (400, 800)
N_SNAP = 400


def exit_curve(p, n_z, t_final):
    t0 = time.time()
    z, t, y = generate_breakthrough_data(p, N_z=n_z, t_final=t_final, n_snapshots=N_SNAP,
                                         verbose=False)
    return t, y[n_z - 1, :], time.time() - t0


def main():
    rows = []
    for k in K_GRID:
        p = AdsorptionPhysicsConfig()
        p.k_LDF = float(k)
        t_final = 1.5 * p.stoichiometric_time(1.0, p.T_in)
        u_int = p.v / p.eps_t
        rec = {"k_LDF": float(k), "Da_res": float(k * p.L / u_int), "Da_run": float(k * t_final),
               "t_final_s": float(t_final)}
        try:
            (t1, c1, s1), (t2, c2, s2) = (exit_curve(p, n, t_final) for n in GRIDS)
            rng = max(float(c2.max() - c2.min()), 1e-12)
            rec.update({"grid_change_rel": float(np.max(np.abs(c1 - c2)) / rng),
                        "exit_final": float(c2[-1]), "sec_400": s1, "sec_800": s2,
                        "breakthrough": bool(c2[-1] > 0.95)})
        except Exception as e:  # recorded, never hidden
            rec["error"] = f"{type(e).__name__}: {e}"
        rows.append(rec)
        print({k2: (round(v, 4) if isinstance(v, float) else v) for k2, v in rec.items()}, flush=True)
    os.makedirs("results", exist_ok=True)
    json.dump({"_pilot": True, "_note": "generator feasibility only; no discovery run",
               "grids": GRIDS, "rows": rows}, open("results/p2_pilot_generator.json", "w"), indent=2)


if __name__ == "__main__":
    main()
