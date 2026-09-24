"""L5's mechanism table, on dataset v2: 240 materials, five folds, three seeds.

WHY THIS EXISTS. `l5_bottleneck.py` measures the load-bearing claim of the whole
paper -- that what binds the error is the parameter-to-coefficient MAP and not the
basis -- and it measures it on the legacy design: **12 held-out materials, one
split, one seed**. L1, L2, L6 and L7 all report over 240 materials in five folds.

Retraction A26 exists precisely because a verdict measured at one material count did
not survive four times as many. A referee will ask why the paper's central
mechanism is one of the three results still on the old data, and the honest answer
today is "nobody has costed it". `audit_risk.md` identifies this as the single
cheapest experiment that most reduces the paper's risk: roughly one to two hours
against twenty-six to thirty-nine for the DeepONet re-run.

WHAT CHANGES FROM THE LEGACY SCRIPT, and nothing else changes:

  1. root               data/parametric -> data/parametric_v2
  2. split              a single `split == "novel_material"` column (12 materials)
                        -> the L6-v2 five-fold map over all 240, pooled OUT OF FOLD
  3. seeds              one -> three, varying the regressor's random_state only
                        (the POD basis is deterministic given the fit set)
  4. statistics         a mean -> a paired, cluster-robust interval by material at
                        the v2 five-fold calibrated level, plus the MDE

WHAT IS DELIBERATELY IDENTICAL. The subsampling (128x128), the channel (c), the
normalisation (per-sample range over the FULL field, rule 5 / A15), the coefficient
standardisation before regression (defect B14: unscaled POD coefficients span ~300x
and silently underfit), and the two regressors. If the v2 numbers differ from the
legacy ones it must be the dataset, not the method.

MEMORY. The c-channel at 128x128 over 3947 samples is ~259 MB resident, loaded via
mmap one sample at a time. That fits beside nothing else -- do not run this while a
training chain is alive. `autorun.sh` sequences it for exactly that reason.

    python l5_bottleneck_v2.py                 # all five p, all five folds
    python l5_bottleneck_v2.py --ps 8 128      # a subset, for a smoke test

Writes results/l5_bottleneck_v2.json, resumably: each (p, fold, seed) cell is
written as it completes and completed cells are skipped on restart.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV

import ladder_data
from mde import mde_report
from metrics import ArmResult, compare
from v2_common import assert_disjoint, load_folds, write_atomic

NZ_S, NT_S = 128, 128          # identical to run_l5.subsample() and the legacy script
CHANNEL = 0                    # c
ROOT = "data/parametric_v2"
OUT = "results/l5_bottleneck_v2.json"
ALPHA = 0.02                   # the v2 five-fold calibrated level (calibration_v2)
SEEDS = (42, 43, 44)
PS = (8, 16, 32, 64, 128)


def load_c_light(root=ROOT):
    """Channel c only, subsampled to (NZ_S, NT_S), via mmap. ~259 MB, not 3 GB."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    keys = ladder_data.param_keys_for(man)
    rows, flds = [], []
    zi = ti = None
    for s in man["samples"]:
        if not s.get("ok", True):
            continue
        f = os.path.join(root, f"m{s['mat']:04d}_c{s['cond']:04d}.npy")
        if not os.path.exists(f):
            continue
        arr = np.load(f, mmap_mode="r")                     # (3, nz, nt)
        if zi is None:
            nz, nt = arr.shape[1], arr.shape[2]
            zi = np.linspace(0, nz - 1, NZ_S).astype(int)
            ti = np.linspace(0, nt - 1, NT_S).astype(int)
        flds.append(np.array(arr[CHANNEL][np.ix_(zi, ti)], dtype=np.float32))
        m, c = mats[s["mat"]], conds[s["cond"]]
        rows.append(([(m if k in m else c)[k] for k in keys], s["mat"]))
    params = np.array([r[0] for r in rows], dtype=np.float64)
    material_ids = np.array([r[1] for r in rows])
    X = np.stack(flds).reshape(len(rows), -1)               # (N, NZ_S*NT_S)
    print(f"loaded c-channel {X.shape}  ({X.nbytes / 1e6:.0f} MB), "
          f"{len(np.unique(material_ids))} materials, params {list(keys)}")
    return X, params, material_ids


def nrmse_per_sample(rec, true):
    """Per-sample range over the FULL field -- rule 5, retraction A15.

    The denominator is asserted non-vanishing by the caller; a window-local range
    that collapses after breakthrough is what destroyed every time-axis number in
    one rung.
    """
    rng = true.max(1) - true.min(1)
    return np.sqrt(((rec - true) ** 2).mean(1)) / np.maximum(rng, 1e-12)


