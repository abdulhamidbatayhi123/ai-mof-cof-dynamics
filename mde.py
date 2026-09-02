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

A synthetic paired difference is then generated with the SAME cluster sizes and
the SAME between/within structure plus a known relative improvement `effect`, and
`metrics.compare` is run at the calibrated alpha. Power is the rejection rate over
trials; the MDE is the smallest effect whose power reaches 80 %.

Two details that were wrong in the first version of this file (retraction A25):

* The DIFFERENCE is simulated directly. Drawing within-material noise for each
  arm separately and subtracting gives a difference whose within sd is sqrt(2)
  times the measured one, which understates power and overstates every MDE.
* The measured between-material sd of per-material means contains a within^2/n_m
  contribution; the material-level advantage is drawn with that removed, so the
  simulated difference reproduces the measured structure rather than exceeding it.

`self_test()` checks both: `cluster_structure` of a simulated difference must
recover the input sds within a few per cent.

Usage
-----
    from mde import mde_report
    rep = mde_report(delta, material_ids, base=err_A.mean(), alpha=0.02)
    # rep["power"] = {"0.02": 21.5, ...}, rep["mde_80"] = 0.05, ...

    python mde.py --self-test
    python mde.py --check-l6-v2      # recompute the L6-v2 power table from its
                                     # recorded between/within sd
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


def simulate_difference(cluster_sizes, base, between_sd, within_sd, effect, rng):
    """One synthetic paired difference D = err_B - err_A with the measured structure.

    `between_sd` is the sd of per-material MEANS of the real difference, which
    includes a within^2/n_m share; the material-level advantage is drawn with that
    share removed so that `cluster_structure(D)` reproduces the inputs.
    """
    sizes = np.asarray(cluster_sizes, dtype=int)
    mats = np.repeat(np.arange(len(sizes)), sizes)
    pure = float(np.sqrt(max(between_sd ** 2 - np.mean(within_sd ** 2 / sizes), 0.0)))
    adv = rng.normal(0.0, pure, len(sizes))[mats]
    return -base * effect + adv + rng.normal(0.0, within_sd, mats.size), mats


def simulate_power(cluster_sizes, base, between_sd, within_sd, alpha, effect,
                   trials=400, n_boot=600, seed0=0):
    """Rejection rate of `compare` at `alpha` for a known relative improvement.

    Arm A has error `base`; arm B is better by `effect` (relative), plus a
    material-level advantage with the measured between-material sd (some
    materials favour A and some B — the realistic, clustered case), plus
    within-material noise with the measured within sd. Nothing is i.i.d. across
    samples that is not i.i.d. in the real data.
    """
    hits = 0
    for s in range(trials):
        rng = np.random.default_rng(seed0 + s)
        D, mats = simulate_difference(cluster_sizes, base, between_sd, within_sd, effect, rng)
        A = np.full(mats.size, base)
        r = compare(ArmResult("A", mats, A), ArmResult("B", mats, A + D),
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
              f"(the calibrated level targets 5 %)")
        print(f"    -> minimum detectable effect at 80 % power: "
              f"{f'{100 * mde:.0f} %' if mde else '> ' + f'{100 * max(effects):.0f} %'}")
    return rep


def self_test(between=0.0104, within=0.0205, sizes=(17,) * 240, trials=200, tol=0.06):
    """The simulated difference must reproduce the measured structure."""
    rng = np.random.default_rng(0)
    bs, ws = [], []
    for _ in range(trials):
        D, mats = simulate_difference(sizes, 0.05, between, within, 0.0, rng)
        cs = cluster_structure(D, mats)
        bs.append(cs["between_sd"]); ws.append(cs["within_sd"])
    b, w = float(np.mean(bs)), float(np.mean(ws))
    ok = abs(b / between - 1) < tol and abs(w / within - 1) < tol
    print(f"self-test: input between {between:.4f} within {within:.4f} -> "
          f"recovered between {b:.4f} within {w:.4f}  {'OK' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit("mde.py self-test FAILED: the simulation does not reproduce the measured structure")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-l6-v2", action="store_true",
                    help="recompute the L6-v2 power table from results/l6_v2_mde.json")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--trials", type=int, default=400)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if args.check_l6_v2:
        self_test()
        rec = json.load(open("results/l6_v2_mde.json"))
        folds = json.load(open("results/l6_v2_folds.json"))
        man = json.load(open("data/parametric_v2/manifest.json"))
        counts = {}
        for s in man["samples"]:
            counts[s["mat"]] = counts.get(s["mat"], 0) + 1
        sizes = [counts[int(m)] for m in folds["material_to_fold"]]
        print(f"L6-v2 recorded: between {rec['between_sd']:.4f}, within {rec['within_sd']:.4f}, "
              f"base {rec['base']:.4f}, {rec['n_clusters']} clusters; RESULTS.md quoted "
              f"22 / 68 / 97 / 100 % at 2 / 4 / 6 / 10 % (the A25 table, inflated noise)")
        print(f"  {'effect':>8} {'power':>7}")
        out = {}
        for e in (0.0, 0.01, 0.02, 0.03, 0.04, 0.06, 0.10):
            p = simulate_power(sizes, rec["base"], rec["between_sd"], rec["within_sd"],
                               0.02, e, trials=args.trials)
            out[e] = p
            print(f"  {100 * e:>7.0f} % {p:>6.1f} %")
        det = [e for e, p in out.items() if e > 0 and p >= 80.0]
        json.dump({"source": "results/l6_v2_mde.json", "alpha": 0.02, "trials": args.trials,
                   "power": {f"{e:.2f}": p for e, p in out.items()},
                   "mde_80": min(det) if det else None,
                   "note": "corrected simulation (A25): the difference is simulated directly with the measured "
                           "between/within structure; the earlier table drew within noise for each arm separately"},
                  open("results/l6_v2_mde_check.json", "w"), indent=2)
        print(f"  -> MDE at 80 % power: {f'{100 * min(det):.0f} %' if det else '> 10 %'}")
        print("wrote results/l6_v2_mde_check.json")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
