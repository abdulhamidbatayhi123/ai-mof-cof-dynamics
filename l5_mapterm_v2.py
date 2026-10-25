"""The two terms of eq. (split), measured separately, on dataset v2.

Why this exists (Digital Discovery rework, 2026-10-25). `l5_bottleneck_v2.py` reports
`coef_pred`, the TOTAL reconstruction error of POD plus a regressor. That total contains
the basis floor, so it is not the map term of eq. (split); and because each mode has
its own independent regressor, the predictions of modes 1..8 are the same at every p,
so the total can fall with p by at most the p = 8 floor. Its near-constancy in p is
therefore close to arithmetic, not a measurement of the map. A data reviewer found
this; this script measures what the paper should have reported:

  floor    ||u - P_p u||           the error of the best coefficients in the p-term basis
  map      ||P_p u - u_hat||       the error of the predicted coefficients, inside the basis
  total    ||u - u_hat||           with total^2 = floor^2 + map^2 exactly (orthogonality),
                                   per sample, in the per-sample-range nRMSE of rule 5

for BOTH regressors, each pre-specified (ridge and per-mode gradient boosting). The
legacy script picked the better regressor on the held-out materials; here neither is
selected, so no selection correction is needed.

Identical to l5_bottleneck_v2.py in data, subsampling, folds, seeds, scaling and
regressor settings (it imports them). Resumable; low CPU priority.

    python l5_mapterm_v2.py                 # all p, five folds, three seeds
    python l5_mapterm_v2.py --ps 8 128 --seeds 42
Writes results/l5_mapterm_v2.json.
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

from l5_bottleneck_v2 import PS, SEEDS, load_c_light, nrmse_per_sample
from v2_common import assert_disjoint, load_folds, write_atomic

OUT = "results/l5_mapterm_v2.json"


def low_priority():
    try:
        import psutil
        p = psutil.Process()
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 10)
    except Exception:
        pass


def cell(X, Pz, fit_idx, eval_idx, p, seed):
    assert_disjoint(fit_idx, eval_idx, f"POD basis (p={p}, seed={seed})")
    pca = PCA(n_components=p, svd_solver="randomized", random_state=0).fit(X[fit_idx])
    A = pca.transform(X)
    rng = X.max(1) - X.min(1)
    proj = pca.inverse_transform(A)

    def nr(diff):
        return np.sqrt((diff ** 2).mean(1)) / np.maximum(rng, 1e-12)

    out = {"floor": nr(proj - X)[eval_idx]}
    amu, asd = A[fit_idx].mean(0), A[fit_idx].std(0)
    asd[asd == 0] = 1.0
    Az = (A - amu) / asd
    preds = {"ridge": RidgeCV(alphas=np.logspace(-4, 4, 25)).fit(Pz[fit_idx], Az[fit_idx]).predict(Pz)}
    gb = np.zeros_like(Az)
    for k in range(p):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          early_stopping=True, random_state=seed)
        m.fit(Pz[fit_idx], Az[fit_idx, k])
        gb[:, k] = m.predict(Pz)
    preds["hgb"] = gb
    for name, Azp in preds.items():
        rec = pca.inverse_transform(Azp * asd + amu)
        out[f"map_{name}"] = nr(rec - proj)[eval_idx]
        out[f"total_{name}"] = nr(rec - X)[eval_idx]
        # orthogonality check: total^2 = floor^2 + map^2 per sample (float32 data)
        gap = np.abs(out[f"total_{name}"] ** 2 - out["floor"] ** 2 - out[f"map_{name}"] ** 2)
        scale = np.maximum(out[f"total_{name}"] ** 2, 1e-12)
        if float((gap / scale).max()) > 1e-3:
            raise AssertionError(f"p={p} {name}: Pythagoras fails by {float((gap / scale).max()):.2e}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ps", type=int, nargs="+", default=list(PS))
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    low_priority()

    X, params, mat = load_c_light()
    fold_of, n_folds, fold_seed = load_folds(mat)
    res = json.load(open(args.out)) if os.path.exists(args.out) else {}
    res.update({"_what": __doc__.split("\n\n")[0], "n_folds": n_folds, "fold_seed": fold_seed,
                "seeds": list(args.seeds), "ps": list(args.ps), "n_samples": int(X.shape[0])})
    res.setdefault("cells", {})

    for p in args.ps:
        for f in range(n_folds):
            fit_idx = np.where(fold_of != f)[0]
            ev_idx = np.where(fold_of == f)[0]
            mu, sd = params[fit_idx].mean(0), params[fit_idx].std(0)
            sd[sd == 0] = 1.0
            Pz = (params - mu) / sd
            for seed in args.seeds:
                key = f"p{p}/f{f}/s{seed}"
                if key in res["cells"]:
                    continue
                t1 = time.time()
                o = cell(X, Pz, fit_idx, ev_idx, p, seed)
                res["cells"][key] = {"p": p, "fold": f, "seed": seed,
                                     "material_ids": mat[ev_idx].tolist(),
                                     **{k: [float(x) for x in v] for k, v in o.items()},
                                     "secs": time.time() - t1}
                write_atomic(res, args.out)
                print(f"  p={p:>4} f{f} s{seed}: floor {o['floor'].mean():.5f}  "
                      f"map hgb {o['map_hgb'].mean():.5f} ridge {o['map_ridge'].mean():.5f}  "
                      f"[{time.time() - t1:.0f}s]", flush=True)

    res["summary"] = {}
    for p in args.ps:
        cs = [c for c in res["cells"].values() if c["p"] == p and c["seed"] in args.seeds]
        if len(cs) < n_folds * len(args.seeds):
            continue
        s = {}
        for term in ("floor", "map_hgb", "map_ridge", "total_hgb", "total_ridge"):
            pooled = np.concatenate([np.mean([c[term] for c in cs if c["fold"] == f], axis=0)
                                     for f in range(n_folds)])
            s[term] = float(pooled.mean())
        s["map_over_floor_hgb"] = s["map_hgb"] / s["floor"]
        s["map_over_floor_ridge"] = s["map_ridge"] / s["floor"]
        res["summary"][str(p)] = s
        print(f"[pooled] p={p:>4} floor {s['floor']:.5f}  map(hgb) {s['map_hgb']:.5f} "
              f"({s['map_over_floor_hgb']:.1f}x floor)  map(ridge) {s['map_ridge']:.5f}")
    write_atomic(res, args.out)


if __name__ == "__main__":
    main()
