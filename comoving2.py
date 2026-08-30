"""A TWO-parameter warp: align both waves, not one.

`comoving.py` refuted single-front alignment and, in doing so, named its
successor. The measurement that killed it: at the outlet the separation between
the fast Henry wave and the cooperative shock, t(0.9) - t(0.1), spans
[0.025, 0.992] normalised time — a **40x range** across the dataset. A single
shift aligns one wave exactly and lets the other scatter by that much, which is
why the warped n-width came out WORSE than doing nothing (31 -> 102 modes for
99.9 %).

So use two shifts. For each axial position take the arrival times of both waves
and normalise the interval between them onto a common coordinate:

    t_lo(z) = time at which c(z, t) crosses L_lo     (the Henry wave)
    t_hi(z) = time at which c(z, t) crosses L_hi     (the shock, complete)
    sigma   = (t - t_lo(z)) / (t_hi(z) - t_lo(z))

    C(z, sigma) = c(z, t_lo + sigma * (t_hi - t_lo))

This removes BOTH the arrival time and the transition width. If the breakthrough
is self-similar once those two are factored out, C collapses towards a universal
curve and the rank falls. If it does not, the two-wave structure is not a
similarity solution and nonlinear reconstruction by warping is finished as a
direction for this system — which is itself a decisive answer.

Scored exactly as `comoving.py` and `l5_bottleneck.py`: L5's 128x128 encoding,
L5's nRMSE normalisation, shape basis swept as L5 swept p, the interpolation floor
measured so it cannot manufacture a negative, and an oracle 2x2 so the total is
attributed rather than asserted.

Reference points, same encoding and same regressor:
    fixed frame (L5)              0.0510
    best single warp (comoving)   0.0612   (worse)

Output: results/comoving2.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA

from comoving import (L5_FIXED_FRAME, arrival_time, load_c_light, nrmse,
                      pca_regress, spectrum)

N_SIG = 512
SIG_LO, SIG_HI = -1.5, 2.5     # covers well before the Henry wave and after the shock
PAIRS = ((0.10, 0.90), (0.05, 0.95), (0.20, 0.80))
PS = (8, 16, 32, 64, 128)
P_WARP = 8
SINGLE_WARP_BEST = 0.0612      # comoving.py, level 0.1, p=64


def warp2(X, u, t_lo, t_hi, sig):
    """C(z, sigma) = c(z, t_lo + sigma * (t_hi - t_lo))."""
    N, NZ, _ = X.shape
    W = np.empty((N, NZ, len(sig)), dtype=np.float32)
    for n in range(N):
        for z in range(NZ):
            span = t_hi[n, z] - t_lo[n, z]
            W[n, z] = np.interp(t_lo[n, z] + sig * span, u, X[n, z])
    return W


def unwarp2(W, u, t_lo, t_hi, sig):
    """Inverse: c(z, t) = C(z, (t - t_lo) / (t_hi - t_lo))."""
    N, NZ, _ = W.shape
    Y = np.empty((N, NZ, len(u)), dtype=np.float32)
    for n in range(N):
        for z in range(NZ):
            span = t_hi[n, z] - t_lo[n, z]
            Y[n, z] = np.interp((u - t_lo[n, z]) / span, sig, W[n, z])
    return Y


def main():
    t0 = time.time()
    X, Pz, mat, split = load_c_light()
    tr = np.where(split == "train")[0]
    nm = np.where(split == "novel_material")[0]
    N, NZ, NT = X.shape
    u = np.linspace(0.0, 1.0, NT)
    sig = np.linspace(SIG_LO, SIG_HI, N_SIG)

    sp0 = spectrum(X, tr)
    print(f"\nn-width, original frame: {sp0}")
    print(f"reference  fixed frame {L5_FIXED_FRAME:.4f} | "
          f"best single warp {SINGLE_WARP_BEST:.4f}")

    out = {"n_sig": N_SIG, "sig_lo": SIG_LO, "sig_hi": SIG_HI,
           "pairs": [list(p) for p in PAIRS], "ps": list(PS), "p_warp": P_WARP,
           "l5_fixed_frame_reference": L5_FIXED_FRAME,
           "single_warp_best": SINGLE_WARP_BEST,
           "spectrum_original": sp0, "material_ids_novel": mat[nm].tolist(),
           "pairs_detail": {}}

    best = None
    for lo, hi in PAIRS:
        tag = f"{lo:.2f}-{hi:.2f}"
        print(f"\n{'=' * 74}\nLEVEL PAIR  c = {lo} -> {hi}\n{'=' * 74}")
        t_lo, bad_lo = arrival_time(X, u, lo)
        t_hi, bad_hi = arrival_time(X, u, hi)

        span = t_hi - t_lo
        # A degenerate span would divide by ~0 and manufacture nonsense (trap 2).
        print(f"   transition width span: min {span.min():.5f}  "
              f"median {np.median(span):.4f}  max {span.max():.4f}")
        if span.min() <= 1e-6:
            n_deg = int((span <= 1e-6).sum())
            print(f"   {n_deg} degenerate spans clamped to 1e-3 "
                  f"({100.0 * n_deg / span.size:.3f} % of (sample, z) pairs)")
            span = np.maximum(span, 1e-3)
            t_hi = t_lo + span

        W = warp2(X, u, t_lo, t_hi, sig)
        floor = nrmse(unwarp2(W, u, t_lo, t_hi, sig), X)[nm].mean()
        print(f"   interpolation floor (oracle warp + oracle shape): {floor:.6f}")
        contaminated = floor > 0.1 * L5_FIXED_FRAME
        if contaminated:
            print("   WARNING: floor >10 % of the reference — result contaminated")

        sp = spectrum(W, tr)
        print(f"   n-width here: {sp}")
        print(f"   original    : {sp0}")
        verdict = "BETTER" if sp["0.999"] < sp0["0.999"] else "WORSE OR EQUAL"
        print(f"   -> rank for 99.9 %: {sp['0.999']} vs {sp0['0.999']}  ({verdict})")

        # Both warp curves must be predicted from parameters, so both cost error.
        _, lo_pred = pca_regress(Pz, t_lo[:, :, None], tr, P_WARP)
        _, hi_pred = pca_regress(Pz, t_hi[:, :, None], tr, P_WARP)
        lo_pred, hi_pred = lo_pred[:, :, 0], hi_pred[:, :, 0]
        hi_pred = np.maximum(hi_pred, lo_pred + 1e-3)          # keep the span positive
        r2 = {}
        for nm_, a, b in (("t_lo", lo_pred, t_lo), ("t_hi", hi_pred, t_hi)):
            r2[nm_] = float(1.0 - ((a[nm] - b[nm]) ** 2).sum()
                            / max(((b[nm] - b[nm].mean()) ** 2).sum(), 1e-30))
        print(f"   warp R² on novel materials: t_lo {r2['t_lo']:+.3f}  "
              f"t_hi {r2['t_hi']:+.3f}")

        rows = []
        print(f"   {'p':>5} {'oracle warp':>13} {'pred warp':>11}   (novel materials)")
        for p in PS:
            _, shp_p = pca_regress(Pz, W, tr, p)
            e_ow = nrmse(unwarp2(shp_p, u, t_lo, t_hi, sig), X)[nm]
            e_pw = nrmse(unwarp2(shp_p, u, lo_pred, hi_pred, sig), X)[nm]
            rows.append({"p": p, "oracle_warp_pred_shape": float(e_ow.mean()),
                         "pred_warp_pred_shape": float(e_pw.mean()),
                         "per_sample_novel": [float(v) for v in e_pw]})
            print(f"   {p:>5} {e_ow.mean():>13.5f} {e_pw.mean():>11.5f}")
            if not contaminated and (best is None or e_pw.mean() < best[0]):
                best = (float(e_pw.mean()), tag, p)

        out["pairs_detail"][tag] = {
            "interp_floor": float(floor), "contaminated": bool(contaminated),
            "spectrum": sp, "warp_r2_novel": r2, "rows": rows,
            "span_min": float(span.min()), "span_median": float(np.median(span))}

    print(f"\n{'=' * 74}\nVERDICT\n{'=' * 74}")
    if best is None:
        print("   every level pair was contaminated by its interpolation floor")
    else:
        print(f"   best two-wave warp: {best[0]:.4f}  (levels {best[1]}, p = {best[2]})")
        print(f"   best single warp  : {SINGLE_WARP_BEST:.4f}")
        print(f"   fixed frame (L5)  : {L5_FIXED_FRAME:.4f}")
        r = L5_FIXED_FRAME / best[0]
        print(f"   two-wave vs fixed frame: {r:.2f}x — "
              f"{'BETTER' if r > 1 else 'WORSE OR EQUAL'}")
        out["best"] = {"nrmse": best[0], "levels": best[1], "p": best[2],
                       "ratio_vs_fixed_frame": r,
                       "ratio_vs_single_warp": SINGLE_WARP_BEST / best[0]}

    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/comoving2.json", "w"), indent=2)
    print(f"\nwrote results/comoving2.json  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
