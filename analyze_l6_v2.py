"""The L6-v2 verdict: the Damkohler slope test, plus the pooled estimand with its MDE.

Estimands and their order are frozen in `PREREG_L6_v2.md`, committed before any arm
trained. This script computes them; it does not choose them.

  PRIMARY    slope of the per-material paired difference on log10(Da).
             H1-v2 predicts a POSITIVE slope: separation pays most at low Da.
  SECONDARY  pooled mean difference, reportable ONLY with its minimum detectable
             effect (retraction A22 exists because a pooled null was quoted
             without one).

Nothing here is typed into a document by hand — defect B21 was a table and a code
block in RESULTS.md disagreeing because one of them was transcribed.
"""
from __future__ import annotations

import json
import os

import numpy as np

from metrics import ArmResult, compare
from run_l6_v2 import ALPHA_V2, damkohler_per_material, slope_test

RES = "results/l6_v2_results.json"


def per_material(res, arm):
    """Mean nRMSE(c) per material, pooled over folds and seeds. Each material
    appears in exactly one fold, so this is 240 independent held-out estimates."""
    acc = {}
    for f, rec in res["folds"].items():
        a = rec["arms"].get(arm, {})
        for s, r in a.items():
            if "per_sample_nrmse_c" not in r:
                continue
            for e, m in zip(r["per_sample_nrmse_c"], r["material_ids"]):
                acc.setdefault(int(m), []).append(float(e))
    return {m: float(np.mean(v)) for m, v in acc.items()}


def flat(res, arm):
    """Per-sample values and material ids, pooled over folds and seeds."""
    v, m = [], []
    for f, rec in res["folds"].items():
        a = rec["arms"].get(arm, {})
        for s, r in sorted(a.items()):
            if "per_sample_nrmse_c" not in r:
                continue
            v += list(r["per_sample_nrmse_c"])
            m += list(r["material_ids"])
    return np.asarray(v), np.asarray(m)


def main():
    if not os.path.exists(RES):
        raise SystemExit(f"{RES} missing — run run_l6_v2.py first")
    res = json.load(open(RES))
    done = sorted(int(f) for f in res["folds"])
    print(f"L6-v2 — design {res['design']}, {len(done)} of {res['n_folds']} folds: {done}")
    if len(done) < res["n_folds"]:
        print("  ⚠ INCOMPLETE. Numbers below are provisional and may not be reported.")

    ck = res.get("checks", {})
    kin = ck.get("kinetic_key", "?")
    print(f"\n  invalidation checks: kinetic object '{kin}' "
          f"R2={ck.get('descriptor_r2', {}).get(kin, float('nan')):+.4f} "
          f"({'hidden' if ck.get('kinetic_hidden') else 'RECOVERABLE — INVALID'}); "
          f"Da spans {ck.get('da', {}).get('decades', float('nan')):.2f} decades")

    arms = sorted({a for f in res["folds"].values() for a in f["arms"]})
    print(f"\n{'arm':16s} {'materials':>10s} {'mean nRMSE(c)':>14s}")
    pm = {}
    for a in arms:
        pm[a] = per_material(res, a)
        v, _ = flat(res, a)
        print(f"{a:16s} {len(pm[a]):10d} {v.mean():14.4f}")

    if not {"joint", "separate"} <= set(arms):
        print("\n  joint/separate not both present; nothing to compare.")
        return

    da = damkohler_per_material(res["root"])
    delta = {m: pm["separate"][m] - pm["joint"][m]
             for m in set(pm["separate"]) & set(pm["joint"])}

    print(f"\n{'='*72}\nPRIMARY — slope of (separate − joint) on log10(Da), alpha={ALPHA_V2}\n{'='*72}")
    st = slope_test(delta, da, alpha=ALPHA_V2)
    print(f"  materials      : {st['n_materials']}")
    print(f"  log10 Da range : {st['log10_da_range'][0]:.2f} to {st['log10_da_range'][1]:.2f}")
    print(f"  slope          : {st['slope']:+.5f}  CI [{st['ci_low']:+.5f}, {st['ci_high']:+.5f}]")
    print(f"  pearson r      : {st['pearson_r']:+.3f}")
    if not st["significant"]:
        verdict = ("SLOPE NOT SIGNIFICANT. The separate-vs-joint difference does not vary "
                   "systematically with Damkohler across the tested range. H1-v2 is NOT "
                   "SUPPORTED, and unlike the legacy null this covers the "
                   "kinetically-controlled regime rather than only near-equilibrium.")
    elif st["slope"] > 0:
        verdict = ("SLOPE POSITIVE AND SIGNIFICANT. Separation's advantage grows as "
                   "Damkohler falls — H1-v2 SUPPORTED, with the mechanism measured "
                   "rather than asserted.")
    else:
        verdict = ("SLOPE NEGATIVE AND SIGNIFICANT. Separation gets WORSE as kinetics "
                   "matter more. This refutes the mechanism as well as the hypothesis, "
                   "and is reported in those words.")
    print(f"\n  -> {verdict}")

    print(f"\n{'='*72}\nSECONDARY — pooled mean difference (never quoted without its MDE)\n{'='*72}")
    vj, mj = flat(res, "joint")
    vs, ms = flat(res, "separate")
    r = compare(ArmResult("joint", mj, vj), ArmResult("separate", ms, vs), alpha=ALPHA_V2)
    print(f"  joint {r['mean_a']:.4f} vs separate {r['mean_b']:.4f} | "
          f"diff {r['mean_diff']:+.5f} CI [{r['ci_low']:+.5f}, {r['ci_high']:+.5f}]  "
          f"{'SIGNIFICANT' if r['significant'] else 'NO DIFFERENCE'}")
    print(f"  clusters: {r['n_materials']}")

    d_arr = np.array([delta[m] for m in sorted(delta)])
    print(f"\n  between-material sd of the difference: {d_arr.std(ddof=1):.4f} "
          f"({d_arr.std(ddof=1)/vj.mean()*100:.0f} % of the base error)")
    print(f"  -> MDE must be quoted with this verdict. See results/l6_power_corrected.json;\n"
          f"     recompute at {r['n_materials']} clusters before publishing the null.")

    out = {"folds_done": done, "n_folds": res["n_folds"],
           "complete": len(done) == res["n_folds"],
           "per_material": {a: pm[a] for a in pm},
           "slope_test": st, "slope_verdict": verdict,
           "pooled": r, "between_material_sd": float(d_arr.std(ddof=1))}
    json.dump(out, open("results/l6_v2_verdict.json", "w"), indent=2)
    print("\nwrote results/l6_v2_verdict.json")


if __name__ == "__main__":
    main()
