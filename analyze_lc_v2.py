"""The learning-curve verdict on dataset v2 — does the materials axis close?

Rules frozen in PREREG_L1L2L7_v2.md §2(b),(c):

  ELIMINATED      iff the last step (96 -> 192 materials) is NOT a significant
                  improvement in the honest (refit-basis) field nRMSE at the
                  calibrated alpha — reported with its MDE.
  NOT ELIMINATED  iff it is; then the power-law exponent beta in err ~ n^-beta is
                  reported with a bootstrap-over-materials CI, and nothing is
                  extrapolated beyond twice the measured range.

Also reported, per size: the fixed-basis curve, the number of coefficient-map
modes with R2 > 0.5 / > 0.2 (A21's measurement), and the R2 of the two front
trajectories (the warp bottleneck). Per-sample values are averaged over seeds;
folds are pooled (each sample once); clustering is by material.

    python analyze_lc_v2.py [--mde-trials 200]
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

from mde import mde_report
from metrics import ArmResult, compare, format_comparison
from v2_common import alpha_for

RES = "results/learning_curve_v2.json"
OUT = "results/learning_curve_v2_verdict.json"
MDE_EFFECTS = (0.0, 0.02, 0.05, 0.10, 0.20)


def pooled(res, axis, g, key, folds):
    """Seed-averaged per-sample held-out values, pooled over folds."""
    v, m = [], []
    for f in folds:
        cells = res["folds"][f][axis][str(g)]
        seeds = sorted(cells)
        vals = np.mean([np.asarray(cells[s][key], dtype=float) for s in seeds], axis=0)
        v.append(vals); m.append(np.asarray(res["folds"][f]["sizes"]["material_ids_test"]))
    return np.concatenate(v), np.concatenate(m)


def scalar_mean(res, axis, g, key, folds):
    vals = [res["folds"][f][axis][str(g)][s][key] for f in folds for s in res["folds"][f][axis][str(g)]]
    return float(np.mean(vals)), float(np.std(vals))


def mode_counts(res, axis, g, folds, thr):
    r2 = np.mean([res["folds"][f][axis][str(g)][s]["mode_r2"]
                  for f in folds for s in res["folds"][f][axis][str(g)]], axis=0)
    return int((r2 > thr).sum()), r2


def power_law(ns, errs):
    b, a = np.polyfit(np.log(ns), np.log(errs), 1)
    return float(-b), float(np.exp(a))


def bootstrap_exponent(res, axis, grid, folds, n_boot=2000, seed=0):
    """Resample MATERIALS, recompute each size's pooled mean, refit the exponent."""
    per_size = {g: pooled(res, axis, g, "per_sample_refit", folds) for g in grid}
    mats = np.unique(per_size[grid[0]][1])
    idx_by_mat = {m: np.where(per_size[grid[0]][1] == m)[0] for m in mats}
    for g in grid:                                   # same sample order at every size
        if not np.array_equal(per_size[g][1], per_size[grid[0]][1]):
            raise AssertionError("sizes were scored on different samples")
    rng = np.random.default_rng(seed)
    ns = np.array([np.mean([res["folds"][f][axis][str(g)][s]["n_materials"]
                            for f in folds for s in res["folds"][f][axis][str(g)]]) for g in grid])
    boots = np.empty(n_boot)
    for b in range(n_boot):
        drawn = rng.choice(mats, size=len(mats), replace=True)
        take = np.concatenate([idx_by_mat[m] for m in drawn])
        errs = [per_size[g][0][take].mean() for g in grid]
        boots[b] = power_law(ns, errs)[0]
    return boots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mde-trials", type=int, default=200)
    ap.add_argument("--no-mde", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(RES):
        raise SystemExit(f"{RES} missing — run learning_curve_v2.py first")
    res = json.load(open(RES))
    alpha, ncl = alpha_for("folds")
    out = {"source": RES, "alpha": alpha, "axes": {}}
    print(f"learning curve v2 — {res['field_shape'][0]}x{res['field_shape'][1]} c-channel, "
          f"p_field {res['p_field']}, p_warp {res['p_warp']}, levels {res['levels']}, alpha {alpha}")

    for axis, grid in (("materials", res["sizes"]), ("conditions", res["fracs"])):
        folds = [f for f in sorted(res.get("folds", {}), key=int)
                 if all(str(g) in res["folds"][f].get(axis, {})
                        and len(res["folds"][f][axis][str(g)]) >= len(res["seeds"]) for g in grid)]
        if not folds:
            print(f"\n{axis}: no complete fold yet")
            continue
        complete = len(folds) == res["n_folds"]
        print(f"\n{'=' * 96}\nAXIS: more {axis} — folds complete {folds} of {res['n_folds']}"
              + ("" if complete else "   ⚠ INCOMPLETE, provisional") + f"\n{'=' * 96}")
        print(f"  {'size':>6} {'n_mats':>6} {'n_train':>8} {'refit nRMSE':>13} {'sd(seeds)':>10} "
              f"{'fixed nRMSE':>12} {'R2 t_lo':>8} {'R2 t_hi':>8} {'modes>0.5':>9} {'modes>0.2':>9}")
        rows = []
        for g in grid:
            v, m = pooled(res, axis, g, "per_sample_refit", folds)
            vf, _ = pooled(res, axis, g, "per_sample_fixed", folds)
            _, sd = scalar_mean(res, axis, g, "field_refit", folds)
            nm = np.mean([res["folds"][f][axis][str(g)][s]["n_materials"]
                          for f in folds for s in res["folds"][f][axis][str(g)]])
            nt = np.mean([res["folds"][f][axis][str(g)][s]["n_train"]
                          for f in folds for s in res["folds"][f][axis][str(g)]])
            rlo, _ = scalar_mean(res, axis, g, "r2_t_lo", folds)
            rhi, _ = scalar_mean(res, axis, g, "r2_t_hi", folds)
            n5, r2 = mode_counts(res, axis, g, folds, 0.5)
            n2, _ = mode_counts(res, axis, g, folds, 0.2)
            rows.append({"size": g, "n_materials": float(nm), "n_train": float(nt),
                         "refit": float(v.mean()), "refit_sd_seeds": sd, "fixed": float(vf.mean()),
                         "r2_t_lo": rlo, "r2_t_hi": rhi, "modes_r2_gt_0.5": n5, "modes_r2_gt_0.2": n2,
                         "mode_r2": [float(x) for x in r2]})
            print(f"  {str(g):>6} {nm:>6.0f} {nt:>8.0f} {v.mean():>13.5f} {sd:>10.5f} {vf.mean():>12.5f} "
                  f"{rlo:>+8.3f} {rhi:>+8.3f} {n5:>9d} {n2:>9d}")

        # every consecutive step, paired and clustered
        print(f"\n  consecutive steps (paired, cluster-robust by material, alpha {alpha}):")
        steps = []
        for g0, g1 in zip(grid[:-1], grid[1:]):
            a, m = pooled(res, axis, g0, "per_sample_refit", folds)
            b, _ = pooled(res, axis, g1, "per_sample_refit", folds)
            r = compare(ArmResult(f"n={g0}", m, a), ArmResult(f"n={g1}", m, b), alpha=alpha, n_boot=4000)
            steps.append(r)
            print("    " + format_comparison(r))
        last = steps[-1]
        improving = bool(last["significant"] and last["mean_diff"] > 0)   # a is the smaller size

        # exponent with a bootstrap-over-materials CI
        ns = np.array([r["n_materials"] if axis == "materials" else r["n_train"] for r in rows])
        errs = np.array([r["refit"] for r in rows])
        beta, _ = power_law(ns, errs)
        boots = bootstrap_exponent(res, axis, grid, folds)
        lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
        print(f"\n  power law err ~ n^-beta over the {len(grid)} sizes: beta = {beta:.3f}  "
              f"CI [{lo:.3f}, {hi:.3f}]  (x-axis: {'materials' if axis == 'materials' else 'training conditions'})")
        print(f"  first -> last: {rows[0]['refit']:.4f} -> {rows[-1]['refit']:.4f} "
              f"({rows[0]['refit'] / rows[-1]['refit']:.2f}x)")

        mde = None
        if not improving and not args.no_mde:
            a, m = pooled(res, axis, grid[-2], "per_sample_refit", folds)
            b, _ = pooled(res, axis, grid[-1], "per_sample_refit", folds)
            mde = mde_report(b - a, m, base=float(a.mean()), alpha=alpha, effects=MDE_EFFECTS,
                             trials=args.mde_trials, label=f"last step {grid[-2]} -> {grid[-1]}")

        if improving:
            verdict = (f"NOT ELIMINATED at the largest size available ({grid[-1]}): the last step "
                       f"{grid[-2]} -> {grid[-1]} is a significant improvement "
                       f"(diff {last['mean_diff']:+.5f}, CI [{last['ci_low']:+.5f}, {last['ci_high']:+.5f}]). "
                       f"Exponent beta = {beta:.3f} [{lo:.3f}, {hi:.3f}]; no extrapolation beyond 2x the measured range.")
        else:
            verdict = (f"ELIMINATED: the last step {grid[-2]} -> {grid[-1]} is not a significant improvement "
                       f"(diff {last['mean_diff']:+.5f}, CI [{last['ci_low']:+.5f}, {last['ci_high']:+.5f}])"
                       + (f"; MDE at 80 % power {100 * mde['mde_80']:.0f} %" if mde and mde['mde_80'] else
                          "; MDE at 80 % power beyond the simulated range" if mde else ""))
        print(f"\n  VERDICT ({axis}): {verdict}")
        out["axes"][axis] = {"folds_done": folds, "complete": complete, "rows": rows,
                             "steps": steps, "last_step_improving": improving,
                             "beta": beta, "beta_ci": [float(lo), float(hi)],
                             "ratio_first_to_last": float(rows[0]["refit"] / rows[-1]["refit"]),
                             "mde_last_step": mde, "verdict": verdict}

    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
