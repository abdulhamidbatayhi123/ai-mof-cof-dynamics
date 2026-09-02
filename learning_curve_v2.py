"""The materials learning curve on dataset v2 — L1's load-bearing measurement.

Design frozen in PREREG_L1L2L7_v2.md §2(b),(c). Read that first.

Retraction A18 narrowed L1 to "more conditions is eliminated; more materials is
not" because the legacy curve was still falling 1.82x at 48 training materials.
Retraction A21 showed the coefficient-map ceiling at 48 materials is a sample-size
effect. Dataset v2 has 192 training materials per fold. This script measures
whether the axis closes.

Function class and encoding are those of `learning_curve.py`, `l5_bottleneck.py`
and `warp_verdict.py`: the c-channel at 128x128, POD p = 32 + per-mode gradient
boosting, so the v2 curve is comparable to the legacy A18 numbers. It is NOT
comparable to run_l1_v2's table (three channels, 64 modes, different arms).

Axes
  materials    n in {12, 24, 48, 96, 192} training materials per fold
  conditions   fraction f in {0.25, 0.5, 0.75, 1.0} of each material's conditions,
               at the full 192 materials

Targets, every cell, on the held-out fold
  field_refit     POD refit on the subset -> what a practitioner with n materials gets
  field_fixed     POD fixed on the fold's full 192 training materials, regressor
                  trained on the subset -> separates basis-needs-data from map-needs-data
  mode_r2         per-mode R2 of the coefficient map, fixed basis, modes 1..32 (A21)
  r2_t_lo/t_hi    R2 of the two front trajectories at levels (0.05, 0.95) — the
                  two-wave warp's bottleneck

Every size has 3 seeds moving every stochastic component: the material subset,
the randomised SVD and HGB's early-stopping split. The full size is NOT exempt
(the legacy script ran it once with random_state=0; retraction A24).

Five folds: the L6-v2 fold map, so the held-out materials are the same 240 that
L1-(a), L2 and L6 report on. Cells are written as they complete and resumed.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor

import ladder_data
from comoving import arrival_time, nrmse
from v2_common import (FIELD_RES, ROOT_V2, assert_disjoint, get_path, load_folds,
                       load_or_init, set_path, standardise_params, write_atomic)

SIZES = (12, 24, 48, 96, 192)
FRACS = (0.25, 0.50, 0.75, 1.00)
SEEDS = (42, 43, 44)
P_FIELD = 32
P_WARP = 8
LEVELS = (0.05, 0.95)


def load_c_channel(root, field_res):
    """c-channel only, subsampled on load — 259 MB for v2, not 3.1 GB."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    keys = ladder_data.param_keys_for(man)
    rows, flds = [], []
    zi = ti = None
    for s in man["samples"]:
        f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not os.path.exists(f):
            continue
        arr = np.load(f, mmap_mode="r")
        if zi is None:
            zi = np.linspace(0, arr.shape[1] - 1, field_res).astype(int)
            ti = np.linspace(0, arr.shape[2] - 1, field_res).astype(int)
        flds.append(np.array(arr[0][np.ix_(zi, ti)], dtype=np.float32))
        m, c = mats[s["mat"]], conds[s["cond"]]
        rows.append(([(m if k in m else c)[k] for k in keys], s["mat"], s["cond"], s["split"]))
    X = np.stack(flds)
    params = np.array([r[0] for r in rows], dtype=np.float64)
    mat = np.array([r[1] for r in rows])
    cond = np.array([r[2] for r in rows])
    split = np.array([r[3] for r in rows])
    print(f"loaded c-channel {X.shape} ({X.nbytes / 1e6:.0f} MB), design {man.get('design')}")
    return X, params, mat, cond, split


def hgb(seed):
    return HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                         early_stopping=True, random_state=seed)


def r2(pred, true, idx):
    return float(1.0 - ((pred[idx] - true[idx]) ** 2).sum()
                 / max(((true[idx] - true[idx].mean()) ** 2).sum(), 1e-30))


def fit_pca_sub(flat, fit_idx, n_comp, seed):
    """PCA on `fit_idx` only; returns (pca, standardised coefficients OF fit_idx, mu, sd).

    Only the fit rows are transformed here. Transforming all 3947 fields per cell
    materialised ~260 MB float32 arrays three times over and paged on a 16 GB
    machine (one cell took 305 s in the smoke test); the held-out fold is
    transformed separately, and only it is ever reconstructed.
    """
    n_comp = min(n_comp, len(fit_idx) - 1, flat.shape[1])
    pca = PCA(n_components=n_comp, svd_solver="randomized", random_state=seed).fit(flat[fit_idx])
    A = pca.transform(flat[fit_idx])
    mu, sd = A.mean(0), A.std(0)
    sd[sd == 0] = 1.0
    return pca, (A - mu) / sd, mu, sd


