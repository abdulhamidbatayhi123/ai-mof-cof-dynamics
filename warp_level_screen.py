"""PREREG_WARP_v2 Stage 1 -- the landmark screen. No reconstruction, no warp outcome.

For every candidate (L_lo, L_hi) and every fold, on that fold's FIT materials only:
  G1 resolution       sd of t_L over (sample, z) >= 4/(NT-1)             (both levels)
  G2 boundary mass    fraction of cells with t_L <= 2/(NT-1) < 0.20       (both levels)
  G3 no fabrication   n_bad == 0 -- no cell that never crosses the level  (both levels)
  G4 span             min(t_hi - t_lo) > 2/(NT-1), clamps counted, none applied
  G5 ceiling          eta^2, the between-material share of the variance of each
                      landmark (reported; the stage-2 pre-check uses it)
Selection (frozen in the prereg): the LOWEST L_lo passing G1-G4 on every fold, with
the LOWEST passing L_hi. Output: results/warp_level_screen.json, committed before
stage 2 is built.

    python warp_level_screen.py
"""
import json
import time

import numpy as np

from comoving import arrival_time
from learning_curve_v2 import load_c_channel
from v2_common import FIELD_RES, ROOT_V2, load_folds

LOS = (0.10, 0.20, 0.30, 0.40, 0.50)
HIS = (0.90, 0.95)


def eta2(t, mats):
    """Between-material share of the variance of t (over all its cells)."""
    t = t.reshape(len(mats), -1)
    grand = t.mean()
    total = ((t - grand) ** 2).sum()
    between = 0.0
    for m in np.unique(mats):
        rows = t[mats == m]
        between += rows.size * (rows.mean() - grand) ** 2
    return float(between / total) if total > 0 else float("nan")


def main():
    t0 = time.time()
    X, params, mat, cond, split = load_c_channel(ROOT_V2, FIELD_RES)
    fold_of, n_folds, fold_seed = load_folds(mat)
    N, NZ, NT = X.shape
    u = np.linspace(0.0, 1.0, NT)
    q1, q2 = 4.0 / (NT - 1), 2.0 / (NT - 1)
    arrivals, never_mask = {}, {}
    for L in LOS + HIS:
        arrivals[L] = arrival_time(X, u, L)
        # the exact never-crossed mask (arrival_time fabricates those cells at u[-1]; a
        # genuine crossing at the last sample also reads u[-1], so t == 1 cannot tell them apart)
        never_mask[L] = ~(X >= L).any(axis=2)
        print(f"level {L:.2f}: never-crossed {arrivals[L][1]}  [{time.time() - t0:.0f}s]", flush=True)
    del X
    out = {"_note": "PREREG_WARP_v2 stage 1; guards on FIT materials per fold", "NT": NT,
           "g1_min_sd": q1, "g2_quantum": q2, "levels": {}, "pairs": {}}
    for L in LOS + HIS:
        t, _ = arrivals[L]
        per = {}
        for f in range(n_folds):
            fit = fold_of != f
            tf = t[fit]
            never = int(never_mask[L][fit].sum())
            per[f] = {"sd": float(tf.std()), "boundary_frac": float(np.mean(tf <= q2)),
                      "never_crossed": never, "eta2": eta2(tf, mat[fit]),
                      "G1": bool(tf.std() >= q1), "G2": bool(np.mean(tf <= q2) < 0.20),
                      "G3": bool(never == 0)}
        out["levels"][f"{L:.2f}"] = per
    chosen = None
    for lo in LOS:
        for hi in HIS:
            ok_all, rows = True, {}
            for f in range(n_folds):
                fit = fold_of != f
                span = arrivals[hi][0][fit] - arrivals[lo][0][fit]
                g4 = bool(span.min() > q2)
                lv_lo, lv_hi = out["levels"][f"{lo:.2f}"][f], out["levels"][f"{hi:.2f}"][f]
                passes = all([lv_lo["G1"], lv_lo["G2"], lv_lo["G3"], lv_hi["G1"], lv_hi["G2"],
                              lv_hi["G3"], g4])
                rows[f] = {"span_min": float(span.min()), "span_clamps_needed": int((span <= q2).sum()),
                           "G4": g4, "passes": passes}
                ok_all &= passes
            out["pairs"][f"{lo:.2f}-{hi:.2f}"] = {"per_fold": rows, "passes_all_folds": ok_all}
            if ok_all and chosen is None:
                chosen = (lo, hi)
    out["selected"] = (None if chosen is None else {"L_lo": chosen[0], "L_hi": chosen[1]})
    out["selected_words"] = ("no absolute pair passes: fall back to Option B, then C (PREREG §2)"
                             if chosen is None else f"selected ({chosen[0]:.2f}, {chosen[1]:.2f})")
    json.dump(out, open("results/warp_level_screen.json", "w"), indent=2)
    print(out["selected_words"], f"[{time.time() - t0:.0f}s]")
    for k, v in out["pairs"].items():
        print(f"  {k}: passes all folds = {v['passes_all_folds']}")


if __name__ == "__main__":
    main()
