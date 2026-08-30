"""Does more data help? L1 is recorded as eliminating that, and never measured it.

L1's rung is titled "you just need more data" and its verdict is **eliminated**.
Its audit swept the POD rank, the bootstrap calibration and the choice of held-out
split — but it never varied the TRAINING-SET SIZE. The verdict therefore rests on
a measurement that was not taken.

This became load-bearing once every map in the project turned out to saturate the
same way: field coefficients flat in basis size (L1 audit, l5_bottleneck, L5), and
now the two warp curves flat in warp modes and identical to four decimals across
parameterisations (warp_predict). A saturation that looks intrinsic and a
saturation caused by 691 training samples are indistinguishable until the learning
curve is measured.

Two axes, because they are different questions and the answers can differ:

  A. MORE MATERIALS  — more distinct (q_max, dH, kinetics, isotherm shape).
     This is the axis that novel-material transfer should care about.
  B. MORE CONDITIONS per material — denser sampling of operating space at a fixed
     set of materials. Should help interpolation, not transfer.

Targets measured at each size, since the project's bottleneck has moved:

  * novel-material nRMSE of POD + gradient boosting (the L5 fixed-frame arm)
  * R² of the two warp curves t_lo(z), t_hi(z) (the two-wave frame's bottleneck)

Encoding is L5's frozen 128x128 c-channel throughout, so these numbers are
comparable to `l5_bottleneck.py` and `warp_predict.py` and NOT to L1's own table
(different encoding, different arms) — this re-measures L1's *hypothesis*, not
L1's arms.

Output: results/learning_curve.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor

from comoving import arrival_time, load_c_light, nrmse

FRACS = (0.25, 0.50, 0.75, 1.00)
SEEDS = (42, 43, 44)
P_FIELD = 32                   # flat over 8..128, so any value in range represents it
P_WARP = 8
LEVELS = (0.05, 0.95)


def fit_score(Pz, target, tr_sub, nm, n_comp):
    """PCA + HGB on a subset; return predictions for everyone."""
    flat = target.reshape(target.shape[0], -1)
    n_comp = min(n_comp, len(tr_sub) - 1, flat.shape[1])
    pca = PCA(n_components=n_comp, svd_solver="randomized",
              random_state=0).fit(flat[tr_sub])
    A = pca.transform(flat)
    mu, sd = A[tr_sub].mean(0), A[tr_sub].std(0)
    sd[sd == 0] = 1.0
    Az = (A - mu) / sd
    P = np.empty_like(Az)
    for k in range(n_comp):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          early_stopping=True, random_state=0)
        m.fit(Pz[tr_sub], Az[tr_sub, k])
        P[:, k] = m.predict(Pz)
    return pca.inverse_transform(P * sd + mu).reshape(target.shape)


def r2(pred, true, idx):
    return float(1.0 - ((pred[idx] - true[idx]) ** 2).sum()
                 / max(((true[idx] - true[idx].mean()) ** 2).sum(), 1e-30))


def main():
    t0 = time.time()
    X, Pz, mat, split = load_c_light()
    tr = np.where(split == "train")[0]
    nm = np.where(split == "novel_material")[0]
    N, NZ, NT = X.shape
    u = np.linspace(0.0, 1.0, NT)

    t_lo, _ = arrival_time(X, u, LEVELS[0])
    t_hi, _ = arrival_time(X, u, LEVELS[1])
    t_hi = t_lo + np.maximum(t_hi - t_lo, 1e-3)

    tr_mats = np.unique(mat[tr])
    print(f"\ntrain: {len(tr)} conditions over {len(tr_mats)} materials")
    print(f"novel-material: {len(nm)} conditions over {len(np.unique(mat[nm]))} materials")

    out = {"fracs": list(FRACS), "seeds": list(SEEDS), "p_field": P_FIELD,
           "p_warp": P_WARP, "levels": list(LEVELS),
           "n_train_conditions": int(len(tr)), "n_train_materials": int(len(tr_mats)),
           "material_ids_novel": mat[nm].tolist(), "axes": {}}

    for axis in ("materials", "conditions"):
        print(f"\n{'=' * 78}\nAXIS: more {axis}\n{'=' * 78}")
        print(f"  {'frac':>6} {'n_train':>8} {'n_mats':>7} "
              f"{'field nRMSE':>13} {'R2 t_lo':>9} {'R2 t_hi':>9}")
        rows = []
        for f in FRACS:
            per_seed = []
            for s in SEEDS:
                rng = np.random.default_rng(s)
                if axis == "materials":
                    k = max(2, int(round(f * len(tr_mats))))
                    keep = set(rng.choice(tr_mats, size=k, replace=False))
                    sub = np.array([i for i in tr if mat[i] in keep])
                else:
                    sub = []
                    for m in tr_mats:
                        idx = tr[mat[tr] == m]
                        k = max(1, int(round(f * len(idx))))
                        sub.extend(rng.choice(idx, size=k, replace=False))
                    sub = np.array(sorted(sub))
                if f == 1.00:
                    sub = tr                      # exact, not a resample
                fld = fit_score(Pz, X, sub, nm, P_FIELD)
                lo_p = fit_score(Pz, t_lo[:, :, None], sub, nm, P_WARP)[:, :, 0]
                hi_p = fit_score(Pz, t_hi[:, :, None], sub, nm, P_WARP)[:, :, 0]
                per_seed.append({
                    "seed": s, "n_train": int(len(sub)),
                    "n_materials": int(len(np.unique(mat[sub]))),
                    "field_nrmse": float(nrmse(fld, X)[nm].mean()),
                    "r2_t_lo": r2(lo_p, t_lo, nm), "r2_t_hi": r2(hi_p, t_hi, nm),
                    "per_sample_novel": [float(v) for v in nrmse(fld, X)[nm]]})
                if f == 1.00:
                    break                          # deterministic; one run suffices
            e = float(np.mean([p["field_nrmse"] for p in per_seed]))
            rl = float(np.mean([p["r2_t_lo"] for p in per_seed]))
            rh = float(np.mean([p["r2_t_hi"] for p in per_seed]))
            nt = int(np.mean([p["n_train"] for p in per_seed]))
            nmt = int(np.mean([p["n_materials"] for p in per_seed]))
            rows.append({"frac": f, "n_train": nt, "n_materials": nmt,
                         "field_nrmse": e, "r2_t_lo": rl, "r2_t_hi": rh,
                         "seeds": per_seed})
            print(f"  {f:>6.2f} {nt:>8} {nmt:>7} {e:>13.5f} {rl:>+9.3f} {rh:>+9.3f}")
        out["axes"][axis] = rows
        a, b = rows[0], rows[-1]
        print(f"  -> field error {a['field_nrmse']:.4f} -> {b['field_nrmse']:.4f} "
              f"({a['field_nrmse'] / b['field_nrmse']:.2f}x) as data goes "
              f"{a['n_train']} -> {b['n_train']}")

    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/learning_curve.json", "w"), indent=2)
    print(f"\nwrote results/learning_curve.json  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
