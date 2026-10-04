"""B-COARSE (PREREG_BASELINES.md §2): the same solver on a coarser grid.

Owner of results/coarse_solver_baseline.json. The cost section compares the
surrogate only with the full-resolution solve; the decision-relevant competitor is a
cheaper NUMERICAL solve at matched accuracy. Frozen design: one sample per material
(240; the condition drawn per material with default_rng(20261004) among its accepted
samples), re-solved with the generator's own physics (build_physics, the recorded
t_final, the generator's integrator settings and 600 snapshots) at
N_z in {50, 100, 200, 400, 800}; resampled to the stored grid with the generator's
`resample`, subsampled to 128 x 128 by ladder_data's rule, and scored with
metrics.per_variable_nrmse against the stored field. Wall time per solve is measured
in this process, and the N_z = 2000 production solve is timed on the first 24 of the
same samples so costs are solve-equivalents on one machine. A coarse solve that fails
or does not reach the acceptance level is counted per N_z, never dropped silently.
Resumable: every (sample, N_z) cell is written as it finishes.

    python coarse_solver_baseline.py
"""
import json
import os
import time

import numpy as np

import gen_parametric_dataset as gen
from metrics import per_variable_nrmse
from solver_fd import generate_breakthrough_data
from v2_common import FIELD_RES, ROOT_V2, write_atomic

OUT = "results/coarse_solver_baseline.json"
NZS = (50, 100, 200, 400, 800)
N_PROD = 24
SEED = 20261004


def solve_fields(p, c_in, t_final, nz, store_nz, store_nt):
    z, t, y = generate_breakthrough_data(p, N_z=nz, t_final=t_final, c_in=c_in, T_in=p.T_in,
                                         n_snapshots=600, verbose=False)
    n = len(z)
    c, q, T = y[:n], y[n:2 * n], y[2 * n:]
    fields = np.stack([gen.resample(z, t, c / c_in, store_nz, store_nt, p.L, t_final),
                       gen.resample(z, t, q / p.q_max, store_nz, store_nt, p.L, t_final),
                       gen.resample(z, t, T / p.T_in, store_nz, store_nt, p.L, t_final)])
    return fields, float(c[-1, -1] / c_in)


def sub(arr, res):
    zi = np.linspace(0, arr.shape[1] - 1, res).astype(int)
    ti = np.linspace(0, arr.shape[2] - 1, res).astype(int)
    return arr[:, zi][:, :, ti]


def main():
    t0 = time.time()
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    by_mat = {}
    for s in man["samples"]:
        if s.get("ok", True) and os.path.exists(os.path.join(ROOT_V2, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")):
            by_mat.setdefault(s["mat"], []).append(s)
    rng = np.random.default_rng(SEED)
    picks = [by_mat[m][int(rng.integers(len(by_mat[m])))] for m in sorted(by_mat)]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {"_what": __doc__.splitlines()[0], "seed": SEED,
                                                           "nzs": list(NZS), "n_prod": N_PROD, "cells": {}}
    store_nz, store_nt = man["store_nz"], man["store_nt"]
    jobs = [(i, nz) for i in range(len(picks)) for nz in NZS] + [(i, 2000) for i in range(N_PROD)]
    for i, nz in jobs:
        s = picks[i]
        key = f"m{s['mat']:04d}_c{s['cond']:04d}_nz{nz}"
        if key in res["cells"]:
            continue
        p = gen.build_physics(mats[s["mat"]], conds[s["cond"]])
        c_in = gen.rh_to_conc(conds[s["cond"]]["rh_feed"], conds[s["cond"]]["T_in"])
        truth = sub(np.load(os.path.join(ROOT_V2, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")), FIELD_RES)
        t1 = time.perf_counter()
        try:
            f, exit_ratio = solve_fields(p, c_in, s["t_final"], nz, store_nz, store_nt)
            wall = time.perf_counter() - t1
            m = per_variable_nrmse(sub(f, FIELD_RES), truth)
            cell = {"mat": s["mat"], "cond": s["cond"], "nz": nz, "wall_s": wall, "exit_ratio": exit_ratio,
                    "accepted": exit_ratio >= 0.90 and bool(np.all(np.isfinite(f))), **{k: float(v) for k, v in m.items()}}
        except Exception as e:
            cell = {"mat": s["mat"], "cond": s["cond"], "nz": nz, "failed": f"{type(e).__name__}: {e}",
                    "wall_s": time.perf_counter() - t1}
        res["cells"][key] = cell
        write_atomic(res, OUT)
        print(f"  {key}: " + (f"c {cell['c']:.4f}  {cell['wall_s']:.2f}s" if "c" in cell else cell["failed"]),
              flush=True)

    # summary per N_z
    prod = [v["wall_s"] for v in res["cells"].values() if v["nz"] == 2000 and "c" in v]
    t_prod = float(np.mean(prod))
    summ = {}
    for nz in NZS:
        cs = [v for v in res["cells"].values() if v["nz"] == nz]
        ok = [v for v in cs if "c" in v and v["accepted"]]
        summ[str(nz)] = {"n": len(cs), "n_failed_or_unaccepted": len(cs) - len(ok),
                         "mean_nrmse_c": float(np.mean([v["c"] for v in ok])) if ok else None,
                         "mean_wall_s": float(np.mean([v["wall_s"] for v in ok])) if ok else None,
                         "solve_equivalents": float(np.mean([v["wall_s"] for v in ok]) / t_prod) if ok else None}
    l1 = json.load(open("results/l1_v2_verdict.json"))["folds"]["table"]["mlp"]["c"]
    l2 = json.load(open("results/l2_v2_verdict.json"))["best_overall"][0]
    def match(target):
        good = [int(nz) for nz, v in summ.items() if v["mean_nrmse_c"] is not None and v["mean_nrmse_c"] <= target]
        return min(good) if good else None
    res["summary"] = {"t_prod_s": t_prod, "n_prod": len(prod), "per_nz": summ,
                      "target_l1_mlp": l1, "target_l2_best": l2,
                      "nz_matching_l1": match(l1), "nz_matching_l2": match(l2)}
    for tag, target, nzm in (("L1-v2 MLP", l1, match(l1)), ("best L2", l2, match(l2))):
        if nzm is None:
            coarsest = summ[str(NZS[0])]["mean_nrmse_c"]
            print(f"  {tag} ({target:.4f}): no tested grid matches it (coarsest N_z={NZS[0]}: {coarsest})")
        else:
            print(f"  {tag} ({target:.4f}): a coarse solve at N_z = {nzm} matches it at "
                  f"{summ[str(nzm)]['solve_equivalents']:.3f} solve-equivalents per query")
    write_atomic(res, OUT)
    print(f"wrote {OUT}  [{time.time() - t0:.0f}s]")
    print("BCOARSE_DONE")


if __name__ == "__main__":
    main()
