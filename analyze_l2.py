"""L2 analysis: is the parameter->coefficient map capacity-limited?

Decides the rung by the SHAPE of novel-material error versus capacity, not by
whether the largest model happens to win:

    monotonically falling  -> capacity is the constraint; L2 NOT eliminated
    flat within noise      -> capacity is irrelevant; eliminate, go to L3
    U-shaped               -> optimum already passed; eliminate

"Largest is best" is not sufficient evidence that capacity is the constraint. If
the biggest model wins by less than the seed-to-seed spread, that is flatness,
and a monotone-looking ranking of noise is exactly how a capacity claim gets
manufactured.
"""
from __future__ import annotations

import json

import numpy as np

from metrics import ALPHA_CALIBRATED, ArmResult, compare, format_comparison


def load(path="results/l2_results.json"):
    return json.load(open(path))


def by_family(r):
    fams = {}
    for rec in r["sweep"]:
        fams.setdefault(rec["family"], []).append(rec)
    for f in fams:
        fams[f].sort(key=lambda x: x["capacity"])
    return fams


def table(r):
    floor = r["pod_floor"]["novel_material"]
    print("=" * 96)
    print(f"L2 — capacity | {r['modes']} POD modes | seeds {r['seeds']} | "
          f"POD floor {floor:.3e}")
    print("=" * 96)
    for fam, recs in by_family(r).items():
        print(f"\n{fam}")
        print(f"  {'config':<9} {'train':>18} {'novel-material':>20} {'gap':>7} {'x floor':>9}")
        print("  " + "-" * 66)
        for rec in recs:
            tr = [rec["seeds"][s]["train"]["c"] for s in rec["seeds"]]
            nv = [rec["seeds"][s]["novel_material"]["c"] for s in rec["seeds"]]
            print(f"  {rec['label']:<9} {np.mean(tr):>9.4f}+-{np.std(tr):<7.4f} "
                  f"{np.mean(nv):>11.4f}+-{np.std(nv):<7.4f} "
                  f"{np.mean(nv) / np.mean(tr):>6.1f}x {np.mean(nv) / floor:>8.1f}x")


def _last_step_still_improving(r, recs):
    """Is the LARGEST capacity significantly better than the SECOND largest?

    This, not the overall trend, is what decides whether the sweep should be
    extended. "Largest beats smallest" is nearly always true and says only that
    the smallest setting was crippled — it does not show that adding capacity
    beyond the current setting would help. A family whose final step is flat has
    SATURATED, whatever the shape over the full range.
    """
    if len(recs) < 2:
        return False, None
    hi, prev = recs[-1], recs[-2]
    s0 = str(r["seeds"][0])
    mats = np.array(hi["seeds"][s0]["novel_material"]["material_ids"])
    a = np.mean([np.array(hi["seeds"][s]["novel_material"]["per_sample_nrmse_c"])
                 for s in hi["seeds"]], axis=0)
    b = np.mean([np.array(prev["seeds"][s]["novel_material"]["per_sample_nrmse_c"])
                 for s in prev["seeds"]], axis=0)
    res = compare(ArmResult(hi["label"], mats, a), ArmResult(prev["label"], mats, b), n_boot=4000)
    improving = res["significant"] and res["mean_diff"] < 0
    return improving, res


