"""B-FIT (PREREG_BASELINES.md §3): the Klinkenberg form with two fitted corrections.

Owner of results/fitted_classical.json. L7 scores the closed forms with nothing
fitted. The fair classical competitor, declared before this was run, is the same
Klinkenberg form with its two physically interpretable inputs -- the chord Henry slope
K and the rate k_LDF -- each multiplied by a constant, exp(a) and exp(b), fitted per
fold by Nelder-Mead from (0, 0) on the fold's TRAINING samples (mean exit-curve nRMSE,
v2_common.exit_nrmse), then applied unchanged to that fold's held-out samples. Two
parameters per fold; no per-material fitting.

The vectorised form below must reproduce classical.klinkenberg exactly at (a, b) =
(0, 0); that is asserted on every sample before any fit.

Comparison and words (frozen in the prereg): fitted Klinkenberg vs the learned arm's
out-of-fold exit curve, paired exactly as analyze_l7_v2.py pairs them.

    python fitted_classical.py
"""
import json
import time

import numpy as np
from scipy.optimize import minimize
from scipy.special import erfc

from analyze_l1_v2 import pooled_folds
from classical import _stoich_time, klinkenberg
from fetch_real_mof_data import rh_to_conc
from mde import mde_report
from metrics import ArmResult, compare
from run_l4 import physics_from_params
from run_l7_v2 import load_exit_curves
from v2_common import FIELD_RES, ROOT_V2, alpha_for, load_folds

OUT = "results/fitted_classical.json"


def base_terms(phys, params, keys, t_final, NT):
    """Per-sample quantities of the Klinkenberg form that the two multipliers scale."""
    N = len(phys)
    k0, lam0, Lu = np.empty(N), np.empty(N), np.empty(N)
    t = np.empty((N, NT))
    t_norm = np.linspace(0.0, 1.0, NT)
    for i, p in enumerate(phys):
        c_in = rh_to_conc(params[i][keys.index("rh_feed")], p.T_in)
        u = p.v / p.eps_t
        _, q_eq = _stoich_time(p, c_in, p.T_in)
        K = q_eq / c_in
        k0[i] = p.k_LDF
        lam0[i] = (1 - p.eps_t) * p.rho_p * K / p.eps_t * p.L / u     # lam * L / u
        Lu[i] = p.L / u
        t[i] = t_norm * t_final[i]
    return k0, lam0, Lu, t


def predict(ab, k0, lam0, Lu, t):
    fK, fk = np.exp(ab[0]), np.exp(ab[1])
    xi = (k0 * fk * lam0 * fK)[:, None]
    tau = (k0 * fk)[:, None] * np.maximum(t - Lu[:, None], 0.0)
    sx = np.sqrt(np.maximum(xi, 1e-12))
    st = np.sqrt(np.maximum(tau, 1e-12))
    out = 0.5 * erfc(sx - st - 1.0 / (8.0 * sx) - 1.0 / (8.0 * st))
    return np.clip(np.where(tau > 0, out, 0.0), 0.0, 1.0)


def nrmse_rows(pred, truth):
    rng = truth.max(1) - truth.min(1)
    if np.any(rng < 0.05):
        raise ValueError("an exit curve has no breakthrough (range < 0.05); A15")
    return np.sqrt(np.mean((pred - truth) ** 2, axis=1)) / rng


