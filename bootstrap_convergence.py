"""Are the paper's confidence intervals converged, or are we quoting Monte Carlo noise?

WHY THIS SCRIPT EXISTS. Every interval in this paper is a percentile cluster
bootstrap from `metrics.compare`, whose default is `n_boot = 2000`. That default was
never justified anywhere, and a percentile interval is a Monte Carlo estimate of a
quantile: its endpoints have their own sampling error, which falls only as
1/sqrt(n_boot) and is WORST in the tails -- which is exactly where alpha/2 and
1 - alpha/2 live, and exactly what the paper quotes.

It surfaced while giving `results/l5_fno_verdict.json` a script. The file reproduced
to the bit at n_boot = 2000 (so the unowned number was right), but at n_boot = 4000
L5's headline lower bound moved from +0.00035 to +0.00015 -- a factor of 2.3 on the
number a referee reads as "how sure are you". The effect itself is +0.00488, so
significance never came into question; the reported PRECISION did.

This is not a claim that any verdict is wrong. It is a measurement of how much of
each quoted endpoint is signal and how much is the resampler, and it is the kind of
thing that should be known before a number is printed rather than after a referee
asks.

WHAT IT MEASURES. For each comparison it can reconstruct cheaply, the interval at a
ladder of n_boot values, plus a seed-to-seed spread at the production n_boot (the
bootstrap is seeded, so the same seed reproduces exactly -- the spread across SEEDS
is the honest estimate of the endpoint's own Monte Carlo error).

    python bootstrap_convergence.py

Writes results/bootstrap_convergence.json.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

from metrics import ArmResult, compare

LADDER = (1000, 2000, 4000, 8000, 20000, 50000, 200000)
SEEDS_MC = range(12)          # 12 independent resamplers at the production setting
PRODUCTION = 200000


def find_arm(sources, family, p, lr, seeds, split="novel_material"):
    """The arm with this (family, p, lr) among the files l5_merged.json merged.

    The merge recorded which learning rate it selected per p but not which FILE
    that arm came from, and the sweep is spread over six of them.
    """
    ss = [str(s) for s in seeds]
    for fname in sources:
        path = os.path.join("results", fname)
        if not os.path.exists(path):
            continue
        for a in json.load(open(path)).get("arms", []):
            if (a.get("family") == family and a.get("p") == p
                    and math.isclose(float(a.get("lr", -1)), float(lr), rel_tol=1e-9)
                    and all(s in a.get("seeds", {}) and split in a["seeds"][s] for s in ss)):
                return a
    return None


def _cmp(a_name, b_name, mats, va, vb, alpha, n_boot, seed=0):
    return compare(ArmResult(a_name, mats, va), ArmResult(b_name, mats, vb),
                   alpha=alpha, n_boot=n_boot, seed=seed)


def collect():
    """Every comparison whose per-sample arrays live in a SMALL results file."""
    cases = []

    # ---- L5: the best DeepONet against the best FNO (the rung's headline) ----
    import analyze_l5_fno as A
    fno = json.load(open(A.FNO)); onet = json.load(open(A.ONET_HI))
    seeds = fno["seeds"]
    fa = A.complete(fno["arms"], seeds)
    best_fno = min(fa, key=lambda x: A.arm_mean(x, seeds))
    oa = A.complete(onet["arms"], seeds)
    merged = json.load(open(A.MERGED))
    sel = {k: v for k, v in merged["selected"].items() if k.startswith("deeponet_p")}
    bp = int(min(sel, key=lambda k: sel[k]["mean"]).split("_p")[1])
    bo = next(x for x in oa if x["family"] == "deeponet" and x["p"] == bp)
    vo, mo = A.seed_mean_per_sample(bo, seeds)
    vf, mf = A.seed_mean_per_sample(best_fno, seeds)
    assert np.array_equal(mo, mf)
    cases.append(("L5 DeepONet vs FNO", "DeepONet", "FNO", mo, vo, vf, A.ALPHA))

    # ---- L5: DeepONet flat in p, p=8 against p=128 (the "flat" null) ---------
    # Each p at ITS OWN best learning rate, as l5_merged.json selected them --
    # p=8 at lr 0.01, p=128 at lr 0.003, which live in two different source files.
    # The first version of this script took both arms from l5_onet_hi.json, i.e.
    # both at lr 0.01, where p=128 has not converged at all: it reported a
    # significant -0.10 where the rung reports a null spanning zero. That is not
    # the paper's comparison and reporting it as such would have invented a
    # contradiction. Select the way the merge selected.
    sel_p8 = merged["selected"]["deeponet_p8"]
    sel_p128 = merged["selected"]["deeponet_p128"]
    a8 = find_arm(merged["sources"], "deeponet", 8, sel_p8["lr"], seeds)
    a128 = find_arm(merged["sources"], "deeponet", 128, sel_p128["lr"], seeds)
    if a8 is not None and a128 is not None:
        v8, m8 = A.seed_mean_per_sample(a8, seeds)
        v128, m128 = A.seed_mean_per_sample(a128, seeds)
        if not np.array_equal(m8, m128):
            raise AssertionError("p=8 and p=128 scored on different samples")
        # sanity: the means must match what the merge recorded, or we have the
        # wrong arm and every number below would be about something else.
        for got, want, name in ((float(np.mean(v8)), sel_p8["mean"], "p=8"),
                                (float(np.mean(v128)), sel_p128["mean"], "p=128")):
            if not math.isclose(got, want, rel_tol=1e-6):
                raise AssertionError(f"{name}: reconstructed {got:.6f} but the merge "
                                     f"recorded {want:.6f} -- wrong arm")
        cases.append(("L5 DeepONet p=8 vs p=128 (the flat-in-p null, each at its own best lr)",
                      "p=8", "p=128", m8, v8, v128, A.ALPHA))

    return cases


def main():
    out = {"_what": "convergence of the percentile cluster bootstrap endpoints the "
                    "paper quotes, against n_boot",
           "_why": "metrics.compare defaults to n_boot=2000; a percentile interval "
                   "is a Monte Carlo quantile estimate and its endpoints carry their "
                   "own error, worst in the tails, which is where alpha/2 lives.",
           "_production_n_boot": PRODUCTION,
           "cases": {}}

    for label, an, bn, mats, va, vb, alpha in collect():
        print(f"\n{'=' * 92}\n{label}   (alpha {alpha}, {np.unique(mats).size} clusters)\n{'=' * 92}")
        ladder = {}
        print(f"  {'n_boot':>8}  {'ci_low':>12}  {'ci_high':>12}   verdict")
        for nb in LADDER:
            c = _cmp(an, bn, mats, va, vb, alpha, nb)
            ladder[str(nb)] = {"ci_low": c["ci_low"], "ci_high": c["ci_high"],
                               "significant": c["significant"]}
            print(f"  {nb:>8}  {c['ci_low']:>+12.6f}  {c['ci_high']:>+12.6f}   "
                  f"{'SIGNIFICANT' if c['significant'] else 'ns'}")

        # the honest Monte Carlo error: independent resamplers at the production setting
        los, his, sigs = [], [], []
        for s in SEEDS_MC:
            c = _cmp(an, bn, mats, va, vb, alpha, PRODUCTION, seed=s)
            los.append(c["ci_low"]); his.append(c["ci_high"]); sigs.append(c["significant"])
        mean_diff = float(np.mean(va - vb))
        mc = {"n_resamplers": len(los),
              "ci_low_mean": float(np.mean(los)), "ci_low_sd": float(np.std(los)),
              "ci_low_min": float(np.min(los)), "ci_low_max": float(np.max(los)),
              "ci_high_mean": float(np.mean(his)), "ci_high_sd": float(np.std(his)),
              "verdict_stable": bool(len(set(sigs)) == 1),
              "verdict": bool(sigs[0])}
        print(f"  {len(los)} independent resamplers at n_boot={PRODUCTION}:")
        print(f"    ci_low  {mc['ci_low_mean']:+.6f} +/- {mc['ci_low_sd']:.6f} "
              f"(range {mc['ci_low_min']:+.6f} to {mc['ci_low_max']:+.6f})")
        print(f"    ci_high {mc['ci_high_mean']:+.6f} +/- {mc['ci_high_sd']:.6f}")
        print(f"    significance stable across resamplers: {mc['verdict_stable']}")
        # how much of the quoted endpoint is resampler noise
        if mc["ci_low_mean"] != 0:
            share = abs(mc["ci_low_sd"] / mc["ci_low_mean"])
            print(f"    the lower bound's own Monte Carlo sd is {100 * share:.1f} % of it")
            mc["ci_low_mc_sd_share"] = float(share)
        mc["mean_diff"] = mean_diff
        out["cases"][label] = {"alpha": alpha, "n_clusters": int(np.unique(mats).size),
                               "mean_diff": mean_diff, "ladder": ladder, "monte_carlo": mc}

    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/bootstrap_convergence.json", "w"), indent=1)
    print("\nwrote results/bootstrap_convergence.json")


if __name__ == "__main__":
    main()
