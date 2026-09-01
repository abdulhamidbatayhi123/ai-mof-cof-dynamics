"""L6 on dataset v2: the Damkohler slope test, cross-validated over materials.

Design frozen in `PREREG_L6_v2.md`, committed before this file was run. Read that
first; this is the implementation, not the argument.

Two changes from `run_l6.py`, both forced by measurement rather than preference.

1. CROSS-VALIDATION OVER MATERIALS, not one holdout.
   The legacy design held out 12 materials and had 7 % power at a 20 % effect
   (retraction A22). Dataset v2 holds out 48, which reaches only ~36 %. Five folds
   over all 240 materials put every material in a held-out set exactly once, giving
   240 held-out clusters instead of 48 at 5x the compute. Power scales roughly as
   sqrt(n_clusters), so the expected MDE improves from ~50 % to ~23 %.

2. THE ESTIMAND IS A SLOPE, not a pooled mean.
   The pooled question -- "is separate better than joint on average?" -- cannot be
   answered at any cluster count we can afford, because the between-material sd of
   the arm difference is 69 % of the base error. The mechanism says the benefit
   should DEPEND on how much the kinetics matter, and Damkohler measures exactly
   that. Regressing the per-material paired difference on log10(Da) uses that
   variance instead of paying for it as noise, and it is a stronger scientific
   statement than a verdict.

   The pooled mean is still reported, with its MDE, as the secondary estimand.

Usage
    python run_l6_v2.py --folds 5 --seeds 42 43 44
    python run_l6_v2.py --check-only        # invalidation checks, no training
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import time

import numpy as np

import descriptors as DSC
import ladder_data
from metrics import ArmResult, compare
from run_l6 import eval_fields, train

ALPHA_V2 = 0.02          # calibrated for 48 clusters; results/calibration_v2.json


def assign_folds(material_ids, n_folds, seed):
    """Partition MATERIALS (never conditions) into folds. Written before training."""
    mats = np.unique(material_ids)
    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(mats)
    return {int(m): int(i % n_folds) for i, m in enumerate(shuffled)}


def damkohler_per_material(root):
    """Median Da per material, from the manifest's per-sample record."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    by = {}
    for s in man["samples"]:
        if "Da" in s:
            by.setdefault(s["mat"], []).append(s["Da"])
    return {m: float(np.median(v)) for m, v in by.items()}


def slope_test(delta_by_mat, da_by_mat, n_boot=4000, alpha=ALPHA_V2, seed=0):
    """Regress the per-material paired difference on log10(Da); bootstrap MATERIALS.

    delta_m = err_separate,m - err_joint,m.  A POSITIVE slope means the separate
    arm's disadvantage shrinks (or its advantage grows) as Da rises... so H1-v2
    predicts a positive slope on log10(Da), i.e. separation pays MOST at low Da.
    The sign convention is stated here and in the pre-registration so it cannot be
    chosen after seeing the data.
    """
    mats = sorted(set(delta_by_mat) & set(da_by_mat))
    x = np.log10(np.array([da_by_mat[m] for m in mats]))
    y = np.array([delta_by_mat[m] for m in mats])
    if len(mats) < 5:
        return {"n_materials": len(mats), "error": "too few materials"}
    slope, intercept = np.polyfit(x, y, 1)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        i = rng.integers(0, len(mats), len(mats))
        if len(np.unique(x[i])) < 2:
            boots[b] = np.nan
            continue
        boots[b] = np.polyfit(x[i], y[i], 1)[0]
    boots = boots[np.isfinite(boots)]
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"n_materials": len(mats), "slope": float(slope),
            "intercept": float(intercept), "ci_low": float(lo), "ci_high": float(hi),
            "significant": bool(lo > 0 or hi < 0), "alpha": alpha,
            "log10_da_range": [float(x.min()), float(x.max())],
            "pearson_r": float(np.corrcoef(x, y)[0, 1])}


