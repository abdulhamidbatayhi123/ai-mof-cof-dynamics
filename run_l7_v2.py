"""L7 on dataset v2 — the classical control. Design frozen in PREREG_L1L2L7_v2.md.

Zero training, closed form, microseconds. Because nothing is fitted, nothing is
held out: every one of the 3947 samples is a genuine zero-parameter transfer
reference, and the comparison with the learned arm is made on the learned arm's
OUT-OF-FOLD exit-curve predictions (run_l1_v2, fold design), paired sample by
sample over all 240 materials.

Two guards specific to v2:

* `k_LDF` is not in the parameter vector under v2 — it is derived from the
  particle by Glueckauf inside `physics_from_params`. Before any curve is scored
  the derived value is asserted equal to the manifest's per-sample record, so the
  classical forms cannot be run against the wrong kinetics (defect B37's class).
* the time grid is the same 128-point normalised grid the learned arm is scored
  on, so the pairing is exact.

    python run_l7_v2.py
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

import ladder_data
from classical import MODELS
from fetch_real_mof_data import rh_to_conc
from run_l4 import physics_from_params
from v2_common import FIELD_RES, ROOT_V2, exit_nrmse, load_folds, write_atomic
from metrics import breakthrough_times


def load_exit_curves(root, field_res):
    """Only the exit concentration curve of every sample, subsampled to the same
    time grid `ladder_data.load(field_res=...)` uses. ~2 MB, via mmap."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    keys = ladder_data.param_keys_for(man)
    rows, curves = [], []
    ti = None
    for s in man["samples"]:
        f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not os.path.exists(f):
            continue
        arr = np.load(f, mmap_mode="r")
        if ti is None:
            ti = np.linspace(0, arr.shape[2] - 1, field_res).astype(int)
        curves.append(np.array(arr[0, -1, ti], dtype=np.float32))
        m, c = mats[s["mat"]], conds[s["cond"]]
        rows.append(([(m if k in m else c)[k] for k in keys], s["mat"], s["cond"],
                     s["split"], s["t_final"], s.get("k_LDF")))
    return (np.stack(curves), np.array([r[0] for r in rows], dtype=np.float64),
            np.array([r[1] for r in rows]), np.array([r[2] for r in rows]),
            np.array([r[3] for r in rows]), np.array([r[4] for r in rows], dtype=np.float64),
            np.array([r[5] for r in rows], dtype=np.float64), tuple(keys), man.get("design", "legacy"))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--field-res", type=int, default=FIELD_RES)
    ap.add_argument("--out", default="results/l7_v2_results.json")
    args = ap.parse_args()

    t0 = time.time()
    exits, params, mat, cond, split, t_final, k_man, keys, design = load_exit_curves(args.root, args.field_res)
    N, NT = exits.shape
    t_norm = np.linspace(0.0, 1.0, NT)
    fold_of, n_folds, fold_seed = load_folds(mat)
    print(f"loaded {N} exit curves on a {NT}-point grid; design {design}; params {list(keys)}")

    # Rebuild the physics for every sample and ASSERT the derived k_LDF matches
    # the generator's record. A mismatch means the classical forms would be run
    # against a different PDE than the one that produced the data.
    phys = [physics_from_params(params[i], keys) for i in range(N)]
    if design == "v2":
        k_der = np.array([p.k_LDF for p in phys])
        rel = np.abs(k_der - k_man) / np.maximum(np.abs(k_man), 1e-30)
        if not np.all(rel < 1e-9):
            raise SystemExit(f"ABORT: Glueckauf k_LDF rebuilt from the parameter vector differs from "
                             f"the manifest record (max rel {rel.max():.3e}). See defect B37.")
        print(f"k_LDF reconstruction asserted: max relative deviation {rel.max():.2e} over {N} samples")

    res = {"root": args.root, "design_of_data": design, "field_res": args.field_res,
           "n_t": int(NT), "fold_file": "results/l6_v2_folds.json", "fold_seed": fold_seed,
           "n_folds": n_folds, "n_samples": int(N), "n_materials": int(len(np.unique(mat))),
           "split_counts": {s: int((split == s).sum()) for s in ladder_data.SPLITS},
           "material_ids": mat.tolist(), "condition_ids": cond.tolist(),
           "split": split.tolist(), "fold": fold_of.tolist(), "models": {}}
    print(f"\n{'model':<20} {'exit nRMSE':>11} {'dt50 (h)':>9} {'ms/curve':>9}   (all {N} samples)")
    for name, fn in MODELS.items():
        e, dt05, dt50, dt95, wall = [], [], [], [], 0.0
        for i in range(N):
            p = phys[i]
            c_in = rh_to_conc(params[i][keys.index("rh_feed")], p.T_in)
            t = t_norm * t_final[i]
            t1 = time.perf_counter()
            pred = np.asarray(fn(p, c_in, p.T_in, t), dtype=np.float64)
            wall += time.perf_counter() - t1
            truth = exits[i].astype(np.float64)
            e.append(exit_nrmse(pred, truth))
            bp, bt = breakthrough_times(pred, t_norm), breakthrough_times(truth, t_norm)
            for lev, store in ((0.05, dt05), (0.50, dt50), (0.95, dt95)):
                a, b = bp[lev], bt[lev]
                store.append(abs(a - b) * t_final[i] if np.isfinite(a) and np.isfinite(b) else np.nan)
        res["models"][name] = {
            "nrmse": float(np.mean(e)), "dt_bt05": float(np.nanmean(dt05)),
            "dt_bt50": float(np.nanmean(dt50)), "dt_bt95": float(np.nanmean(dt95)),
            "per_sample_nrmse": e, "per_sample_dt_bt50": dt50,
            "ms_per_curve": 1e3 * wall / N,
            "by_split": {s: float(np.mean(np.array(e)[split == s])) for s in ladder_data.SPLITS}}
        print(f"{name:<20} {np.mean(e):>11.4f} {np.nanmean(dt50) / 3600:>9.2f} "
              f"{1e3 * wall / N:>9.3f}", flush=True)

    write_atomic(res, args.out)
    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")
    print("Run analyze_l7_v2.py once run_l1_v2.py's fold design is complete.")


if __name__ == "__main__":
    main()