def regress_modes_sub(P_fit, Az_fit, P_pred, seed):
    """Fit one HGB per mode on (P_fit, Az_fit); return predictions at P_pred."""
    out = np.empty((P_pred.shape[0], Az_fit.shape[1]), dtype=np.float64)
    for k in range(Az_fit.shape[1]):
        m = hgb(seed).fit(P_fit, Az_fit[:, k])
        out[:, k] = m.predict(P_pred)
    return out


def cell(X, Pz, t_lo, t_hi, sub, te, fixed, seed):
    """One learning-curve cell. `fixed` = (pca, Az_te, mu, sd) — the basis fitted on
    the fold's FULL training set, with the held-out fold's standardised true
    coefficients. Everything reconstructed here is held-out only."""
    assert_disjoint(sub, te, "learning-curve subset")
    flat = X.reshape(X.shape[0], -1)
    X_te = X[te]

    # (1) honest curve: basis refit on the subset
    pca_s, Az_s, mu_s, sd_s = fit_pca_sub(flat, sub, P_FIELD, seed)
    P_s = regress_modes_sub(Pz[sub], Az_s, Pz[te], seed)
    rec_s = pca_s.inverse_transform(P_s * sd_s + mu_s).astype(np.float32).reshape(X_te.shape)
    e_refit = nrmse(rec_s, X_te)
    del rec_s

    # (2) fixed basis, regressor on the subset; per-mode R2 on the held-out fold
    pca_f, Az_f_te, mu_f, sd_f, Az_f_sub = fixed(sub)
    P_f = regress_modes_sub(Pz[sub], Az_f_sub, Pz[te], seed)
    rec_f = pca_f.inverse_transform(P_f * sd_f + mu_f).astype(np.float32).reshape(X_te.shape)
    e_fixed = nrmse(rec_f, X_te)
    del rec_f
    mode_r2 = [r2(P_f[:, k], Az_f_te[:, k], np.arange(len(te))) for k in range(Az_f_te.shape[1])]

    # (3) the two front trajectories
    out_w = {}
    for name, T in (("t_lo", t_lo), ("t_hi", t_hi)):
        pca_w, Az_w, mu_w, sd_w = fit_pca_sub(T, sub, P_WARP, seed)
        P_w = regress_modes_sub(Pz[sub], Az_w, Pz[te], seed)
        pred = pca_w.inverse_transform(P_w * sd_w + mu_w)
        out_w[f"r2_{name}"] = r2(pred, T[te], np.arange(len(te)))

    return {"seed": seed, "n_train": int(len(sub)),
            "field_refit": float(e_refit.mean()),
            "field_fixed": float(e_fixed.mean()),
            "per_sample_refit": [float(v) for v in e_refit],
            "per_sample_fixed": [float(v) for v in e_fixed],
            "mode_r2": mode_r2, **out_w}


