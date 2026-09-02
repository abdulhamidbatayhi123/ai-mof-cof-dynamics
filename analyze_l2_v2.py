"""L2-v2 verdict: is the parameter->coefficient map capacity-limited, on dataset v2?

Rule frozen in PREREG_L1L2L7_v2.md §2 (L2-v2), identical to legacy analyze_l2:
a family has SATURATED iff its largest capacity is not significantly better than
its second-largest at the calibrated alpha; L2 is ELIMINATED iff every family has
saturated. Each saturation null carries its MDE. Per-sample held-out values are
averaged over seeds and pooled over the five folds (each sample once); clustering
is by material.

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
MDE_EFFECTS = (0.0, 0.02, 0.05, 0.10, 0.20)


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
            vals[k] = (v, m)
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
