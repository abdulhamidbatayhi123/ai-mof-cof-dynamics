"""L7-v2 verdict: is learning justified against closed-form theory, on dataset v2?

Rule frozen in PREREG_L1L2L7_v2.md §2 (L7-v2): learning is JUSTIFIED iff every
classical form is significantly worse than the best learned arm on exit-curve
nRMSE, paired sample by sample over all 240 materials. The learned arm's numbers
are its OUT-OF-FOLD exit-curve predictions from run_l1_v2 (fold design). "Best",
the arms that tie with it, and the B14 flag are READ FROM THE L1-v2 VERDICT — this
script refuses to run without a complete L1-v2 verdict, so the tie rule cannot be
dropped silently. If any classical form ties or wins, that is the headline.

    python analyze_l7_v2.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os

import numpy as np

from analyze_l1_v2 import pooled_floor, pooled_folds
from mde import mde_report
from metrics import ArmResult, compare, format_comparison
from v2_common import alpha_for

L7 = "results/l7_v2_results.json"
L1 = "results/l1_v2_results.json"
L1V = "results/l1_v2_verdict.json"
OUT = "results/l7_v2_verdict.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l7", default=L7)
    ap.add_argument("--l1", default=L1)
    ap.add_argument("--l1-verdict", default=L1V)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--no-mde", action="store_true")
    ap.add_argument("--mde-trials", type=int, default=200)
    args = ap.parse_args()
    for p in (args.l7, args.l1, args.l1_verdict):
        if not os.path.exists(p):
            raise SystemExit(f"{p} missing — L7-v2 needs the L7 results, the L1-v2 results AND the L1-v2 verdict")
    l7, l1, l1v = json.load(open(args.l7)), json.load(open(args.l1)), json.load(open(args.l1_verdict))
    if "folds" not in l1v or not l1v["folds"].get("complete"):
        raise SystemExit("ABORT: the L1-v2 fold verdict is incomplete; L7-v2 cannot be scored")
    alpha, ncl = alpha_for("folds")
    seeds = [str(s) for s in l1["seeds"]]
    arms = [a for a in l1["arms_requested"] if a not in l1.get("arms_skipped", [])]
    done = [f for f in sorted(l1["folds"], key=int)
            if all(all(s in l1["folds"][f]["arms"].get(a, {}) for s in seeds) for a in arms)]
    if len(done) < l1["n_folds"]:
        raise SystemExit(f"L1-v2 fold design incomplete ({done} of {l1['n_folds']})")
    sub = {"folds": {f: l1["folds"][f] for f in done}}

    # the learned reference and its ties come from the L1 verdict, and must agree
    # with what this file sees
    field_c = {a: float(pooled_folds(sub, a, "per_sample_nrmse_c")[0].mean()) for a in arms}
    best_local = min(arms, key=field_c.get)
    best = l1v["folds"]["best"]
    if best != best_local:
        raise SystemExit(f"ABORT: L1-v2 verdict names '{best}' as best but the results file gives '{best_local}' "
                         f"— the verdict is stale; re-run analyze_l1_v2.py")
    ties = [a for a in l1v["folds"].get("ties_with_best", []) if a in arms and a != best]
    flagged = l1v["folds"].get("underfitting_flag", [])
    compare_arms = [best] + ties
    if best in flagged:
        raise SystemExit(f"ABORT: the learned reference '{best}' carries the B14 underfitting flag")

    learned = {}
    for a in compare_arms:
        e, m, c = pooled_folds(sub, a, "per_sample_exit_nrmse")
        learned[a] = {(int(mm), int(cc)): float(v) for v, mm, cc in zip(e, m, c)}
    fl_key = {}
    for f in done:
        rec = l1["folds"][f]["pod_floor_per_sample"]
        for v, mm, cc in zip(rec["per_sample_exit_nrmse"], rec["material_ids"], rec["condition_ids"]):
            fl_key[(int(mm), int(cc))] = float(v)

    keys = [(int(m), int(c)) for m, c in zip(l7["material_ids"], l7["condition_ids"])]
    mats = np.asarray(l7["material_ids"])
    missing = [k for k in keys if k not in learned[best]]
    if missing:
        raise SystemExit(f"{len(missing)} L7 samples have no out-of-fold learned prediction — the sample sets differ")

    print(f"L7-v2 — exit-curve nRMSE, {len(keys)} samples over {len(np.unique(mats))} materials, alpha {alpha}")
    print(f"  learned reference from the L1-v2 verdict: {best} (out-of-fold field nRMSE c = {field_c[best]:.4f})"
          + (f"; tied arms also compared: {ties}" if ties else "; no tied arms"))
    print(f"\n  {'method':<20} {'exit nRMSE':>11} {'dt50 (h)':>9} {'ms/curve':>9} {'trained?':>9}")
    print(f"  {'POD floor':<20} {np.mean([fl_key[k] for k in keys]):>11.4f} {'':>9} {'':>9} {'—':>9}")
    for a in compare_arms:
        e = np.array([learned[a][k] for k in keys])
        dt = pooled_folds(sub, a, "per_sample_dt_bt50")[0]
        print(f"  {a + ' (learned)':<20} {e.mean():>11.4f} {np.nanmean(dt) / 3600:>9.2f} {'~ms':>9} {'yes':>9}")
    for name, rec in l7["models"].items():
        print(f"  {name:<20} {rec['nrmse']:>11.4f} {rec['dt_bt50'] / 3600:>9.2f} {rec['ms_per_curve']:>9.3f} {'no':>9}")

    out = {"alpha": alpha, "learned_reference": best, "tied_arms": ties, "comparisons": {}, "mde": {},
           "l1_verdict_sha1": hashlib.sha1(open(args.l1_verdict, "rb").read()).hexdigest(),
           "mde_computed": not args.no_mde}
    justified = True
    print(f"\n  paired, cluster-robust by material, alpha {alpha}:")
    for a in compare_arms:
        e_l = np.array([learned[a][k] for k in keys])
        for name, rec in l7["models"].items():
            e_c = np.asarray(rec["per_sample_nrmse"], float)
            r = compare(ArmResult(a, mats, e_l), ArmResult(name, mats, e_c), alpha=alpha, n_boot=4000)
            out["comparisons"][f"{a} vs {name}"] = r
            print("    " + format_comparison(r))
            learned_better = r["significant"] and r["mean_diff"] < 0
            if not learned_better:
                justified = False
                if not r["significant"] and not args.no_mde:
                    out["mde"][f"{a} vs {name}"] = mde_report(
                        e_c - e_l, mats, base=float(e_l.mean()), alpha=alpha,
                        effects=(0.0, 0.05, 0.1, 0.2, 0.3), trials=args.mde_trials, label=f"{a} vs {name}")
    ratio = min(rec["nrmse"] for rec in l7["models"].values()) / np.mean([learned[best][k] for k in keys])
    if justified:
        verdict = (f"LEARNING IS JUSTIFIED on dataset v2: every classical form is significantly worse than "
                   f"the learned reference on the exit curve; the best closed form is {ratio:.2f}x worse.")
    else:
        verdict = ("A CLASSICAL FORM TIES OR BEATS THE LEARNED ARM. This is the headline of the rung "
                   "and must be reported as such (protocol §2)."
                   + (" PROVISIONAL: no MDE computed." if args.no_mde else ""))
    print(f"\n  VERDICT: {verdict}")
    out["verdict"] = verdict
    out["best_classical_over_learned"] = float(ratio)
    json.dump(out, open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