class FixedBasis:
    """The fold's fixed basis (fitted on the full training set once per seed).

    Calling it with a subset returns (pca, Az_te, mu, sd, Az_sub): the held-out
    fold's standardised true coefficients and the subset's, both under the
    train-set standardisation — without ever transforming every sample at once.
    """

    def __init__(self, flat, tr, te, seed):
        assert_disjoint(tr, te, "fixed POD basis")
        self.pca, Az_tr, self.mu, self.sd = fit_pca_sub(flat, tr, P_FIELD, seed)
        self.tr = tr
        self.pos = {int(i): k for k, i in enumerate(tr)}
        self.Az_tr = Az_tr
        self.Az_te = (self.pca.transform(flat[te]) - self.mu) / self.sd

    def __call__(self, sub):
        rows = np.array([self.pos[int(i)] for i in sub])
        return self.pca, self.Az_te, self.mu, self.sd, self.Az_tr[rows]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--field-res", type=int, default=FIELD_RES)
    ap.add_argument("--sizes", type=int, nargs="+", default=list(SIZES))
    ap.add_argument("--fracs", type=float, nargs="+", default=list(FRACS))
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--only-folds", type=int, nargs="+", default=None)
    ap.add_argument("--axes", nargs="+", default=["materials", "conditions"])
    ap.add_argument("--out", default="results/learning_curve_v2.json")
    args = ap.parse_args()

    t0 = time.time()
    X, params, mat, cond, split = load_c_channel(args.root, args.field_res)
    fold_of, n_folds, fold_seed = load_folds(mat)
    N, NZ, NT = X.shape
    u = np.linspace(0.0, 1.0, NT)
    t_lo, nb_lo = arrival_time(X, u, LEVELS[0])
    t_hi, nb_hi = arrival_time(X, u, LEVELS[1])
    t_hi = t_lo + np.maximum(t_hi - t_lo, 1e-3)
    print(f"arrival times at {LEVELS}: never-crossed cells lo={nb_lo} hi={nb_hi} "
          f"of {N * NZ}  [{time.time() - t0:.0f}s]")

    header = {"root": args.root, "field_res": args.field_res, "field_shape": [NZ, NT],
              "p_field": P_FIELD, "p_warp": P_WARP, "levels": list(LEVELS),
              "sizes": args.sizes, "fracs": args.fracs, "seeds": args.seeds,
              "fold_file": "results/l6_v2_folds.json", "fold_seed": fold_seed,
              "n_folds": n_folds, "never_crossed": {"lo": int(nb_lo), "hi": int(nb_hi)}}
    res, resumed = load_or_init(args.out, header,
                                ("root", "field_res", "p_field", "p_warp", "sizes", "fracs",
                                 "seeds", "fold_seed", "n_folds"))
    if resumed:
        print(f"  resuming {args.out}")

    folds = args.only_folds if args.only_folds is not None else list(range(n_folds))
    for f in folds:
        te = np.where(fold_of == f)[0]
        tr = np.where(fold_of != f)[0]
        tr_mats = np.unique(mat[tr])
        Pz = standardise_params(params, tr)
        flat = X.reshape(N, -1)
        fixed_by_seed = {}
        print(f"\n=== FOLD {f}: {len(tr)} train conds / {len(tr_mats)} materials | "
              f"{len(te)} held-out conds / {len(np.unique(mat[te]))} materials ===")
        set_path(res, {"n_train": int(len(tr)), "n_test": int(len(te)),
                       "material_ids_test": mat[te].tolist(),
                       "condition_ids_test": cond[te].tolist()}, "folds", str(f), "sizes")

        for axis in args.axes:
            grid = args.sizes if axis == "materials" else args.fracs
            for g in grid:
                for seed in args.seeds:
                    key = ("folds", str(f), axis, str(g), str(seed))
                    if get_path(res, *key) is not None:
                        continue
                    t1 = time.time()
                    rng = np.random.default_rng(seed * 1000 + f)
                    if axis == "materials":
                        k = int(g)
                        if k > len(tr_mats):
                            raise SystemExit(f"size {k} exceeds the fold's {len(tr_mats)} training materials")
                        keep = set(rng.choice(tr_mats, size=k, replace=False).tolist())
                        sub = np.array([i for i in tr if mat[i] in keep])
                    else:
                        sub = []
                        for m in tr_mats:
                            idx = tr[mat[tr] == m]
                            k = max(1, int(round(float(g) * len(idx))))
                            sub.extend(rng.choice(idx, size=k, replace=False).tolist())
                        sub = np.array(sorted(sub))
                    if seed not in fixed_by_seed:
                        fixed_by_seed[seed] = FixedBasis(flat, tr, te, seed)
                    rec = cell(X, Pz, t_lo, t_hi, sub, te, fixed_by_seed[seed], seed)
                    rec["n_materials"] = int(len(np.unique(mat[sub])))
                    set_path(res, rec, *key)
                    write_atomic(res, args.out)
                    print(f"  {axis:<10} {str(g):>5} seed {seed}: n_train {rec['n_train']:>4} "
                          f"mats {rec['n_materials']:>3} | refit {rec['field_refit']:.5f} "
                          f"fixed {rec['field_fixed']:.5f} | R2 t_lo {rec['r2_t_lo']:+.3f} "
                          f"t_hi {rec['r2_t_hi']:+.3f} | modes R2>0.5: "
                          f"{sum(1 for v in rec['mode_r2'] if v > 0.5)}/{len(rec['mode_r2'])}  "
                          f"[{time.time() - t1:.0f}s]", flush=True)
        del fixed_by_seed

    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