def main():
    t0 = time.time()
    exits, params, mat, cond, split, t_final, k_man, keys, design = load_exit_curves(ROOT_V2, FIELD_RES)
    N, NT = exits.shape
    fold_of, n_folds, _ = load_folds(mat)
    phys = [physics_from_params(params[i], keys) for i in range(N)]
    k0, lam0, Lu, t = base_terms(phys, params, keys, t_final, NT)

    # the vectorised form IS classical.klinkenberg at (0, 0) -- asserted, not assumed
    p0 = predict((0.0, 0.0), k0, lam0, Lu, t)
    for i in range(N):
        c_in = rh_to_conc(params[i][keys.index("rh_feed")], phys[i].T_in)
        ref = klinkenberg(phys[i], c_in, phys[i].T_in, t[i])
        if not np.allclose(p0[i], ref, atol=1e-12):
            raise SystemExit(f"ABORT: vectorised Klinkenberg differs from classical.py on sample {i}")
    truth = exits.astype(np.float64)
    e0 = nrmse_rows(p0, truth)
    print(f"vectorised form reproduces classical.klinkenberg on all {N} samples; "
          f"unfitted mean exit nRMSE {e0.mean():.4f}  [{time.time() - t0:.0f}s]", flush=True)

    e_fit = np.empty(N)
    folds = {}
    for f in range(n_folds):
        tr, te = fold_of != f, fold_of == f
        obj = lambda ab: float(nrmse_rows(predict(ab, k0[tr], lam0[tr], Lu[tr], t[tr]), truth[tr]).mean())
        r = minimize(obj, np.zeros(2), method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-7, "maxiter": 400})
        e_fit[te] = nrmse_rows(predict(r.x, k0[te], lam0[te], Lu[te], t[te]), truth[te])
        folds[str(f)] = {"log_mult_K": float(r.x[0]), "log_mult_k": float(r.x[1]),
                         "train_nrmse": float(r.fun), "test_nrmse": float(e_fit[te].mean()),
                         "converged": bool(r.success)}
        print(f"  fold {f}: K x{np.exp(r.x[0]):.3f}, k x{np.exp(r.x[1]):.3f}; train {r.fun:.4f}, "
              f"held-out {e_fit[te].mean():.4f}", flush=True)

    # the learned arm's out-of-fold exit curve, exactly as analyze_l7_v2 pairs it
    l1 = json.load(open("results/l1_v2_results.json"))
    best = json.load(open("results/l1_v2_verdict.json"))["folds"]["best"]
    e, m, c = pooled_folds({"folds": l1["folds"]}, best, "per_sample_exit_nrmse")
    learned = {(int(mm), int(cc)): float(v) for v, mm, cc in zip(e, m, c)}
    e_l = np.array([learned[(int(a), int(b))] for a, b in zip(mat, cond)])
    alpha, _ = alpha_for("folds")
    r = compare(ArmResult(best, mat, e_l), ArmResult("klinkenberg_fitted", mat, e_fit), alpha=alpha, n_boot=4000)
    if r["significant"] and r["mean_diff"] < 0:
        words = f"learning remains justified against a fitted classical form ({e_fit.mean() / e_l.mean():.2f}x)"
        mde = None
    elif not r["significant"]:
        words = "a two-parameter fitted Klinkenberg form matches the learned arm on the exit curve"
        mde = mde_report(e_fit - e_l, mat, base=float(e_l.mean()), alpha=alpha, label="B-FIT vs learned")
    else:
        words = "the fitted Klinkenberg form is better than the learned arm on the exit curve"
        mde = None
    out = {"_what": __doc__.splitlines()[0], "alpha": alpha, "learned_reference": best,
           "unfitted_mean": float(e0.mean()), "fitted_mean": float(e_fit.mean()),
           "learned_mean": float(e_l.mean()), "ratio_fitted_over_learned": float(e_fit.mean() / e_l.mean()),
           "folds": folds, "comparison": r, "mde": mde, "words": words,
           "per_sample_fitted": e_fit.tolist(), "material_ids": mat.tolist(), "condition_ids": cond.tolist()}
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\n{words}\n  learned {e_l.mean():.4f}  fitted Klinkenberg {e_fit.mean():.4f}  "
          f"CI [{r['ci_low']:+.5f}, {r['ci_high']:+.5f}]")
    print(f"wrote {OUT}  [{time.time() - t0:.0f}s]")
    print("BFIT_DONE")


if __name__ == "__main__":
    main()
