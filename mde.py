"""Minimum detectable effect for a paired, cluster-robust comparison. ONE implementation.

Rule 7 of this project: **no null is reported without its minimum detectable
effect.** Retraction A22 exists because a null was quoted with a power figure that
came from a simulation resampling residuals i.i.d. across samples — which destroys
the material-level clustering that makes the test hard — and the design turned out
to have 7 % power where 96 % had been claimed.

This module fixes that class of error at the API boundary, the way `metrics.py`
fixes pooled MSE: the power simulation here *measures* the clustering of the real
paired difference and preserves it, so it cannot be run in the i.i.d. form.

How it works
------------
Given the per-sample paired difference `delta = err_B - err_A` and the material of
each sample, the difference is decomposed into

    between-material sd   sd over materials of the per-material mean of delta
    within-material sd    sd of delta about its material mean

exactly as `results/l6_v2_mde.json` recorded for L6-v2. A synthetic pair of arms is
then generated with the SAME cluster sizes, the SAME between/within structure, and
a known relative improvement `effect`, and `metrics.compare` is run at the
calibrated alpha. Power is the rejection rate over trials; the MDE is the smallest
effect whose power reaches 80 %.

The null (effect = 0) is the size check: it must come out near the calibrated
level. If it does not, the alpha is wrong for this design and the verdict may not
be reported.

Usage
-----
    from mde import mde_report
    rep = mde_report(delta, material_ids, base=err_A.mean(), alpha=0.02)
    # rep["power"] = {0.02: 21.5, 0.04: 68.0, ...}, rep["mde_80"] = 0.05, ...

    python mde.py --check-l6-v2      # reproduce the L6-v2 power table from its
                                     # recorded between/within sd, as a self-test
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from metrics import ArmResult, compare

EFFECTS_DEFAULT = (0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50)


def cluster_structure(delta, material_ids):
    """Measured between- and within-material sd of a paired difference."""
    delta = np.asarray(delta, dtype=float)
    material_ids = np.asarray(material_ids)
    mats, inv = np.unique(material_ids, return_inverse=True)
    sums = np.bincount(inv, weights=delta, minlength=len(mats))
    cnts = np.bincount(inv, minlength=len(mats))
    means = sums / cnts
    resid = delta - means[inv]
    between = float(np.std(means, ddof=1)) if len(mats) > 1 else 0.0
    within = float(np.std(resid, ddof=1)) if delta.size > 1 else 0.0
    return {"between_sd": between, "within_sd": within,
            "n_clusters": int(len(mats)), "cluster_sizes": cnts.tolist()}


def simulate_power(cluster_sizes, base, between_sd, within_sd, alpha, effect,
                   trials=400, n_boot=600, seed0=0):
    """Rejection rate of `compare` at `alpha` for a known relative improvement.

    Arm A has error `base`; arm B has error `base * (1 - effect)`, plus a
    material-level advantage drawn with the measured between-material sd (so
    some materials favour A and some B — the realistic, clustered case), plus
    within-material noise with the measured within sd. Nothing is i.i.d. across
    samples that is not i.i.d. in the real data.
    """
    sizes = np.asarray(cluster_sizes, dtype=int)
    mats = np.repeat(np.arange(len(sizes)), sizes)
    hits = 0
    for s in range(trials):
        rng = np.random.default_rng(seed0 + s)
        adv = rng.normal(0.0, between_sd, len(sizes))[mats]
        A = base + rng.normal(0.0, within_sd, mats.size)
        B = base * (1.0 - effect) + adv + rng.normal(0.0, within_sd, mats.size)
        r = compare(ArmResult("A", mats, A), ArmResult("B", mats, B),
                    n_boot=n_boot, seed=s, alpha=alpha)
        hits += int(r["significant"])
    return 100.0 * hits / trials


def mde_report(delta, material_ids, base, alpha, effects=EFFECTS_DEFAULT,
               trials=400, n_boot=600, verbose=True, label=""):
    """Power curve and MDE for the comparison whose paired difference is `delta`."""
    cs = cluster_structure(delta, material_ids)
    power = {}
    for e in effects:
        power[float(e)] = simulate_power(cs["cluster_sizes"], base, cs["between_sd"],
                                         cs["within_sd"], alpha, e,
                                         trials=trials, n_boot=n_boot)
    detectable = [e for e, p in power.items() if e > 0 and p >= 80.0]
    mde = min(detectable) if detectable else None
    rep = {"label": label, "alpha": alpha, "base": float(base),
           "between_sd": cs["between_sd"], "within_sd": cs["within_sd"],
           "between_over_base": cs["between_sd"] / base if base > 0 else float("nan"),
           "n_clusters": cs["n_clusters"], "n_samples": int(np.asarray(delta).size),
           "trials": trials, "n_boot": n_boot,
           "power": {f"{e:.2f}": p for e, p in power.items()},
           "size_at_null": power.get(0.0),
           "mde_80": mde}
    if verbose:
        print(f"  MDE {label}: {cs['n_clusters']} clusters, base {base:.4f}, "
              f"between sd {cs['between_sd']:.4f} ({100 * rep['between_over_base']:.0f} % of base), "
              f"within sd {cs['within_sd']:.4f}, alpha {alpha}")
        print(f"    {'true effect':>12} {'power':>7}")
        for e, p in power.items():
            print(f"    {100 * e:>11.0f} % {p:>6.0f} %")
        print(f"    -> size at the null {power.get(0.0, float('nan')):.1f} % "
              f"(should be near {100 * alpha:.0f}–{100 * 2.5 * alpha:.0f} %; the calibrated level targets 5 %)")
        print(f"    -> minimum detectable effect at 80 % power: "
              f"{f'{100 * mde:.0f} %' if mde else '> ' + f'{100 * max(effects):.0f} %'}")
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-l6-v2", action="store_true",
                    help="reproduce the L6-v2 power table from results/l6_v2_mde.json")
    ap.add_argument("--trials", type=int, default=400)
    args = ap.parse_args()

    if args.check_l6_v2:
        rec = json.load(open("results/l6_v2_mde.json"))
        folds = json.load(open("results/l6_v2_folds.json"))
        man = json.load(open("data/parametric_v2/manifest.json"))
        counts = {}
        for s in man["samples"]:
            counts[s["mat"]] = counts.get(s["mat"], 0) + 1
        sizes = [counts[int(m)] for m in folds["material_to_fold"]]
        print(f"L6-v2 recorded: between {rec['between_sd']:.4f}, within {rec['within_sd']:.4f}, "
              f"base {rec['base']:.4f}, {rec['n_clusters']} clusters; RESULTS.md quotes "
              f"22 / 68 / 97 / 100 % at 2 / 4 / 6 / 10 %")
        print(f"  {'effect':>8} {'power':>7}")
        out = {}
        for e in (0.0, 0.02, 0.04, 0.06, 0.10):
            p = simulate_power(sizes, rec["base"], rec["between_sd"], rec["within_sd"],
                               0.02, e, trials=args.trials)
            out[e] = p
            print(f"  {100 * e:>7.0f} % {p:>6.1f} %")
        json.dump({"source": "results/l6_v2_mde.json", "alpha": 0.02,
                   "power": {f"{e:.2f}": p for e, p in out.items()}},
                  open("results/l6_v2_mde_check.json", "w"), indent=2)
        print("wrote results/l6_v2_mde_check.json")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
