"""L7-v2 verdict: is learning justified against closed-form theory, on dataset v2?

Rule frozen in PREREG_L1L2L7_v2.md §2 (L7-v2): learning is JUSTIFIED iff every
classical form is significantly worse than the best learned arm on exit-curve
nRMSE, paired sample by sample over all 240 materials. The learned arm's numbers
are its OUT-OF-FOLD exit-curve predictions from run_l1_v2 (fold design); "best"
is the L1-(a) arm with the lowest pooled out-of-fold nRMSE(c), and every arm that
ties with it under L1's rule is compared as well. If any classical form ties or
wins, that is the headline.

    python analyze_l7_v2.py
"""
from __future__ import annotations

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
    for p in (L7, L1):
        if not os.path.exists(p):
            raise SystemExit(f"{p} missing")
    l7, l1 = json.load(open(L7)), json.load(open(L1))
    alpha, ncl = alpha_for("folds")
    arms = [a for a in l1["arms_requested"] if a not in l1.get("arms_skipped", [])]
    done = [f for f in sorted(l1.get("folds", {}), key=int)
            if all(len(l1["folds"][f]["arms"].get(a, {})) >= 3 for a in arms)]
    if len(done) < l1["n_folds"]:
        raise SystemExit(f"L1-v2 fold design incomplete ({done} of {l1['n_folds']}); L7-v2 cannot be scored")
    sub = {"folds": {f: l1["folds"][f] for f in done}}

    # learned arms, out-of-fold, keyed by (material, condition)
    learned = {}
    for a in arms:
        e, m, c = pooled_folds(sub, a, "per_sample_exit_nrmse")
        learned[a] = {(int(mm), int(cc)): float(v) for v, mm, cc in zip(e, m, c)}
    fl_e, _ = pooled_floor(sub, "per_sample_exit_nrmse")
    fl_key = {}
    for f in done:
        rec = l1["folds"][f]["pod_floor_per_sample"]
        for v, mm, cc in zip(rec["per_sample_exit_nrmse"], rec["material_ids"], rec["condition_ids"]):
            fl_key[(int(mm), int(cc))] = float(v)

    keys = [(int(m), int(c)) for m, c in zip(l7["material_ids"], l7["condition_ids"])]
    mats = np.asarray(l7["material_ids"])
    missing = [k for k in keys if k not in learned[arms[0]]]
    if missing:
        raise SystemExit(f"{len(missing)} L7 samples have no out-of-fold learned prediction — the sample sets differ")

    field_c = {a: float(pooled_folds(sub, a, "per_sample_nrmse_c")[0].mean()) for a in arms}
    best = min(arms, key=field_c.get)
    ties = []
    if os.path.exists(L1V):
        ties = json.load(open(L1V)).get("folds", {}).get("ties_with_best", [])
    compare_arms = [best] + [a for a in ties if a in arms and a != best]

    print(f"L7-v2 — exit-curve nRMSE, {len(keys)} samples over {len(np.unique(mats))} materials, alpha {alpha}")
    print(f"  learned reference: {best} (lowest out-of-fold field nRMSE c = {field_c[best]:.4f})"
          + (f"; tied arms also compared: {ties}" if ties else ""))
    print(f"\n  {'method':<20} {'exit nRMSE':>11} {'dt50 (h)':>9} {'ms/curve':>9} {'trained?':>9}")
    print(f"  {'POD floor':<20} {np.mean([fl_key[k] for k in keys]):>11.4f} {'':>9} {'':>9} {'—':>9}")
    for a in compare_arms:
        e = np.array([learned[a][k] for k in keys])
        dt = pooled_folds(sub, a, "per_sample_dt_bt50")[0]
        print(f"  {a + ' (learned)':<20} {e.mean():>11.4f} {np.nanmean(dt) / 3600:>9.2f} {'~ms':>9} {'yes':>9}")
    for name, rec in l7["models"].items():
        print(f"  {name:<20} {rec['nrmse']:>11.4f} {rec['dt_bt50'] / 3600:>9.2f} {rec['ms_per_curve']:>9.3f} {'no':>9}")

    out = {"alpha": alpha, "learned_reference": best, "tied_arms": ties, "comparisons": {}, "mde": {}}
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
                if not r["significant"]:
                    out["mde"][f"{a} vs {name}"] = mde_report(e_c - e_l, mats, base=float(e_l.mean()),
                                                              alpha=alpha, effects=(0.0, 0.05, 0.1, 0.2, 0.3),
                                                              trials=200, label=f"{a} vs {name}")
    ratio = min(rec["nrmse"] for rec in l7["models"].values()) / np.mean([learned[best][k] for k in keys])
    if justified:
        verdict = (f"LEARNING IS JUSTIFIED on dataset v2: every classical form is significantly worse than "
                   f"the learned reference on the exit curve; the best closed form is {ratio:.2f}x worse.")
    else:
        verdict = ("A CLASSICAL FORM TIES OR BEATS THE LEARNED ARM. This is the headline of the rung "
                   "and must be reported as such (protocol §2).")
    print(f"\n  VERDICT: {verdict}")
    out["verdict"] = verdict
    out["best_classical_over_learned"] = float(ratio)
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
