"""Is the front predictor's error partly a violated CONSTRAINT it was never told about?

`warp_verdict.py` establishes the target: given the true front trajectories the
two-wave frame is 2.27x better than the fixed frame (CI [+0.0199, +0.0367]), and
with predicted trajectories the whole gain disappears. The obstruction is the
prediction of two smooth 1-D curves, at R2 ~ 0.85-0.88 (lower) and 0.91-0.92
(upper).

Those curves are not arbitrary functions. Physically:

    t_lo(z) and t_hi(z) are MONOTONE NON-DECREASING in z
        — the front cannot arrive at a deeper point before a shallower one, in a
          single-pass column with no backflow.
    t_hi(z) > t_lo(z) everywhere
        — the 95 % crossing cannot precede the 5 % crossing.

The current predictor is a per-mode HistGradientBoostingRegressor on POD
coefficients of the curves. Nothing in that pipeline knows either constraint: POD
modes are not monotone, and a regression on their coefficients can reconstruct a
curve that doubles back. L4b already measured, on the fields, that imposing a
known physical bound ARCHITECTURALLY was worth 11.5x while imposing it as a
penalty was worth nothing — this asks whether the same lesson applies to the warp.

Cheap decisive test before building a differentiable warp with a monotone network:

  1. MEASURE the violation. What fraction of predicted trajectories are
     non-monotone, by how much, and does the violation correlate with error?
  2. PROJECT onto the constraint set, post hoc, with isotonic regression, and
     re-score. Free, requires no retraining.
  3. Report whether the projection moves the reconstruction error at all.

If the projection buys a real improvement, a monotone-by-construction predictor is
worth building and this says so with a number. If it buys nothing, monotonicity is
not the binding constraint and the effort belongs elsewhere -- which is equally
worth knowing before spending it.

Output: results/warp_monotone.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.isotonic import IsotonicRegression

from comoving import arrival_time, load_c_light, nrmse
from comoving2 import N_SIG, SIG_HI, SIG_LO, unwarp2, warp2
from metrics import ALPHA_CALIBRATED, ArmResult, compare

LEVELS = (0.05, 0.95)
P_SHAPE = 32
P_WARP = 4
SEEDS = (42, 43, 44)


def pod_hgb(target, Pz, tr, n_comp, seed):
    flat = target.reshape(target.shape[0], -1)
    n_comp = min(n_comp, len(tr) - 1, flat.shape[1])
    pca = PCA(n_components=n_comp, svd_solver="randomized", random_state=seed).fit(flat[tr])
    A = pca.transform(flat)
    mu, sd = A[tr].mean(0), A[tr].std(0)
    sd[sd == 0] = 1.0
    Az = (A - mu) / sd
    P = np.empty_like(Az)
    for k in range(n_comp):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          early_stopping=True, random_state=seed)
        m.fit(Pz[tr], Az[tr, k])
        P[:, k] = m.predict(Pz)
    return pca.inverse_transform(P * sd + mu).reshape(target.shape)


def monotone_stats(T):
    """Per-sample: does t(z) ever decrease, and by how much relative to its range?"""
    d = np.diff(T, axis=1)
    viol = (d < 0)
    frac_samples = float(viol.any(axis=1).mean())
    rng = np.maximum(T.max(1) - T.min(1), 1e-12)
    worst = np.abs(np.minimum(d, 0.0)).sum(1) / rng          # total backtrack / range
    return frac_samples, worst


def project_monotone(T):
    """Isotonic projection of each trajectory onto non-decreasing functions of z."""
    z = np.arange(T.shape[1])
    out = np.empty_like(T)
    for i in range(T.shape[0]):
        out[i] = IsotonicRegression(increasing=True).fit_transform(z, T[i])
    return out


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
    sig = np.linspace(SIG_LO, SIG_HI, N_SIG)

    lo, hi = LEVELS
    t_lo, _ = arrival_time(X, u, lo)
    t_hi, _ = arrival_time(X, u, hi)
    span = np.maximum(t_hi - t_lo, 1e-3)
    t_hi = t_lo + span

    fr_true_lo, _ = monotone_stats(t_lo)
    fr_true_hi, _ = monotone_stats(t_hi)
    print(f"\nTRUE trajectories: non-monotone in {fr_true_lo:.1%} (lo) and "
          f"{fr_true_hi:.1%} (hi) of samples — the reference itself is not perfectly\n"
          f"monotone because arrival_time reads a discrete grid, so this is the floor.")

    out = {"levels": list(LEVELS), "seeds": list(SEEDS),
           "true_nonmonotone_frac": {"lo": fr_true_lo, "hi": fr_true_hi},
           "per_seed": []}
    err_raw, err_proj = [], []

    for seed in SEEDS:
        lo_p = pod_hgb(t_lo, Pz, tr, P_WARP, seed)
        lg_p = pod_hgb(np.log(span), Pz, tr, P_WARP, seed)
        hi_p = lo_p + np.maximum(np.exp(lg_p), 1e-3)

        f_lo, w_lo = monotone_stats(lo_p)
        f_hi, w_hi = monotone_stats(hi_p)

        # raw
        W = warp2(X, u, lo_p, hi_p, sig)
        sh = pod_hgb(W, Pz, tr, P_SHAPE, seed)
        e_raw = nrmse(unwarp2(sh, u, lo_p, hi_p, sig), X)

        # projected onto the constraint set
        lo_m = project_monotone(lo_p)
        hi_m = np.maximum(project_monotone(hi_p), lo_m + 1e-3)
        Wm = warp2(X, u, lo_m, hi_m, sig)
        shm = pod_hgb(Wm, Pz, tr, P_SHAPE, seed)
        e_proj = nrmse(unwarp2(shm, u, lo_m, hi_m, sig), X)

        err_raw.append(e_raw[nm]); err_proj.append(e_proj[nm])
        rec = {
            "seed": seed,
            "nonmonotone_frac": {"lo": f_lo, "hi": f_hi},
            "backtrack_over_range": {"lo_median": float(np.median(w_lo[nm])),
                                     "hi_median": float(np.median(w_hi[nm])),
                                     "lo_p95": float(np.percentile(w_lo[nm], 95))},
            "r2_raw": {"lo": r2(lo_p, t_lo, nm), "hi": r2(hi_p, t_hi, nm)},
            "r2_proj": {"lo": r2(lo_m, t_lo, nm), "hi": r2(hi_m, t_hi, nm)},
            "nrmse_raw": float(e_raw[nm].mean()),
            "nrmse_proj": float(e_proj[nm].mean()),
        }
        out["per_seed"].append(rec)
        print(f"  seed {seed}: non-monotone lo {f_lo:5.1%} hi {f_hi:5.1%} | "
              f"R2 lo {rec['r2_raw']['lo']:+.3f}->{rec['r2_proj']['lo']:+.3f} "
              f"hi {rec['r2_raw']['hi']:+.3f}->{rec['r2_proj']['hi']:+.3f} | "
              f"nRMSE {rec['nrmse_raw']:.5f} -> {rec['nrmse_proj']:.5f} "
              f"[{time.time()-t0:.0f}s]", flush=True)

    mids = np.concatenate([mat[nm]] * len(SEEDS))
    a = ArmResult("raw", mids, np.concatenate(err_raw))
    b = ArmResult("isotonic", mids, np.concatenate(err_proj))
    r = compare(a, b)
    print(f"\nPaired, cluster-robust, alpha = {ALPHA_CALIBRATED}:")
    print(f"  raw {r['mean_a']:.5f} vs isotonic {r['mean_b']:.5f} | "
          f"diff {r['mean_diff']:+.5f} CI [{r['ci_low']:+.5f}, {r['ci_high']:+.5f}]"
          f"  {'SIGNIFICANT' if r['significant'] else 'NO DIFFERENCE'}")
    out["comparison"] = r
    if r["significant"] and r["mean_diff"] > 0:
        out["verdict"] = ("Enforcing monotonicity improves the reconstruction. A "
                          "monotone-by-construction front predictor is worth building.")
    elif r["significant"]:
        out["verdict"] = ("Isotonic projection makes it WORSE — the unconstrained "
                          "predictor is exploiting non-monotonicity to fit something real.")
    else:
        out["verdict"] = ("No difference. Monotonicity is not the binding constraint on "
                          "the front predictor; the remaining 2.17x is elsewhere.")
    print(f"  -> {out['verdict']}")

    os.makedirs("results", exist_ok=True)
    with open("results/warp_monotone.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote results/warp_monotone.json  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