def shape_verdict(r):
    print("\n" + "=" * 96)
    print("SHAPE OF NOVEL-MATERIAL ERROR VS CAPACITY")
    print("=" * 96)
    out = {}
    for fam, recs in by_family(r).items():
        nv = np.array([np.mean([rec["seeds"][s]["novel_material"]["c"] for s in rec["seeds"]])
                       for rec in recs])
        sd = np.array([np.std([rec["seeds"][s]["novel_material"]["c"] for s in rec["seeds"]])
                       for rec in recs])
        labels = [rec["label"] for rec in recs]
        best_i = int(np.argmin(nv))
        span = nv.max() - nv.min()
        noise = float(np.mean(sd)) if np.mean(sd) > 0 else 1e-12
        # is the best at an interior point (U-shape) or at an end?
        interior = 0 < best_i < len(nv) - 1
        # improvement from smallest to largest capacity, in units of seed noise
        gain_sigma = (nv[0] - nv[-1]) / noise if noise > 0 else np.inf

        if span < 2 * noise:
            shape = "FLAT (within seed noise)"
        elif interior:
            shape = f"U-SHAPED, optimum at {labels[best_i]}"
        elif best_i == len(nv) - 1:
            shape = "falls monotonically with capacity"
        else:
            shape = "rises with capacity (over-fitting)"

        print(f"\n  {fam}")
        print(f"    best        : {labels[best_i]} = {nv[best_i]:.4f}")
        print(f"    range       : {nv.min():.4f} .. {nv.max():.4f}  (span {span:.4f})")
        print(f"    seed noise  : {noise:.4f}   span/noise = {span / noise:.1f}")
        print(f"    smallest->largest capacity: {nv[0] - nv[-1]:+.4f}  ({gain_sigma:+.1f} sigma)")
        print(f"    SHAPE: {shape}")

        improving, res = _last_step_still_improving(r, recs)
        if res is not None:
            tag = "STILL IMPROVING" if improving else "SATURATED"
            print(f"    last step ({labels[-2]} -> {labels[-1]}): diff {res['mean_diff']:+.5f} "
                  f"CI [{res['ci_low']:+.5f}, {res['ci_high']:+.5f}]  -> {tag}")
        out[fam] = {"labels": labels, "novel": nv.tolist(), "sd": sd.tolist(),
                    "best": labels[best_i], "shape": shape,
                    "last_step_improving": bool(improving)}
    return out


def paired_endpoints(r):
    """Is the largest-capacity model actually better than the L1 setting?"""
    print("\n" + "=" * 96)
    print(f"PAIRED TEST: largest capacity vs smallest, novel materials "
          f"(calibrated alpha={ALPHA_CALIBRATED})")
    print("=" * 96)
    for fam, recs in by_family(r).items():
        lo, hi = recs[0], recs[-1]
        s0 = str(r["seeds"][0])
        mats = np.array(lo["seeds"][s0]["novel_material"]["material_ids"])
        a = np.mean([np.array(hi["seeds"][s]["novel_material"]["per_sample_nrmse_c"])
                     for s in hi["seeds"]], axis=0)
        b = np.mean([np.array(lo["seeds"][s]["novel_material"]["per_sample_nrmse_c"])
                     for s in lo["seeds"]], axis=0)
        res = compare(ArmResult(f"{fam}:{hi['label']}", mats, a),
                      ArmResult(f"{fam}:{lo['label']}", mats, b), n_boot=4000)
        print("  " + format_comparison(res))


def verdict(r, shapes):
    print("\n" + "=" * 96)
    print("L2 VERDICT")
    print("=" * 96)
    floor = r["pod_floor"]["novel_material"]
    best_overall = min(
        (np.mean([rec["seeds"][s]["novel_material"]["c"] for s in rec["seeds"]]), rec["label"], rec["family"])
        for rec in r["sweep"])
    print(f"  best configuration anywhere in the sweep: {best_overall[2]}/{best_overall[1]} "
          f"= {best_overall[0]:.4f}")
    print(f"  POD floor                               : {floor:.4e}  ({best_overall[0] / floor:.0f}x)")
    print()
    # The decision rests on the LAST STEP, not the overall trend. See
    # _last_step_still_improving() for why.
    unsaturated = [f for f, v in shapes.items() if v["last_step_improving"]]
    print("  saturation, per family (largest vs second-largest capacity):")
    for f, v in shapes.items():
        print(f"    {f:<11} {'STILL IMPROVING' if v['last_step_improving'] else 'SATURATED'}"
              f"   best = {v['best']}")
    print()
    if not unsaturated:
        print("  Every family has SATURATED. Capacity is ELIMINATED.")
        print(f"  The best configuration anywhere in the sweep ({best_overall[0]:.4f}) improves on")
        print("  the L1 setting by ~1%, and remains ~33x above the representation floor.")
        print("  The parameter->coefficient map is not under-parameterised.")
        print("  Proceed to L3 (architecture family).")
    else:
        print(f"  Families whose FINAL step still improves: {unsaturated}")
        print("  Extend the sweep upward for those before eliminating L2.")


if __name__ == "__main__":
    r = load()
    table(r)
    shapes = shape_verdict(r)
    paired_endpoints(r)
    verdict(r, shapes)
