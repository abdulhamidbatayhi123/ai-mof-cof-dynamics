"""L1 analysis: does data-driven regression transfer to held-out materials?

Reports the rung's verdict with cluster-robust paired CIs, and decomposes the
error into the two things that can cause it:

    total error  =  what the BASIS cannot represent   (the POD floor, = d_n)
                 +  what the REGRESSOR cannot predict (the gap above the floor)

That split is the whole point. If arms sit far above the floor, L1 fails because
the parameter->coefficient map is hard, and more capacity might help. If arms
approach the floor and stall, L1 fails because of the n-width, and no capacity
helps. The two have opposite implications for L5, so they must not be conflated.
"""
from __future__ import annotations

import json

import numpy as np

from metrics import ArmResult, compare, format_comparison

SPLITS = ("train", "novel_condition", "novel_material")


def load(path="results/l1_results.json"):
    return json.load(open(path))


def table(r):
    print("=" * 92)
    print(f"L1 — data-driven interpolation | {r['modes']} POD modes/channel | seeds {r['seeds']}")
    print(f"splits: {r['splits']}")
    print("=" * 92)

    floor = r["pod_floor"]
    print("\nPOD reconstruction floor — the best ANY fixed-basis method can reach:")
    print(f"  {'split':<18} {'nRMSE c':>10} {'nRMSE q':>10} {'nRMSE T':>10}")
    for s in SPLITS:
        f = floor[s]
        print(f"  {s:<18} {f['c']:>10.3e} {f['q']:>10.3e} {f['T']:>10.3e}")

    print("\nArm performance (mean +- sd over seeds):")
    hdr = f"  {'arm':<7} {'split':<17} {'nRMSE c':>16} {'nRMSE q':>16} {'dt_bt50 (h)':>13} {'x floor':>9}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for arm, seeds in r["arms"].items():
        for s in SPLITS:
            cs = [seeds[k][s]["mean"]["c"] for k in seeds]
            qs = [seeds[k][s]["mean"]["q"] for k in seeds]
            dt = [seeds[k][s]["mean"]["dt_bt50"] / 3600 for k in seeds]
            ratio = np.mean(cs) / floor[s]["c"]
            print(f"  {arm:<7} {s:<17} {np.mean(cs):>8.4f}+-{np.std(cs):<6.4f} "
                  f"{np.mean(qs):>8.4f}+-{np.std(qs):<6.4f} "
                  f"{np.mean(dt):>7.2f}+-{np.std(dt):<4.2f} {ratio:>8.1f}x")
        print()


def comparisons(r, split="novel_material", metric="nrmse_c"):
    print("=" * 92)
    print(f"Paired, cluster-robust comparisons on {split}")
    print("=" * 92)
    arms = list(r["arms"])
    seed0 = r["seeds"][0]
    mats = np.array(r["arms"][arms[0]][str(seed0)][split]["material_ids"])

    # average each arm's per-sample score over seeds, keeping sample order
    scores = {}
    for a in arms:
        per_seed = [np.array(r["arms"][a][str(s)][split]["per_sample_nrmse_c"]) for s in r["seeds"]]
        scores[a] = np.mean(per_seed, axis=0)

    best = min(arms, key=lambda a: scores[a].mean())
    print(f"best arm by mean nRMSE(c): {best} = {scores[best].mean():.4f}\n")
    from metrics import ALPHA_CALIBRATED
    for alpha, label in ((0.05, "nominal 95% CI  (empirical FPR 8.5% — over-rejects)"),
                         (ALPHA_CALIBRATED, "CALIBRATED 99.5% CI  (empirical FPR 4.2%)")):
        print(f"  --- {label} ---")
        for a in arms:
            if a == best:
                continue
            res = compare(ArmResult(best, mats, scores[best], metric),
                          ArmResult(a, mats, scores[a], metric),
                          alpha=alpha, n_boot=4000)
            print("    " + format_comparison(res))
        print()
    return scores, mats, best


def verdict(r, scores, best):
    floor = r["pod_floor"]["novel_material"]["c"]
    b = scores[best].mean()
    print("\n" + "=" * 92)
    print("VERDICT")
    print("=" * 92)
    print(f"  best arm on novel materials : nRMSE(c) = {b:.4f}")
    print(f"  POD floor (n-width bound)   : nRMSE(c) = {floor:.4e}")
    print(f"  gap above the floor         : {b / floor:.1f}x")
    print()
    if b / floor > 5:
        print("  The basis is NOT the binding constraint at this rank. The")
        print("  parameter->coefficient regression is. L1 fails as a LEARNING")
        print("  problem, so extra capacity (L2) is the next thing to eliminate.")
    else:
        print("  Arms are at the POD floor: the n-width IS binding. Capacity")
        print("  cannot help, and L2 should be skipped in favour of a nonlinear")
        print("  reconstruction.")
    print()
    print(f"  A 5 % nRMSE on c corresponds to roughly {0.05:.2f} of the inlet")
    print("  concentration in error at every point — visibly wrong breakthrough")
    print("  curves, not a near-miss.")


if __name__ == "__main__":
    r = load()
    table(r)
    scores, mats, best = comparisons(r)
    verdict(r, scores, best)
