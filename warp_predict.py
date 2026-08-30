"""How accurately must the two fronts be located, and can we locate them?

`comoving2.py` found the right representation and an unrealised gain:

    two-wave frame, ORACLE warp     0.0203     <- beats DeepONet's 0.0281
    two-wave frame, PREDICTED warp  0.0514     <- ties the fixed frame's 0.0510

The frame cuts the reconstruction error 2.5x and the rank 2.4x (31 -> 13 modes for
99.9 %). Every bit of that is then given back by the error in predicting the two
warp curves, whose R2 was only 0.81-0.92. So the ladder's obstruction has MOVED:
it is no longer "the coefficients are unpredictable" but "the front trajectories
are not located accurately enough".

That is a much better-posed problem — two smooth monotone 1-D curves instead of a
2-D field — and this script asks the two questions that decide whether it is
worth pursuing.

**(1) How good does the warp have to be?** Blend the predicted warp toward the
true one and trace the reconstruction error. This is the payoff curve: it converts
"warp R2" into "nRMSE you would actually get", so a future front-locating model
has a target rather than a hope.

**(2) How good can we make it cheaply?** Sweep the parameterisation, the number of
warp modes and the regressor. Two parameterisations are compared because they are
not equivalent numerically: predicting (t_lo, t_hi) treats two correlated curves
independently, while predicting (t_lo, log span) separates *where* the transition
starts from *how wide* it is — and the span varies 40x, so its log is the better
conditioned target.

Everything reuses `comoving.py` / `comoving2.py` machinery so the encoding, the
normalisation and the interpolation-floor self-check are identical.

Output: results/warp_predict.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV

from comoving import L5_FIXED_FRAME, arrival_time, load_c_light, nrmse
from comoving2 import SIG_HI, SIG_LO, N_SIG, unwarp2, warp2

LEVELS = (0.05, 0.95)          # the best-ranked pair in comoving2
P_SHAPE = 128                  # shape is not the bottleneck here; use the best
P_WARPS = (4, 8, 16, 32)
ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)
ORACLE_REF = 0.0203            # comoving2, oracle warp
SINGLE_WARP = 0.0612


def curves_to_modes(C, tr, n_comp):
    """PCA a set of smooth curves and return (pca, standardised coefficients)."""
    pca = PCA(n_components=min(n_comp, C.shape[1]),
              svd_solver="randomized", random_state=0).fit(C[tr])
    A = pca.transform(C)
    mu, sd = A[tr].mean(0), A[tr].std(0)
    sd[sd == 0] = 1.0
    return pca, A, mu, sd


def regress(Pz, A, mu, sd, tr, kind):
    """Predict standardised coefficients from parameters."""
    Az = (A - mu) / sd
    P = np.empty_like(Az)
    if kind == "ridge":
        m = RidgeCV(alphas=np.logspace(-4, 4, 25)).fit(Pz[tr], Az[tr])
        P = m.predict(Pz)
    else:
        for k in range(Az.shape[1]):
            m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                              early_stopping=True, random_state=0)
            m.fit(Pz[tr], Az[tr, k])
            P[:, k] = m.predict(Pz)
    return P * sd + mu


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
    print(f"\nlevels {lo} -> {hi};  span median {np.median(span):.4f}, "
          f"range {span.min():.5f}-{span.max():.4f} ({span.max() / span.min():.0f}x)")

    W = warp2(X, u, t_lo, t_hi, sig)
    floor = nrmse(unwarp2(W, u, t_lo, t_hi, sig), X)[nm].mean()
    print(f"interpolation floor: {floor:.6f}")

    # Shape is fixed at its best; this study is about the warp alone.
    flat = W.reshape(N, -1)
    pca_s = PCA(n_components=P_SHAPE, svd_solver="randomized", random_state=0).fit(flat[tr])
    A = pca_s.transform(flat)
    smu, ssd = A[tr].mean(0), A[tr].std(0)
    ssd[ssd == 0] = 1.0
    Az = (A - smu) / ssd
    Ps = np.empty_like(Az)
    for k in range(P_SHAPE):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          early_stopping=True, random_state=0)
        m.fit(Pz[tr], Az[tr, k])
        Ps[:, k] = m.predict(Pz)
    shape_pred = pca_s.inverse_transform(Ps * ssd + smu).reshape(W.shape)
    print(f"shape basis fixed at p={P_SHAPE} (predicted)")

    out = {"levels": list(LEVELS), "p_shape": P_SHAPE, "p_warps": list(P_WARPS),
           "interp_floor": float(floor), "oracle_reference": ORACLE_REF,
           "l5_fixed_frame_reference": L5_FIXED_FRAME,
           "single_warp_reference": SINGLE_WARP,
           "material_ids_novel": mat[nm].tolist(), "sweep": []}

    print(f"\n{'=' * 78}\n1. CAN THE WARP BE PREDICTED BETTER?\n{'=' * 78}")
    print(f"  {'param':<14} {'modes':>6} {'reg':>7} {'R2(t_lo)':>9} {'R2(t_hi)':>9}")
    best = None
    for par in ("endpoints", "start_logspan"):
        for pw in P_WARPS:
            for kind in ("ridge", "hgb"):
                if par == "endpoints":
                    pa, Aa, mua, sda = curves_to_modes(t_lo, tr, pw)
                    pb, Ab, mub, sdb = curves_to_modes(t_hi, tr, pw)
                    lo_p = pa.inverse_transform(regress(Pz, Aa, mua, sda, tr, kind))
                    hi_p = pb.inverse_transform(regress(Pz, Ab, mub, sdb, tr, kind))
                else:
                    ls = np.log(span)
                    pa, Aa, mua, sda = curves_to_modes(t_lo, tr, pw)
                    pb, Ab, mub, sdb = curves_to_modes(ls, tr, pw)
                    lo_p = pa.inverse_transform(regress(Pz, Aa, mua, sda, tr, kind))
                    sp_p = np.exp(pb.inverse_transform(regress(Pz, Ab, mub, sdb, tr, kind)))
                    hi_p = lo_p + np.maximum(sp_p, 1e-3)
                hi_p = np.maximum(hi_p, lo_p + 1e-3)
                rl, rh = r2(lo_p, t_lo, nm), r2(hi_p, t_hi, nm)
                rec = {"param": par, "p_warp": pw, "regressor": kind,
                       "r2_t_lo": rl, "r2_t_hi": rh}
                out["sweep"].append(rec)
                print(f"  {par:<14} {pw:>6} {kind:>7} {rl:>+9.3f} {rh:>+9.3f}")
                score = rl + rh
                if best is None or score > best[0]:
                    best = (score, rec, lo_p, hi_p)

    _, brec, lo_b, hi_b = best
    print(f"\n  best warp predictor: {brec['param']}, {brec['p_warp']} modes, "
          f"{brec['regressor']}  (R2 {brec['r2_t_lo']:+.3f} / {brec['r2_t_hi']:+.3f})")

    print(f"\n{'=' * 78}\n2. THE PAYOFF CURVE — what warp accuracy is worth\n{'=' * 78}")
    print("  alpha = 1 is the predicted warp, alpha = 0 is the oracle warp.")
    print(f"  {'alpha':>6} {'R2(t_lo)':>9} {'R2(t_hi)':>9} {'nRMSE':>9}")
    curve = []
    for a in ALPHAS:
        lo_a = (1 - a) * t_lo + a * lo_b
        hi_a = np.maximum((1 - a) * t_hi + a * hi_b, lo_a + 1e-3)
        e = nrmse(unwarp2(shape_pred, u, lo_a, hi_a, sig), X)[nm]
        rl, rh = r2(lo_a, t_lo, nm), r2(hi_a, t_hi, nm)
        curve.append({"alpha": a, "r2_t_lo": rl, "r2_t_hi": rh,
                      "nrmse_novel": float(e.mean()),
                      "per_sample_novel": [float(v) for v in e]})
        print(f"  {a:>6.2f} {rl:>+9.3f} {rh:>+9.3f} {e.mean():>9.5f}")
    out["payoff_curve"] = curve

    print(f"\n{'=' * 78}\n3. VERDICT\n{'=' * 78}")
    got = curve[-1]["nrmse_novel"]
    orc = curve[0]["nrmse_novel"]
    print(f"  oracle warp                : {orc:.4f}")
    print(f"  best predicted warp        : {got:.4f}")
    print(f"  fixed frame (L5)           : {L5_FIXED_FRAME:.4f}")
    print(f"  headroom still on the table: {got / orc:.2f}x")
    if got < L5_FIXED_FRAME:
        print(f"  -> two-wave frame now BEATS the fixed frame "
              f"({L5_FIXED_FRAME / got:.2f}x)")
    else:
        print("  -> warp prediction still consumes the entire gain")
    out["verdict"] = {"oracle": orc, "predicted": got,
                      "headroom": got / orc,
                      "beats_fixed_frame": bool(got < L5_FIXED_FRAME)}

    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/warp_predict.json", "w"), indent=2)
    print(f"\nwrote results/warp_predict.json  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