def fit_cell(X, Pz, fit_idx, eval_idx, p, seed):
    """One (p, fold, seed): POD on the fit set, coefficients predicted, reconstructed.

    Returns (basis_floor_eval, coef_pred_eval, best_regressor, mode_r2, per_reg).
    """
    assert_disjoint(fit_idx, eval_idx, f"POD basis (p={p}, seed={seed})")
    pca = PCA(n_components=p, svd_solver="randomized", random_state=0).fit(X[fit_idx])
    A = pca.transform(X)                                    # true coefficients

    # (1) BASIS error: optimal coefficients in a p-term basis = the n-width floor
    e_basis = nrmse_per_sample(pca.inverse_transform(A), X)

    # (2) COEFFICIENT error. Standardise the targets first (B14).
    amu, asd = A[fit_idx].mean(0), A[fit_idx].std(0)
    asd[asd == 0] = 1.0
    Az = (A - amu) / asd

    preds = {}
    rg = RidgeCV(alphas=np.logspace(-4, 4, 25)).fit(Pz[fit_idx], Az[fit_idx])
    preds["ridge"] = rg.predict(Pz)
    gb = np.zeros_like(Az)
    for k in range(p):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          early_stopping=True, random_state=seed)
        m.fit(Pz[fit_idx], Az[fit_idx, k])
        gb[:, k] = m.predict(Pz)
    preds["hgb"] = gb

    per_reg, best_name, best_e = {}, None, None
    for name, Azp in preds.items():
        e = nrmse_per_sample(pca.inverse_transform(Azp * asd + amu), X)
        per_reg[name] = float(e[eval_idx].mean())
        if best_e is None or e[eval_idx].mean() < best_e[eval_idx].mean():
            best_name, best_e = name, e
    Azb = preds[best_name]
    denom = ((Az[eval_idx] - Az[eval_idx].mean(0)) ** 2).sum(0)
    mode_r2 = [float(1.0 - ((Azb[eval_idx, k] - Az[eval_idx, k]) ** 2).sum()
                     / max(denom[k], 1e-30)) for k in range(p)]
    return e_basis, best_e, best_name, mode_r2, per_reg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ps", type=int, nargs="+", default=list(PS))
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--mde-trials", type=int, default=200)
    args = ap.parse_args()
    t0 = time.time()

    X, params, mat = load_c_light()
    fold_of, n_folds, fold_seed = load_folds(mat)
    rng_min = float((X.max(1) - X.min(1)).min())
    print(f"folds {n_folds} (seed {fold_seed}); min per-sample range {rng_min:.4f}")
    if rng_min <= 1e-3:
        raise SystemExit("vanishing per-sample range -- the metric would be invalid (rule 5)")

    res = {}
    if os.path.exists(args.out):
        res = json.load(open(args.out))
        print(f"  resuming {args.out}")
    res.setdefault("_what", "L5's basis-vs-coefficient decomposition on dataset v2, "
                            "five folds over 240 materials, three seeds")
    res.update({"nz_s": NZ_S, "nt_s": NT_S, "channel": "c", "root": ROOT,
                "alpha": ALPHA, "n_folds": n_folds, "fold_seed": fold_seed,
                "seeds": list(args.seeds), "ps": list(args.ps),
                "n_samples": int(X.shape[0]), "n_materials": int(np.unique(mat).size),
                "min_sample_range": rng_min})
    res.setdefault("cells", {})

    for p in args.ps:
        for f in range(n_folds):
            fit_idx = np.where(fold_of != f)[0]
            ev_idx = np.where(fold_of == f)[0]
            # params standardised on THIS fold's fit set only -- a scaler fitted on
            # everything is the leakage A8's neighbourhood is made of
            mu, sd = params[fit_idx].mean(0), params[fit_idx].std(0)
            sd[sd == 0] = 1.0
            Pz = (params - mu) / sd
            for seed in args.seeds:
                key = f"p{p}/f{f}/s{seed}"
                if key in res["cells"]:
                    continue
                t1 = time.time()
                e_basis, e_coef, best, mode_r2, per_reg = fit_cell(
                    X, Pz, fit_idx, ev_idx, p, seed)
                res["cells"][key] = {
                    "p": p, "fold": f, "seed": seed,
                    "basis_floor": float(e_basis[ev_idx].mean()),
                    "coef_pred": float(e_coef[ev_idx].mean()),
                    "best_regressor": best,
                    "per_regressor": per_reg,
                    "mode_r2": mode_r2,
                    "modes_r2_gt_0.2": int(sum(1 for v in mode_r2 if v > 0.2)),
                    "modes_r2_gt_0.5": int(sum(1 for v in mode_r2 if v > 0.5)),
                    "per_sample_basis": [float(v) for v in e_basis[ev_idx]],
                    "per_sample_coef": [float(v) for v in e_coef[ev_idx]],
                    "material_ids": mat[ev_idx].tolist(),
                    "secs": time.time() - t1,
                }
                write_atomic(res, args.out)
                print(f"  p={p:>4} fold {f} seed {seed}: floor "
                      f"{res['cells'][key]['basis_floor']:.5f}  coef-pred "
                      f"{res['cells'][key]['coef_pred']:.5f} ({best})  "
                      f"modes R2>0.2: {res['cells'][key]['modes_r2_gt_0.2']}/{p}  "
                      f"[{time.time() - t1:.0f}s]", flush=True)

    # ---- pooled out-of-fold summary, seed-averaged, with intervals ----------
    res["summary"] = {}
    for p in args.ps:
        cells = [res["cells"][k] for k in res["cells"]
                 if res["cells"][k]["p"] == p]
        if len(cells) < n_folds * len(args.seeds):
            continue
        basis, coef, mats_pooled = [], [], []
        for f in range(n_folds):
            fc = [c for c in cells if c["fold"] == f]
            ids = fc[0]["material_ids"]
            if any(c["material_ids"] != ids for c in fc):
                raise AssertionError(f"p={p} fold {f}: seeds scored different samples")
            basis.append(np.mean([c["per_sample_basis"] for c in fc], axis=0))
            coef.append(np.mean([c["per_sample_coef"] for c in fc], axis=0))
            mats_pooled.append(np.asarray(ids))
        b = np.concatenate(basis); c_ = np.concatenate(coef)
        m = np.concatenate(mats_pooled)
        cmp_ = compare(ArmResult("basis floor", m, b), ArmResult("coefficient map", m, c_),
                       alpha=ALPHA, n_boot=20000)
        res["summary"][str(p)] = {
            "basis_floor": float(b.mean()), "coef_pred": float(c_.mean()),
            "ratio_coef_over_floor": float(c_.mean() / b.mean()),
            "modes_r2_gt_0.2": float(np.mean([c["modes_r2_gt_0.2"] for c in cells])),
            "floor_vs_coef": cmp_,
            "n_clusters": int(np.unique(m).size),
        }
        print(f"  [pooled] p={p:>4}  floor {b.mean():.5f}  coef-pred {c_.mean():.5f}  "
              f"({c_.mean() / b.mean():.0f}x the floor)  "
              f"modes R2>0.2 {np.mean([c['modes_r2_gt_0.2'] for c in cells]):.1f}")

    # the flat-in-p statement, measured: smallest p against largest p
    if len(args.ps) >= 2:
        lo, hi = min(args.ps), max(args.ps)
        if str(lo) in res["summary"] and str(hi) in res["summary"]:
            def pooled(p, which):
                out_v, out_m = [], []
                for f in range(n_folds):
                    fc = [res["cells"][k] for k in res["cells"]
                          if res["cells"][k]["p"] == p and res["cells"][k]["fold"] == f]
                    out_v.append(np.mean([c[which] for c in fc], axis=0))
                    out_m.append(np.asarray(fc[0]["material_ids"]))
                return np.concatenate(out_v), np.concatenate(out_m)
            v_lo, m_lo = pooled(lo, "per_sample_coef")
            v_hi, m_hi = pooled(hi, "per_sample_coef")
            if not np.array_equal(m_lo, m_hi):
                raise AssertionError("p=lo and p=hi pooled over different samples")
            c2 = compare(ArmResult(f"coef map p={lo}", m_lo, v_lo),
                         ArmResult(f"coef map p={hi}", m_hi, v_hi),
                         alpha=ALPHA, n_boot=20000)
            rep = None
            if not c2["significant"]:
                rep = mde_report(v_hi - v_lo, m_lo, base=float(v_lo.mean()), alpha=ALPHA,
                                 effects=(0.0, 0.02, 0.05, 0.10, 0.20),
                                 trials=args.mde_trials,
                                 label=f"coefficient map p={lo} vs p={hi}")
            res["coef_flat_in_p"] = {"p_lo": lo, "p_hi": hi, "comparison": c2, "mde": rep}
            print(f"\n  coefficient map p={lo} vs p={hi}: diff {c2['mean_diff']:+.5f} "
                  f"CI [{c2['ci_low']:+.5f}, {c2['ci_high']:+.5f}] "
                  f"{'SIGNIFICANT' if c2['significant'] else 'ns'}")

    write_atomic(res, args.out)
    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
