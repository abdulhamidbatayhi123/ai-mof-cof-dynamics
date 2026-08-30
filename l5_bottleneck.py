"""L5 diagnostic: WHICH term binds — the basis, or the coefficient map?

DeepONet's output is exactly a linear reconstruction in a learned p-term basis:

    u(params, z, t) = sum_k b_k(params) * t_k(z, t)

Two things can limit it, and they are separable:

  (1) BASIS error   — the best any p-term linear basis can do, given the
                      *optimal* coefficients. This is the Kolmogorov n-width,
                      estimated by POD.  Section 6d measured it: algebraic,
                      d_n ~ n^-1.23, falling 28.7x over p = 8 -> 128.

  (2) COEFFICIENT error — the branch must PREDICT b_k from 11 parameters. POD
                      gets its coefficients by *projecting the true field*,
                      which a surrogate cannot do.

Section 6d asserted (1) is "the load-bearing result of the ladder". The L5 sweep
shows DeepONet FLAT in p at ~0.029 while the floor falls to 0.0005 — 59x below
it. So (1) cannot be what binds. This script measures (2) directly, in the
*optimal* linear basis, so the conclusion does not depend on what basis DeepONet
happened to learn.

Method: fit POD on train, then predict the coefficients from params_z with the
strongest regressor available, and reconstruct. Coefficients are STANDARDISED
before regression — unscaled POD coefficients span ~300x and silently underfit
(defect B14).

Output: results/l5_bottleneck.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV

import ladder_data

NZ_S, NT_S = 128, 128          # identical to run_l5.subsample()
CHANNEL = 0                    # c


def load_c_light(root="data/parametric"):
    """Channel c only, subsampled to (NZ_S, NT_S), via mmap. ~64 MB not 1.5 GB."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    rows, flds = [], []
    zi = ti = None
    for s in man["samples"]:
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
        rows.append(([(m if k in m else c)[k] for k in ladder_data.param_keys_for(man)],
                     s["mat"], s["split"]))
    params = np.array([r[0] for r in rows], dtype=np.float64)
    material_ids = np.array([r[1] for r in rows])
    split = np.array([r[2] for r in rows])
    tr = split == "train"
    mu, sd = params[tr].mean(0), params[tr].std(0)
    sd[sd == 0] = 1.0
    X = np.stack(flds).reshape(len(rows), -1)               # (N, NZ_S*NT_S)
    print(f"loaded c-channel {X.shape}  ({X.nbytes / 1e6:.0f} MB)")
    return X, (params - mu) / sd, material_ids, split


def nrmse_per_sample(rec, true):
    """Identical normalisation to run_l5: per-sample range over the FULL field."""
    rng = true.max(1) - true.min(1)
    return np.sqrt(((rec - true) ** 2).mean(1)) / np.maximum(rng, 1e-12)


def main():
    t0 = time.time()
    X, Pz, mat, split = load_c_light()
    tr = np.where(split == "train")[0]
    nm = np.where(split == "novel_material")[0]
    rng_min = float((X.max(1) - X.min(1)).min())
    print(f"train {len(tr)}  novel_material {len(nm)}")
    print(f"min per-sample range = {rng_min:.4f}  (trap 2: must not be ~0)")
    assert rng_min > 1e-3, "vanishing denominator — metric invalid"

    out = {"nz_s": NZ_S, "nt_s": NT_S, "channel": "c",
           "n_train": len(tr), "n_novel_material": len(nm),
           "min_sample_range": rng_min, "ps": [], "rows": []}

    for p in (8, 16, 32, 64, 128):
        pca = PCA(n_components=p, svd_solver="randomized", random_state=0).fit(X[tr])
        A = pca.transform(X)                                  # true coefficients

        # (1) BASIS error: optimal coefficients, p-term basis = the n-width floor
        rec_true = pca.inverse_transform(A)
        e_basis = nrmse_per_sample(rec_true, X)

        # (2) COEFFICIENT error: predict A from params. Standardise first (B14).
        amu, asd = A[tr].mean(0), A[tr].std(0)
        asd[asd == 0] = 1.0
        Az = (A - amu) / asd

        preds, r2 = {}, {}
        # ridge (linear baseline, alpha tuned by generalised CV)
        rg = RidgeCV(alphas=np.logspace(-4, 4, 25)).fit(Pz[tr], Az[tr])
        preds["ridge"] = rg.predict(Pz)
        # gradient boosting, one model per mode (strongest available -- trap 3)
        gb = np.zeros_like(Az)
        for k in range(p):
            m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                              early_stopping=True, random_state=0)
            m.fit(Pz[tr], Az[tr, k])
            gb[:, k] = m.predict(Pz)
        preds["hgb"] = gb

        best_name, best_e = None, None
        for name, Azp in preds.items():
            rec = pca.inverse_transform(Azp * asd + amu)
            e = nrmse_per_sample(rec, X)
            if best_e is None or e[nm].mean() < best_e[nm].mean():
                best_name, best_e = name, e
            r2[name] = [float(1.0 - ((Azp[nm, k] - Az[nm, k]) ** 2).sum()
                                / max(((Az[nm, k] - Az[nm, k].mean()) ** 2).sum(), 1e-30))
                        for k in range(p)]

        row = {
            "p": p,
            "basis_floor_train": float(e_basis[tr].mean()),
            "basis_floor_novel": float(e_basis[nm].mean()),
            "coef_pred_train": float(best_e[tr].mean()),
            "coef_pred_novel": float(best_e[nm].mean()),
            "best_regressor": best_name,
            "per_regressor_novel": {n: float(nrmse_per_sample(
                pca.inverse_transform(a * asd + amu), X)[nm].mean())
                for n, a in preds.items()},
            "mode_r2_novel": r2[best_name],
            "per_sample_novel": [float(v) for v in best_e[nm]],
            "material_ids_novel": mat[nm].tolist(),
        }
        out["ps"].append(p)
        out["rows"].append(row)
        n_pred = sum(1 for v in r2[best_name] if v > 0.5)
        print(f"p={p:>4}  floor {row['basis_floor_novel']:.5f}   "
              f"coef-pred {row['coef_pred_novel']:.5f} ({best_name})   "
              f"modes with R2>0.5: {n_pred}/{p}")

    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/l5_bottleneck.json", "w"), indent=2)
    print(f"\nwrote results/l5_bottleneck.json  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
