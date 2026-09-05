"""L2-v2 verdict: is the parameter->coefficient map capacity-limited, on dataset v2?

Rule frozen in PREREG_L1L2L7_v2.md §2 (L2-v2), identical to legacy analyze_l2:
a family has SATURATED iff its largest capacity is not significantly better than
its second-largest at the calibrated alpha; L2 is ELIMINATED iff every family has
saturated. Each saturation null carries its MDE. Per-sample held-out values are
averaged over seeds and pooled over the five folds (each sample once); clustering
is by material.

The CROSS section (defect B43) is descriptive and POST-HOC, not part of the frozen
rule: it answers "how far did the optimum move from where L1 left it, and how far
ahead of the other families is it". Those four numbers were quoted in RESULTS.md
with CIs and had no script behind them — B39's class, in the rung whose retraction
(A26) rests on them. They are computed here so that they regenerate with the rest.

The section also asserts an identity the sweep makes available for free:
`mlp_width/w256` and `mlp_depth/d3` are the SAME estimator, (256, 256, 256), and
that estimator is also L1-v2's `mlp` arm. All three are trained on the same folds,
the same POD and the same seeds, so their per-sample scores must agree. A drift
between them would mean the folds, the basis or the seeding differ across runners
that the paper reports as identical.

    python analyze_l2_v2.py [--mde-trials 200]
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

from mde import mde_report
from metrics import ArmResult, compare, format_comparison
from v2_common import alpha_for

RES = "results/l2_v2_results.json"
OUT = "results/l2_v2_verdict.json"
L1_RES = "results/l1_v2_results.json"
MDE_EFFECTS = (0.0, 0.02, 0.05, 0.10, 0.20)

# The configuration L1-v2 and L7-v2 report: MLPRegressor(hidden_layer_sizes=(256,)*3).
# It appears in this sweep twice, once per family, and must be the same estimator.
L1_SETTING = ("mlp_depth/d3", "mlp_width/w256")
# The identity is exact only if both runners see the same POD basis; the randomised
# SVD is seeded per fold, so allow a floor rather than requiring bit-equality.
IDENTITY_TOL = 5e-3


def pooled(res, key, folds):
    v, m = [], []
    for f in folds:
        cells = res["cells"][key][f]
        seeds = sorted(cells)
        ids = [tuple(zip(cells[s]["test"]["material_ids"], cells[s]["test"]["condition_ids"])) for s in seeds]
        if any(i != ids[0] for i in ids[1:]):
            raise AssertionError(f"{key} fold {f}: seeds scored on different samples")
        v.append(np.mean([np.asarray(cells[s]["test"]["per_sample_nrmse_c"], float) for s in seeds], axis=0))
        m.append(np.asarray(cells[seeds[0]]["test"]["material_ids"]))
    return np.concatenate(v), np.concatenate(m)


def pooled_l1(path, arm, folds):
    """The same pooling for L1-v2's own results file, so the shared configuration
    can be compared across the two runners rather than assumed identical."""
    r = json.load(open(path))
    v, m = [], []
    for f in folds:
        cells = r["folds"][f]["arms"][arm]
        seeds = sorted(cells)
        v.append(np.mean([np.asarray(cells[s]["test"]["per_sample_nrmse_c"], float) for s in seeds], axis=0))
        m.append(np.asarray(cells[seeds[0]]["test"]["material_ids"]))
    return np.concatenate(v), np.concatenate(m)


def relative(r, base_mean):
    """A comparison as a percentage of the baseline arm, CI and all.

    `mean_diff` in `compare` is (a - b), so a NEGATIVE diff means arm_a is better.
    The percentages here are always 'how much better is arm_a than arm_b', so the
    sign is flipped once, here, and nowhere else.
    """
    return {"pct": -100.0 * r["mean_diff"] / base_mean,
            "pct_ci_low": -100.0 * r["ci_high"] / base_mean,
            "pct_ci_high": -100.0 * r["ci_low"] / base_mean}


def cross_comparisons(res, vals, best_overall, alpha, folds_all, l1_path=L1_RES):
    """Post-hoc, descriptive: how far the optimum moved, and the identity checks.

    NOT part of the frozen saturation rule (PREREG_L1L2L7_v2.md §2). Reported as
    post-hoc in RESULTS.md and in the paper. Exists because these four numbers were
    quoted with CIs and had no script behind them (defect B43).
    """
    out = {"note": "POST-HOC, descriptive. The pre-registered rule is the per-family "
                   "saturation test above; these contextualise where the optimum sits.",
           "comparisons": {}, "identity": {}}
    if best_overall is None:
        return out
    best_key = f"{best_overall[1]}/{best_overall[2]}"

    def cmp_keys(ka, kb, label):
        if ka not in vals or kb not in vals:
            print(f"  {label}: skipped ({ka if ka not in vals else kb} not complete)")
            return
        (va, ma), (vb, mb) = vals[ka], vals[kb]
        r = compare(ArmResult(ka, ma, va), ArmResult(kb, mb, vb), alpha=alpha, n_boot=4000)
        r["relative_to_b"] = relative(r, float(vb.mean()))
        out["comparisons"][label] = r
        rel = r["relative_to_b"]
        print(f"  {label}: " + format_comparison(r)
              + f"   {rel['pct']:+.1f} % [{rel['pct_ci_low']:+.1f}, {rel['pct_ci_high']:+.1f}]")

    # 1. how far the optimum moved from where L1 left it
    l1_key = next((k for k in L1_SETTING if k in vals), None)
    if l1_key:
        cmp_keys(best_key, l1_key, f"best ({best_key}) vs the L1 setting ({l1_key})")
    # 2. the width family's own optimum against the L1 width
    if "mlp_width/w256" in vals:
        wbest = min((k for k in vals if k.startswith("mlp_width/")), key=lambda k: vals[k][0].mean())
        if wbest != "mlp_width/w256":
            cmp_keys(wbest, "mlp_width/w256", f"{wbest} vs the L1 width (mlp_width/w256)")
    # 3. the best configuration against every other family's best
    fams = sorted({k.split("/")[0] for k in vals})
    for fam in fams:
        if fam == best_overall[1]:
            continue
        fbest = min((k for k in vals if k.startswith(fam + "/")), key=lambda k: vals[k][0].mean())
        cmp_keys(best_key, fbest, f"best ({best_key}) vs {fam} best ({fbest})")

    # 4. identity checks: the same estimator, reached by three different runners
    present = [k for k in L1_SETTING if k in vals]
    if len(present) == 2:
        (va, ma), (vb, _) = vals[present[0]], vals[present[1]]
        d = float(np.abs(va - vb).max())
        out["identity"][f"{present[0]} vs {present[1]}"] = {"max_abs_per_sample_diff": d,
                                                            "mean_a": float(va.mean()),
                                                            "mean_b": float(vb.mean()), "tol": IDENTITY_TOL}
        print(f"  identity {present[0]} vs {present[1]} (the same estimator): "
              f"max |per-sample diff| {d:.2e}  means {va.mean():.5f} / {vb.mean():.5f}")
        if d > IDENTITY_TOL:
            raise AssertionError(
                f"{present[0]} and {present[1]} are the same estimator (256,256,256) on the same "
                f"folds, POD and seeds, but their per-sample scores differ by up to {d:.2e} "
                f"(> {IDENTITY_TOL}). One of the two runs did not see what it is reported to have seen.")
    if present and os.path.exists(l1_path):
        v1, m1 = pooled_l1(l1_path, "mlp", folds_all)
        v2_, m2 = vals[present[0]]
        if v1.shape == v2_.shape and np.array_equal(m1, m2):
            d = float(np.abs(v1 - v2_).max())
            out["identity"][f"L1-v2 mlp vs {present[0]}"] = {"max_abs_per_sample_diff": d,
                                                             "mean_l1": float(v1.mean()),
                                                             "mean_l2": float(v2_.mean()), "tol": IDENTITY_TOL}
            print(f"  identity L1-v2 'mlp' vs {present[0]} (the same estimator, different runner): "
                  f"max |per-sample diff| {d:.2e}  means {v1.mean():.5f} / {v2_.mean():.5f}")
            if d > IDENTITY_TOL:
                raise AssertionError(
                    f"L1-v2's mlp arm and L2-v2's {present[0]} are the same estimator on the same folds "
                    f"and seeds, but differ by up to {d:.2e} (> {IDENTITY_TOL}). L1-v2 and L2-v2 are "
                    f"reported over the same design; one of them is not.")
        else:
            out["identity"]["L1-v2 mlp"] = {"skipped": "sample sets differ in order or length"}
            print("  identity vs L1-v2: skipped (sample sets differ in order or length)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mde-trials", type=int, default=200)
    ap.add_argument("--no-mde", action="store_true")
    ap.add_argument("--res", default=RES)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    res_path, out_path = args.res, args.out
    if not os.path.exists(res_path):
        raise SystemExit(f"{res_path} missing — run run_l2_v2.py first")
    res = json.load(open(res_path))
    alpha, ncl = alpha_for("folds")
    n_seeds = len(res["seeds"])
    keys = [f"{c['family']}/{c['label']}" for c in res["configs"]]
    folds_all = [str(f) for f in range(res["n_folds"])]
    complete = {k: [f for f in folds_all if len(res.get("cells", {}).get(k, {}).get(f, {})) >= n_seeds] for k in keys}
    print(f"L2-v2 — {res['field_shape'][0]}x{res['field_shape'][1]}, {res['modes']} modes, alpha {alpha} "
          f"({ncl} clusters); {sum(1 for k in keys if len(complete[k]) == res['n_folds'])}/{len(keys)} "
          f"configurations complete on all folds")
    floor = np.mean([res["folds"][f]["pod_floor"]["c"] for f in res.get("folds", {})]) if res.get("folds") else float("nan")

    fams = {}
    for c, k in zip(res["configs"], keys):
        fams.setdefault(c["family"], []).append((c, k))
    for f in fams:
        fams[f].sort(key=lambda x: x[0]["capacity"])

    out = {"source": res_path, "alpha": alpha, "pod_floor_mean": float(floor), "families": {}}
    all_saturated, any_incomplete = True, False
    best_overall = None
    all_vals = {}
    for fam, items in fams.items():
        done_folds = [complete[k] for _, k in items]
        usable = [(c, k) for (c, k), d in zip(items, done_folds) if len(d) == res["n_folds"]]
        print(f"\n{fam}: {len(usable)}/{len(items)} configurations complete on all folds")
        if len(usable) < 2:
            any_incomplete = True
            continue
        if len(usable) < len(items):
            any_incomplete = True
            print("  ⚠ INCOMPLETE family — provisional")
        print(f"  {'config':<8} {'train c':>9} {'held-out c':>18} {'gap':>6} {'x floor':>8}")
        rows, vals = [], {}
        for c, k in usable:
            v, m = pooled(res, k, folds_all)
            vals[k] = all_vals[k] = (v, m)
            tr = np.mean([res["cells"][k][f][s]["train"]["mean"]["c"] for f in folds_all for s in res["cells"][k][f]])
            per_seed = [np.mean([res["cells"][k][f][s]["test"]["mean"]["c"] for f in folds_all])
                        for s in map(str, res["seeds"])]
            rows.append({"label": c["label"], "capacity": c["capacity"], "train_c": float(tr),
                         "test_c": float(v.mean()), "test_c_sd_seeds": float(np.std(per_seed)),
                         "gap": float(v.mean() / tr), "x_floor": float(v.mean() / floor)})
            print(f"  {c['label']:<8} {tr:>9.4f} {v.mean():>10.4f}+-{np.std(per_seed):<7.4f} "
                  f"{v.mean() / tr:>5.1f}x {v.mean() / floor:>7.1f}x")
            if best_overall is None or v.mean() < best_overall[0]:
                best_overall = (float(v.mean()), fam, c["label"])
        nv = np.array([r["test_c"] for r in rows])
        best_i = int(np.argmin(nv))
        interior = 0 < best_i < len(nv) - 1
        noise = float(np.mean([r["test_c_sd_seeds"] for r in rows])) or 1e-12
        span = float(nv.max() - nv.min())
        if span < 2 * noise:
            shape = "FLAT (within seed noise)"
        elif interior:
            shape = f"U-SHAPED, optimum at {rows[best_i]['label']}"
        elif best_i == len(nv) - 1:
            shape = "falls monotonically with capacity"
        else:
            shape = "rises with capacity (over-fitting)"
        (c_hi, k_hi), (c_lo, k_lo) = usable[-1], usable[-2]
        r = compare(ArmResult(c_hi["label"], vals[k_hi][1], vals[k_hi][0]),
                    ArmResult(c_lo["label"], vals[k_lo][1], vals[k_lo][0]), alpha=alpha, n_boot=4000)
        improving = bool(r["significant"] and r["mean_diff"] < 0)
        print(f"  shape: {shape}   best {rows[best_i]['label']} = {nv[best_i]:.4f}   span/noise {span / noise:.1f}")
        print(f"  last step ({c_lo['label']} -> {c_hi['label']}): " + format_comparison(r)
              + f"  -> {'STILL IMPROVING' if improving else 'SATURATED'}")
        mde = None
        if not improving and not args.no_mde:
            mde = mde_report(vals[k_hi][0] - vals[k_lo][0], vals[k_hi][1], base=float(vals[k_lo][0].mean()),
                             alpha=alpha, effects=MDE_EFFECTS, trials=args.mde_trials,
                             label=f"{fam} {c_lo['label']} -> {c_hi['label']}")
        r_end = compare(ArmResult(usable[-1][0]["label"], vals[usable[-1][1]][1], vals[usable[-1][1]][0]),
                        ArmResult(usable[0][0]["label"], vals[usable[0][1]][1], vals[usable[0][1]][0]),
                        alpha=alpha, n_boot=4000)
        print(f"  largest vs smallest: " + format_comparison(r_end))
        all_saturated &= not improving
        out["families"][fam] = {"rows": rows, "shape": shape, "best": rows[best_i]["label"],
                                "last_step": r, "last_step_improving": improving,
                                "mde_last_step": mde if mde is not None else ("PENDING" if not improving else None),
                                "provisional": bool(not improving and mde is None),
                                "largest_vs_smallest": r_end}

    print(f"\n{'=' * 80}\nCROSS-CONFIGURATION (post-hoc, descriptive — not the frozen rule)\n{'=' * 80}")
    out["cross"] = cross_comparisons(res, all_vals, best_overall, alpha, folds_all)

    print(f"\n{'=' * 80}\nL2-v2 VERDICT\n{'=' * 80}")
    if best_overall:
        print(f"  best configuration anywhere: {best_overall[1]}/{best_overall[2]} = {best_overall[0]:.4f} "
              f"({best_overall[0] / floor:.0f}x the POD floor)")
    pending = [f for f, v in out["families"].items() if v.get("provisional")]
    if any_incomplete:
        verdict = "INCOMPLETE — no verdict may be reported yet"
    elif all_saturated:
        verdict = ("Every family has SATURATED at its last step. Capacity is ELIMINATED on dataset v2."
                   + (f" PROVISIONAL: MDE pending for {pending} (rule 7)." if pending else ""))
    else:
        still = [f for f, v in out["families"].items() if v["last_step_improving"]]
        verdict = f"NOT ELIMINATED: families still improving at their last step: {still}. Extend their sweeps."
    print(f"  {verdict}")
    out["verdict"] = verdict
    out["best_overall"] = best_overall
    json.dump(out, open(out_path, "w"), indent=2)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
