"""L4b-v2 verdicts: Q1/Q2 (weighting sweep), Q3 (physics at inference), Q4 (L-BFGS polish).

Rules frozen in PREREG_L4b_v2.md §2. Per-sample held-out values are averaged over
seeds; comparisons are paired and cluster-robust by material at alpha = 0.02; every
null carries its MDE. `best_pi` is chosen on the held-out error — the generous
direction for the arm being argued against — and that is stated in the output.

    python analyze_l4b_v2.py [--mde-trials 200]
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

from mde import mde_report
from metrics import ArmResult, compare, format_comparison

SWEEP = "results/l4b_v2_results.json"
REFINE = "results/l4b_v2_refine.json"
OUT = "results/l4b_v2_verdict.json"
ALPHA = 0.02
MDE_EFFECTS = (0.0, 0.05, 0.10, 0.20, 0.30)


def seed_avg(cells, seeds, key):
    recs = [cells[str(s)] for s in seeds]
    ids = [tuple(zip(r["material_ids"], r["condition_ids"])) for r in recs]
    if any(i != ids[0] for i in ids[1:]):
        raise AssertionError("seeds scored on different samples")
    return (np.mean([np.asarray(r[key], float) for r in recs], axis=0),
            np.asarray(recs[0]["material_ids"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mde-trials", type=int, default=200)
    ap.add_argument("--no-mde", action="store_true")
    ap.add_argument("--sweep", default=SWEEP)
    ap.add_argument("--refine", default=REFINE)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    sw = json.load(open(args.sweep))
    seeds = sw["seeds"]
    out = {"alpha": ALPHA, "axes": {}}
    print(f"L4b-v2 — bounded ParametricPINN {sw['n_params']:,} params, {sw['steps']} steps, alpha {ALPHA}")

    for axis in ("time", "material"):
        S = sw.get("sweep", {}).get(axis, {})
        if "data_only" not in S or len(S["data_only"]) < len(seeds):
            print(f"\n[{axis}] data_only incomplete; skipped")
            continue
        complete = {a: v for a, v in S.items() if len(v) >= len(seeds)}
        failed = {a: [s for s in seeds if v[str(s)].get("failed")] for a, v in complete.items()}
        usable = [a for a in complete if not failed[a]]
        # B16 signature: seen-window error > 3x the data-only twin's -> abandoned the data fit
        d0_seen = np.mean([complete["data_only"][str(s)]["seen"] for s in seeds])
        abandoned = [a for a in usable if a != "data_only"
                     and np.mean([complete[a][str(s)]["seen"] for s in seeds]) > 3 * d0_seen]
        eligible = [a for a in usable if a != "data_only" and a not in abandoned]
        print(f"\n{'=' * 90}\n[{axis}] {len(complete)}/{len(sw['arms_all'])} arms complete; "
              f"failed: { {a: f for a, f in failed.items() if f} or 'none'}; "
              f"abandoned data fit (seen > 3x data-only): {abandoned or 'none'}\n{'=' * 90}")
        print(f"  {'arm':<18} {'seen':>8} {'held':>8} {'sd(seeds)':>10} {'w_pde final':>12}")
        table = {}
        for a in complete:
            seen = np.mean([complete[a][str(s)]["seen"] for s in seeds if not complete[a][str(s)].get("failed")] or [np.nan])
            helds = [complete[a][str(s)]["held"] for s in seeds if not complete[a][str(s)].get("failed")]
            w = np.mean([complete[a][str(s)]["final_weights"]["w_pde"] for s in seeds]) if a != "data_only" else 0.0
            table[a] = {"seen": float(seen), "held": float(np.mean(helds)) if helds else None,
                        "held_sd": float(np.std(helds)) if helds else None, "w_pde_final": float(w),
                        "failed_seeds": failed[a]}
            print(f"  {a:<18} {seen:>8.4f} {np.mean(helds) if helds else float('nan'):>8.4f} "
                  f"{np.std(helds) if helds else float('nan'):>10.4f} {w:>12.2e}")
        if not eligible:
            out["axes"][axis] = {"table": table, "verdict": "no eligible physics arm"}
            continue
        d0, mats = seed_avg(complete["data_only"], seeds, "per_sample_held")
        comps, mdes = {}, {}
        worse_all = True
        for a in eligible:
            v, _ = seed_avg(complete[a], seeds, "per_sample_held")
            r = compare(ArmResult("data_only", mats, d0), ArmResult(a, mats, v), alpha=ALPHA, n_boot=4000)
            comps[a] = r
            print("    " + format_comparison(r))
            worse_all &= bool(r["significant"] and r["mean_diff"] < 0)
        best_pi = min(eligible, key=lambda a: table[a]["held"])
        r_best = comps[best_pi]
        print(f"\n  best physics arm (chosen on HELD-OUT error, generous to physics): {best_pi} = {table[best_pi]['held']:.4f}")
        # the edge check (rule 4) on the fixed-weight sweep
        fixed = sorted([a for a in eligible if a.startswith("pi_fixed_w")], key=lambda a: float(a[10:]))
        edge = None
        if fixed:
            bf = min(fixed, key=lambda a: table[a]["held"])
            if bf in (fixed[0], fixed[-1]):
                edge = bf
                print(f"  ⚠ fixed-weight optimum {bf} sits on the sweep edge — extend before a verdict (PREREG §4.2)")
        if worse_all:
            verdict = ("PHYSICS IS WORSE AT EVERY WEIGHTING SCHEME TESTED (fixed over four decades, gradient-norm "
                       "at three targets, NTK, self-adaptive) — the legacy claim stands, now defended.")
        elif not r_best["significant"]:
            verdict = f"NO DIFFERENCE between data_only and the best physics arm {best_pi}; the legacy 'hurts' claim is WITHDRAWN."
            if not args.no_mde:
                v, _ = seed_avg(complete[best_pi], seeds, "per_sample_held")
                mdes[best_pi] = mde_report(v - d0, mats, base=float(d0.mean()), alpha=ALPHA, effects=MDE_EFFECTS,
                                           trials=args.mde_trials, label=f"[{axis}] data_only vs {best_pi}")
        elif r_best["mean_diff"] > 0:
            verdict = f"PHYSICS HELPS once correctly weighted ({best_pi}); the legacy claim is RETRACTED as a weighting artefact."
        else:
            verdict = (f"the best physics arm {best_pi} is significantly worse than data_only, but not every arm is; "
                       f"report per arm.")
        print(f"  VERDICT [{axis}]: {verdict}")
        out["axes"][axis] = {"table": table, "eligible": eligible, "abandoned": abandoned, "failed": failed,
                             "comparisons_vs_data_only": comps, "best_pi": best_pi, "edge_warning": edge,
                             "mde": mdes, "verdict": verdict}

        # Q4 — the polish
        P = sw.get("polish", {}).get(axis, {})
        if P and "data_only" in P and P.get("best_pi") in P and len(P["data_only"]) >= len(seeds):
            bp = P["best_pi"]
            d0p, m2 = seed_avg(P["data_only"], seeds, "per_sample_held")
            vp, _ = seed_avg(P[bp], seeds, "per_sample_held")
            rp = compare(ArmResult("data_only+lbfgs", m2, d0p), ArmResult(bp + "+lbfgs", m2, vp), alpha=ALPHA, n_boot=4000)
            print(f"\n  Q4 polish: " + format_comparison(rp))
            before_sign = np.sign(r_best["mean_diff"]) if r_best["significant"] else 0
            after_sign = np.sign(rp["mean_diff"]) if rp["significant"] else 0
            flip = before_sign != after_sign
            print(f"  -> ordering {'CHANGES' if flip else 'unchanged'} under L-BFGS polish "
                  f"(data_only {np.mean([P['data_only'][str(s)]['held'] for s in seeds]):.4f}, "
                  f"{bp} {np.mean([P[bp][str(s)]['held'] for s in seeds]):.4f})")
            out["axes"][axis]["polish"] = {"best_pi": bp, "comparison": rp, "ordering_flips": bool(flip)}

    # Q3 — refinement
    if os.path.exists(args.refine):
        rf = json.load(open(args.refine))
        out["refine"] = {}
        for axis in ("time", "material"):
            for arm, cells in rf.get(axis, {}).items():
                if len(cells) < len(seeds):
                    continue
                b, mats = seed_avg(cells, seeds, "per_sample_before")
                a, _ = seed_avg(cells, seeds, "per_sample_after")
                r = compare(ArmResult(f"{arm} before", mats, b), ArmResult(f"{arm} after refinement", mats, a),
                            alpha=ALPHA, n_boot=4000)
                sb = np.mean([cells[str(s)]["seen_before"] for s in seeds])
                sa_ = np.mean([cells[str(s)]["seen_after"] for s in seeds])
                print(f"\n  Q3 [{axis}] {arm}: " + format_comparison(r))
                print(f"     seen-window/materials {sb:.4f} -> {sa_:.4f} ({100 * (sa_ / sb - 1):+.1f} %)"
                      + ("   ⚠ seen error rose > 10 % — anchor insufficient (PREREG §4.3)" if sa_ > 1.1 * sb else ""))
                if r["significant"] and r["mean_diff"] > 0:
                    v = "physics at inference HELPS"
                elif r["significant"]:
                    v = "physics at inference makes transfer WORSE"
                else:
                    v = "physics at inference does not improve transfer at this configuration"
                    if not args.no_mde:
                        mde_report(a - b, mats, base=float(b.mean()), alpha=ALPHA, effects=MDE_EFFECTS,
                                   trials=args.mde_trials, label=f"Q3 [{axis}] {arm}")
                print(f"     -> {v}")
                out["refine"][f"{axis}/{arm}"] = {"comparison": r, "seen_before": float(sb), "seen_after": float(sa_),
                                                  "verdict": v}
    json.dump(out, open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
