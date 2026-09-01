"""Recalibrate the bootstrap level for dataset v2's 48-cluster split.

alpha = 0.005 was calibrated for the legacy split's **12** held-out materials,
where the percentile cluster bootstrap was measured to over-reject at 8.5 % against
a nominal 5 %. Dataset v2 holds out **48** materials over 3947 samples. The
over-rejection shrinks with cluster count (the original sweep measured 8.5 % at 12,
10.7 % at 20, 7.7 % at 60), so keeping 0.005 at 48 clusters would be needlessly
punitive: it would cost power on every null verdict in the ladder, and the nulls
are what this paper is largely made of.

This does two things the original calibration did not:

1. **Recalibrates at the real v2 cluster count**, including the unbalanced cluster
   sizes v2 actually has — conditions per material vary because the screen rejects
   some draws, and cluster-bootstrap coverage depends on that imbalance.

2. **Reports the POWER of the calibrated level**, not just its size. A level that
   controls type-I error but cannot detect a 20 % effect is not a good level, and
   "no difference" is only meaningful alongside what the design could have found.
   The audit's L6 power analysis is generalised here to arbitrary cluster counts.

Output: results/calibration_v2.json
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from metrics import ArmResult, compare


def cluster_sizes_from(root):
    """Real conditions-per-material counts for the held-out materials of a dataset."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    novel = set(man["novel_materials"])
    counts = {}
    for s in man["samples"]:
        if s["mat"] in novel:
            counts[s["mat"]] = counts.get(s["mat"], 0) + 1
    return np.array(sorted(counts.values()))


def simulate(sizes, alpha, effect=0.0, trials=400, seed0=0,
             between_sd=0.02, within_sd=0.003, base=0.05):
    """Rejection rate under a realistic null (effect=0) or alternative.

    The null is NOT "two identical arms". It is two arms that tie on average but
    whose *difference* is clustered by material — some materials favour one arm,
    some the other. That is the realistic case, and it is what makes a naive
    condition-level bootstrap over-reject (measured 32.5 % vs 7.0 %).
    """
    mats = np.repeat(np.arange(len(sizes)), sizes)
    hits = 0
    for s in range(trials):
        rng = np.random.default_rng(seed0 + s)
        adv = rng.normal(0, between_sd, len(sizes))[mats]
        A = base + rng.normal(0, within_sd, mats.size)
        B = base * (1 - effect) + adv + rng.normal(0, within_sd, mats.size)
        hits += compare(ArmResult("A", mats, A), ArmResult("B", mats, B),
                        n_boot=600, seed=s, alpha=alpha)["significant"]
    return 100.0 * hits / trials


def main():
    t0 = time.time()
    out = {}
    for tag, root in (("legacy", "data/parametric"), ("v2", "data/parametric_v2")):
        if not os.path.exists(os.path.join(root, "manifest.json")):
            print(f"  (absent: {root})")
            continue
        sizes = cluster_sizes_from(root)
        print(f"\n{'='*70}\n{tag}: {len(sizes)} held-out materials, "
              f"{sizes.sum()} conditions "
              f"(per material: min {sizes.min()}, median {int(np.median(sizes))}, max {sizes.max()})")
        print(f"{'='*70}")

        print(f"\n  SIZE — empirical false-positive rate under a clustered null")
        print(f"  {'nominal alpha':>14} {'empirical FPR':>15}")
        chosen = None
        sizes_rec = {}
        for a in (0.05, 0.02, 0.01, 0.005, 0.002):
            f = simulate(sizes, a)
            sizes_rec[a] = f
            flag = ""
            if chosen is None and f <= 5.0:
                chosen = a
                flag = "   <- calibrated"
            print(f"  {a:>14.3f} {f:>14.1f} %{flag}")

        if chosen is None:
            print("  => even alpha=0.002 over-rejects on this split.")
            chosen = 0.002

        print(f"\n  POWER at alpha = {chosen} — what this design can actually detect")
        print(f"  {'true effect':>12} {'power':>8}")
        pw = {}
        for eff in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50):
            p = simulate(sizes, chosen, effect=eff)
            pw[eff] = p
            print(f"  {eff*100:>11.0f} % {p:>7.0f} %")
        det = [e for e, p in pw.items() if p >= 80.0]
        mde = min(det) if det else None
        print(f"\n  => minimum detectable effect at 80 % power: "
              f"{f'{mde*100:.0f} %' if mde else '> 50 %'}")
        print(f"  => a 'no difference' verdict on this split excludes improvements "
              f"larger than ~{f'{mde*100:.0f} %' if mde else '50 %'}")

        out[tag] = {"n_clusters": int(len(sizes)), "n_conditions": int(sizes.sum()),
                    "cluster_sizes": sizes.tolist(), "alpha": chosen,
                    "fpr_by_alpha": sizes_rec, "power_by_effect": pw,
                    "mde_at_80pct": mde}

    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/calibration_v2.json", "w"), indent=2)
    print(f"\nwrote results/calibration_v2.json  [{time.time()-t0:.0f}s]")

    if "legacy" in out and "v2" in out:
        l, v = out["legacy"], out["v2"]
        print(f"\n{'='*70}\nWHAT v2 BUYS\n{'='*70}")
        print(f"  clusters      {l['n_clusters']:>3d}  ->  {v['n_clusters']:>3d}")
        print(f"  alpha         {l['alpha']}  ->  {v['alpha']}")
        lm = l["mde_at_80pct"]; vm = v["mde_at_80pct"]
        print(f"  MDE @80%%      {f'{lm*100:.0f} %' if lm else '>50 %'}  ->  "
              f"{f'{vm*100:.0f} %' if vm else '>50 %'}")
        print("\n  Every 'no difference' verdict must be reported with its MDE. A null")
        print("  without a power statement is an absence of evidence, not evidence of")
        print("  absence, and this paper is largely made of nulls.")


if __name__ == "__main__":
    main()
