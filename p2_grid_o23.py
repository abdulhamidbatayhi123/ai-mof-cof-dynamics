"""Paper 2 confirmatory grid, observation models O2 and O3 (PREREG_P2 §3-§4).

Same freeze guard as p2_grid_o1.py (imported, not re-implemented): refuses to run until
a 'FREEZE PREREG_P2' commit exists and the prereg is unchanged since it.

O2  interior c, T (q latent): M1b gas-balance inversion, then every O1 solver in both
    forms -- full grid, 20 replicates (the inversion is cheap).
O3  outlet c(t), T(t) only: profile likelihood of k through the full column (law
    known) on the declared subgrid -- all Da x sigma in {0.5 %, 2 %} x eps in {0, 2 %}
    x both isotherms x Pe x1, 3 replicates. The identifiability side of H2b.

Resumable; results written atomically after every cell.

    python p2_grid_o23.py o2
    python p2_grid_o23.py o3
"""
import itertools
import json
import os
import sys
import time

import numpy as np

from p2.identifiability import identifiable, profile_interval_outlet
from p2.metric import k_accuracy, success_L1
from p2.run_o1 import SOLVERS, discover_o2
from p2_grid_o1 import EPSS, FORMS, N_REP, SIGMAS, frozen
from p2_observe import load_cell, observe, physics_for
from v2_common import write_atomic


def run_o2(man):
    out = "results/p2_o2.json"
    res = json.load(open(out)) if os.path.exists(out) else {"rows": {}}
    for name, rec in sorted(man.items()):
        if rec["law"] != "L1":
            continue
        phys = physics_for(rec)
        phys.D_L = rec["D_L"]
        t0 = time.time()
        for sigma, eps, rep, solver, form in itertools.product(SIGMAS, EPSS, range(N_REP), SOLVERS, FORMS):
            key = f"{name}|{sigma}|{eps}|{rep}|{solver}|{form}"
            if key in res["rows"]:
                continue
            obs = observe(name, rep, sigma, eps, "O2")
            try:
                co = discover_o2(obs, phys, solver, form)
                res["rows"][key] = {"success": bool(success_L1(co)),
                                    "k_acc": float(k_accuracy(co, rec["k_LDF"])), "support": sorted(co)}
            except Exception as e:
                res["rows"][key] = {"success": False, "error": f"{type(e).__name__}: {e}"}
        write_atomic(res, out)
        print(f"O2 {name:<34} [{time.time() - t0:.0f}s]", flush=True)


def run_o3(man):
    out = "results/p2_o3_ident.json"
    res = json.load(open(out)) if os.path.exists(out) else {"rows": {}}
    for name, rec in sorted(man.items()):
        if rec["law"] != "L1" or rec["pe_mult"] != 1.0:
            continue
        phys = physics_for(rec)
        phys.D_L = rec["D_L"]
        f, _ = load_cell(name)
        rng_c = float(f["c"].max() - f["c"].min())
        rng_T = float(f["T"].max() - f["T"].min()) or 1.0
        for sigma, eps, rep in itertools.product((0.005, 0.02), (0.0, 0.02), range(3)):
            key = f"{name}|{sigma}|{eps}|{rep}"
            if key in res["rows"]:
                continue
            obs = observe(name, rep, sigma, eps, "O3")
            t0 = time.time()
            # The profile refits k with the isotherm the method is GIVEN (solver_fd's
            # qstar_fn hook), so identifiability faces the same isotherm error as
            # discovery -- information parity in the comparison H2b makes.
            import copy
            phys_obs = copy.copy(phys)
            phys_obs.qstar_fn = obs["qstar_meas"]
            lo, hi = profile_interval_outlet(phys_obs, rec["c_in"], obs["t"], obs["channels"]["c"][0],
                                             obs["channels"]["T"][0], sigma_c=max(sigma, 1e-4) * rng_c,
                                             sigma_T=max(sigma, 1e-4) * rng_T, n_z=100)
            res["rows"][key] = {"lo": lo, "hi": hi, "k": rec["k_LDF"],
                                "identifiable": bool(identifiable(lo, hi, rec["k_LDF"])),
                                "sec": time.time() - t0}
            write_atomic(res, out)
            print(f"O3 {key:<50} [{lo:.3g}, {hi:.3g}] k={rec['k_LDF']:.3g}", flush=True)


def main():
    ok, why = frozen()
    if not ok:
        sys.exit(f"REFUSED: the pre-registration is not frozen ({why}).")
    man = json.load(open("data/p2/manifest.json"))["cells"]
    {"o2": run_o2, "o3": run_o3}[sys.argv[1]](man)


if __name__ == "__main__":
    main()
