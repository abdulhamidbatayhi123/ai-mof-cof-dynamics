"""PREREG_WARP_v2 Stage 1, fallbacks (amendment A1): Options B and C under the SAME guards.

No absolute landmark pair passed on v2 (warp_level_screen.py). The prereg's fallbacks:

  Option B, self-normalised: per (sample, z) the Henry plateau c_p is c at the minimum
    |dc/dt| between the first crossing of 0.02 and the argmax of dc/dt; the landmarks
    are the first crossings of c_p + 0.10 (1 - c_p) and c_p + 0.90 (1 - c_p) -- they
    measure the shock, not the Henry toe.
  Option C, derivative pair: t_peak = argmax dc/dt (interval midpoint), w =
    (1 - c_p) / max dc/dt, landmarks t_peak -/+ w/2.

Guards, on each fold's FIT materials: G1 sd >= 4/(NT-1) (both landmarks); G2 fraction
<= 2/(NT-1) below 0.20 (both); G3 no never-crossed / undefined cells; G4 min span >
2/(NT-1), clamps counted. Selection: Option B if it passes on every fold, else Option C,
else the warp is NOT RUN on v2 (PREREG §2). Output: results/warp_level_screen_bc.json
"""
import json
import time

import numpy as np

from learning_curve_v2 import load_c_channel
from v2_common import FIELD_RES, ROOT_V2, load_folds


def first_crossing(X, level, u):
    """First upward crossing of a per-cell level (N, NZ), linearly interpolated.
    Returns (t, never) with never True where the level is not reached."""
    above = X >= level[..., None]
    never = ~above.any(axis=2)
    k = np.argmax(above, axis=2)
    km1 = np.maximum(k - 1, 0)
    c0 = np.take_along_axis(X, km1[..., None], 2)[..., 0]
    c1 = np.take_along_axis(X, k[..., None], 2)[..., 0]
    w = np.where(c1 > c0, (level - c0) / np.where(c1 > c0, c1 - c0, 1.0), 0.0)
    t = np.where(k == 0, u[0], u[km1] + w * (u[k] - u[km1]))
    return np.where(never, np.nan, t), never


def guards(t_lo, t_hi, undefined, fit, q1, q2):
    a, b = t_lo[fit], t_hi[fit]
    ok = ~undefined[fit]
    span = b[ok] - a[ok]
    g = {"n_undefined": int((~ok).sum()),
         "sd_lo": float(np.nanstd(a)), "sd_hi": float(np.nanstd(b)),
         "boundary_lo": float(np.nanmean(a <= q2)), "boundary_hi": float(np.nanmean(b <= q2)),
         "span_min": float(span.min()) if span.size else float("nan"),
         "span_clamps_needed": int((span <= q2).sum())}
    g["G1"] = g["sd_lo"] >= q1 and g["sd_hi"] >= q1
    g["G2"] = g["boundary_lo"] < 0.20 and g["boundary_hi"] < 0.20
    g["G3"] = g["n_undefined"] == 0
    g["G4"] = bool(span.size) and g["span_min"] > q2
    g["passes"] = bool(g["G1"] and g["G2"] and g["G3"] and g["G4"])
    return g


def main():
    t0 = time.time()
    X, params, mat, cond, split = load_c_channel(ROOT_V2, FIELD_RES)
    fold_of, n_folds, _ = load_folds(mat)
    N, NZ, NT = X.shape
    u = np.linspace(0.0, 1.0, NT)
    q1, q2 = 4.0 / (NT - 1), 2.0 / (NT - 1)
    du = u[1] - u[0]
    dc = np.diff(X, axis=2) / du                       # (N, NZ, NT-1), rate on interval j
    ipk = np.argmax(dc, axis=2)
    dmax = np.max(dc, axis=2)
    above02 = X >= 0.02
    i0 = np.where(above02.any(axis=2), np.argmax(above02, axis=2), NT - 1)
    j = np.arange(NT - 1)[None, None, :]
    # interval j spans samples j..j+1, so the interval that CARRIES c past 0.02 is
    # j = i0 - 1; the first version used j >= i0 and called 92 % of cells undefined
    lo_j = np.maximum(i0 - 1, 0)
    window = (j >= lo_j[..., None]) & (j <= ipk[..., None])
    absd = np.where(window, np.abs(dc), np.inf)
    jp = np.argmin(absd, axis=2)
    c_p = np.take_along_axis(X, jp[..., None], 2)[..., 0]
    bad_plateau = (~above02.any(axis=2)) | (ipk < lo_j) | (dmax <= 0)
    del absd, window
    print(f"plateau found; undefined cells {int(bad_plateau.sum())}  [{time.time() - t0:.0f}s]", flush=True)

    # Option B
    lo_lev = c_p + 0.10 * (1.0 - c_p)
    hi_lev = c_p + 0.90 * (1.0 - c_p)
    tB_lo, nv_lo = first_crossing(X, lo_lev, u)
    tB_hi, nv_hi = first_crossing(X, hi_lev, u)
    undefB = bad_plateau | nv_lo | nv_hi
    # Option C
    t_peak = u[ipk] + 0.5 * du
    width = np.where(dmax > 0, (1.0 - c_p) / np.where(dmax > 0, dmax, 1.0), np.nan)
    tC_lo, tC_hi = t_peak - width / 2, t_peak + width / 2
    undefC = bad_plateau | ~np.isfinite(width)
    del X, dc

    out = {"_note": "PREREG_WARP_v2 stage 1 fallbacks (A1); guards on FIT materials per fold",
           "NT": NT, "g1_min_sd": q1, "g2_quantum": q2,
           "c_p_summary": {"median": float(np.nanmedian(c_p)), "p05": float(np.nanpercentile(c_p, 5)),
                           "p95": float(np.nanpercentile(c_p, 95))},
           "B": {}, "C": {}}
    for f in range(n_folds):
        fit = fold_of != f
        out["B"][str(f)] = guards(tB_lo, tB_hi, undefB, fit, q1, q2)
        out["C"][str(f)] = guards(tC_lo, tC_hi, undefC, fit, q1, q2)
    passB = all(v["passes"] for v in out["B"].values())
    passC = all(v["passes"] for v in out["C"].values())
    out["selected"] = "B" if passB else ("C" if passC else None)
    out["selected_words"] = {"B": "Option B (self-normalised landmarks) selected",
                             "C": "Option C (derivative pair) selected",
                             None: "neither fallback passes: the warp is NOT RUN on v2 (PREREG §2)"}[out["selected"]]
    json.dump(out, open("results/warp_level_screen_bc.json", "w"), indent=2)
    print(out["selected_words"], f"[{time.time() - t0:.0f}s]")
    for opt in ("B", "C"):
        v = out[opt]["0"]
        print(f"  {opt} fold0: " + ", ".join(f"{k}={v[k]}" for k in ("G1", "G2", "G3", "G4", "n_undefined",
                                                                     "span_min", "boundary_lo", "sd_lo")))


if __name__ == "__main__":
    main()