def invalidation_checks(d, X, root, verbose=True):
    """Everything that would make this rung meaningless, checked BEFORE the verdict."""
    out = {}
    if verbose:
        print("\n" + "=" * 72)
        print("INVALIDATION CHECKS (PREREG_L6_v2.md section 5) — run before any verdict")
        print("=" * 72)

    # 1. Is the kinetic object actually hidden? (defect B19)
    r2 = DSC.check_non_degenerate(d, X, verbose=verbose)
    out["descriptor_r2"] = r2
    kin = "d_p" if "d_p" in d.param_keys else "k_LDF"
    out["kinetic_key"] = kin
    out["kinetic_hidden"] = bool(r2.get(kin, 0.0) <= 0.7)
    if verbose:
        print(f"\n  kinetic object '{kin}': R2 = {r2.get(kin, float('nan')):+.4f}  -> "
              f"{'HIDDEN, rung is valid' if out['kinetic_hidden'] else 'RECOVERABLE — RUNG IS DEGENERATE (B19)'}")

    # 2. Does Da actually vary, and by how much?
    da = damkohler_per_material(root)
    v = np.array(list(da.values()))
    out["da"] = {"n": len(v), "min": float(v.min()), "median": float(np.median(v)),
                 "max": float(v.max()), "decades": float(np.log10(v.max() / v.min()))}
    if verbose:
        print(f"\n  Damkohler per material: n={len(v)}  "
              f"min {v.min():.1f}  median {np.median(v):.1f}  max {v.max():.1f}  "
              f"({out['da']['decades']:.2f} decades)")
        print(f"  -> {'sufficient spread for a slope test' if out['da']['decades'] > 1.0 else 'TOO NARROW for a slope test'}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="data/parametric_v2")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--fold-seed", type=int, default=20260901)
    ap.add_argument("--arms", nargs="+", default=["joint", "separate", "separate_noeq"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--budget", type=int, default=120_000)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--n-rays", type=int, default=128)
    ap.add_argument("--n-t", type=int, default=32)
    ap.add_argument("--only-folds", type=int, nargs="+", default=None,
                    help="run a subset of folds; results merge by fold id")
    ap.add_argument("--field-res", type=int, default=128,
                    help="subsample the stored (nz, nt) grid to this square "
                         "resolution on load. Applied once, before any arm sees "
                         "the data, so it is identical across arms and folds and "
                         "is recorded in the results. 0 disables.")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--out", default="results/l6_v2_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load(args.root, field_res=(args.field_res or None))

    # Memory: the subsample happens inside ladder_data.load, per file, because
    # allocating the full 3.1 GB first is what runs a shared 16 GB machine out of
    # RAM. It is applied identically to every sample -- an encoding choice made
    # once, before any arm sees the data -- and is recorded in the results file.

    print(f"\nbuilding observable descriptors for {len(d.params)} samples "
          f"(generative parameters WITHHELD)...", flush=True)
    X_raw, names = DSC.build(d)

    checks = invalidation_checks(d, X_raw, args.root)
    if not checks["kinetic_hidden"]:
        raise SystemExit("\nABORT: the kinetic object is recoverable from the descriptors. "
                         "This is defect B19 — the rung would measure nothing. "
                         "Do not train arms against this descriptor set.")
    if args.check_only:
        json.dump(checks, open("results/l6_v2_checks.json", "w"), indent=2)
        print("\nwrote results/l6_v2_checks.json (checks only, no training)")
        return

    folds = assign_folds(d.material_ids, args.folds, args.fold_seed)
    fold_of = np.array([folds[int(m)] for m in d.material_ids])
    os.makedirs("results", exist_ok=True)
    json.dump({"fold_seed": args.fold_seed, "n_folds": args.folds,
               "material_to_fold": folds},
              open("results/l6_v2_folds.json", "w"), indent=2)
    print(f"\nfolds written BEFORE training: {args.folds} folds over "
          f"{len(set(folds))} materials -> results/l6_v2_folds.json")
    for f in range(args.folds):
        n_mat = len({m for m, ff in folds.items() if ff == f})
        print(f"   fold {f}: {n_mat} held-out materials, {(fold_of == f).sum()} conditions")

    res = {"root": args.root, "design": d.meta.get("design", "legacy"),
           "field_res": args.field_res, "field_shape": list(d.fields.shape[2:]),
           "budget": args.budget, "depth": args.depth, "steps": args.steps,
           "seeds": args.seeds, "n_folds": args.folds, "fold_seed": args.fold_seed,
           "alpha": ALPHA_V2, "n_desc": X_raw.shape[1], "descriptor_names": names,
           "checks": checks, "folds": {}}

    # RESUME, not overwrite. With --only-folds this script writes to the same file,
    # so building a fresh `res` would silently discard every fold completed by an
    # earlier invocation — losing hours of the primary hypothesis while appearing to
    # succeed. Load what is there and merge, after asserting the configuration
    # matches: merging folds trained under a different budget, step count or fold
    # seed would violate information parity across the very comparison this rung is.
    if os.path.exists(args.out):
        try:
            prev = json.load(open(args.out))
        except Exception:
            prev = None
        if prev:
            for k in ("budget", "depth", "steps", "n_folds", "fold_seed", "root", "seeds"):
                if prev.get(k) != res[k]:
                    raise SystemExit(
                        f"ABORT: {args.out} was produced with {k}={prev.get(k)!r} but this "
                        f"run uses {k}={res[k]!r}. Merging them would break information "
                        f"parity across folds. Move the old file aside or match the config.")
            res["folds"] = prev.get("folds", {})
            if res["folds"]:
                print(f"\nresuming: {sorted(res['folds'])} already complete in {args.out}")

    todo = args.only_folds if args.only_folds is not None else range(args.folds)
    for f in todo:
        te = np.where(fold_of == f)[0]
        tr = np.where(fold_of != f)[0]
        # Standardise on THIS fold's training materials only. Using global
        # statistics would leak held-out material properties into every fold.
        X, mu, sd = DSC.standardise(X_raw, tr)
        print(f"\n--- fold {f}: train {len(tr)} conds / "
              f"{len(np.unique(d.material_ids[tr]))} materials | "
              f"held-out {len(te)} conds / {len(np.unique(d.material_ids[te]))} materials ---",
              flush=True)
        res["folds"][str(f)] = {"n_train": int(len(tr)), "n_test": int(len(te)),
                                "test_materials": sorted(map(int, np.unique(d.material_ids[te]))),
                                "arms": {}}
        for arm in args.arms:
            res["folds"][str(f)]["arms"][arm] = {}
            for seed in args.seeds:
                t1 = time.time()
                model, w, npar = train(arm, d, X, tr, args, seed)
                model.eval()
                rows = eval_fields(model, d, te, X, args.n_t)
                rec = {"c": float(np.nanmean([r["c"] for r in rows])),
                       "q": float(np.nanmean([r["q"] for r in rows])),
                       "exit_nrmse": float(np.nanmean([r["exit_nrmse"] for r in rows])),
                       "dt_bt50": float(np.nanmean([r["dt_bt50"] for r in rows])),
                       "per_sample_nrmse_c": [float(r["c"]) for r in rows],
                       "material_ids": d.material_ids[te].tolist(),
                       "width": w, "n_params": npar}
                res["folds"][str(f)]["arms"][arm][str(seed)] = rec
                print(f"  {arm:<14} w{w:<4} {npar:>8,}p seed {seed}: "
                      f"novel={rec['c']:.4f} q={rec['q']:.4f} "
                      f"exit={rec['exit_nrmse']:.4f}  [{time.time()-t1:.0f}s]", flush=True)
                del model; gc.collect()
            json.dump(res, open(args.out, "w"), indent=2)

    print(f"\nwrote {args.out}  [{time.time()-t0:.0f}s]")
    print("Run analyze_l6_v2.py for the slope test and the pooled estimand.")


if __name__ == "__main__":
    main()
