"""L5 analysis — operators, the n-width prediction, and DeepOKAN's failure mode.

Three rules are enforced here because each was learned from a defect.

**Collapse detection is MECHANISTIC, not a threshold.** Ten DeepOKAN runs landed
on the same point in function space to within 3e-7, across different p, learning
rates AND seeds. A trained network cannot be seed-invariant, so a run is flagged
collapsed iff its per-condition error vector matches that of a run with a
DIFFERENT seed. This detects the failure by its mechanism (the optimiser ignored
the initialisation) rather than by a hand-picked error cut-off, which would be a
free parameter chosen after seeing the numbers.

**Each family is scored at its own best learning rate**, and for the collapsed
family that best is taken over SURVIVING seeds only. That is deliberately
generous to DeepOKAN: the protocol requires comparing against the strongest
configuration of the competitor, not the first one run (retractions A2/A19/A20).
The collapse rate is reported separately as a first-class result rather than
being allowed to leak into the accuracy number. The verdict is then checked
against the strict variant, which includes collapsed runs.

**Well-formedness is asserted, not assumed.** A stale background process once
overwrote `l3_results.json` and the figure disagreed with the table by 2x
(defect B15).
"""
from __future__ import annotations

import json
import sys

import numpy as np

import metrics

COLLAPSE_TOL = 1e-5


def assert_wellformed(r, path):
    """Guard against a truncated or clobbered results file (defect B15)."""
    n_arms = len(r["arms"])
    fams = {a["family"] for a in r["arms"]}
    assert fams == {"deeponet", "deepokan"}, f"{path}: families {fams}"
    for a in r["arms"]:
        assert set(a["seeds"]) == {str(s) for s in r["seeds"]}, \
            f"{path}: arm {a['family']} p={a['p']} lr={a['lr']} has seeds {list(a['seeds'])}"
        for sd, o in a["seeds"].items():
            n = len(o["novel_material"]["per_sample_nrmse_c"])
            assert n == r["splits"]["novel_material"], \
                f"{path}: {a['family']} p={a['p']} seed {sd} has {n} conditions"
    print(f"{path}: {n_arms} arms x {len(r['seeds'])} seeds, well-formed")
    return r


def merge(paths):
    """Combine several sweeps into one result set, keyed by (family, p, lr).

    The learning-rate grid was extended twice: the initial {1e-3, 3e-4, 1e-4}
    straddled DeepOKAN's optimum at large p, and 1e-3 sat at the TOP EDGE of the
    grid for both families at small p, so the optimum there was untested. Scoring
    each family at its own best setting is only meaningful over the union.
    """
    base = None
    seen = {}
    for path in paths:
        r = assert_wellformed(json.load(open(path)), path)
        if base is None:
            base = {k: v for k, v in r.items() if k != "arms"}
            base["arms"] = []
            base["sources"] = []
        else:
            # Same data and same PCA seed -> the floor must agree exactly.
            for p, v in r["pod_floor"].items():
                if p in base["pod_floor"]:
                    a, b = base["pod_floor"][p]["novel_material"], v["novel_material"]
                    assert abs(a - b) < 1e-9, f"{path}: POD floor for p={p} is {b}, expected {a}"
                else:
                    base["pod_floor"][p] = v
            assert r["splits"] == base["splits"], f"{path}: different splits"
            assert r["steps"] == base["steps"], f"{path}: different step budget"
        for a in r["arms"]:
            key = (a["family"], a["p"], a["lr"])
            assert key not in seen, f"{path}: duplicate arm {key}, first seen in {seen[key]}"
            seen[key] = path
            base["arms"].append(a)
        base["sources"].append(path)
        base["ps"] = sorted(set(base.get("ps", [])) | set(r["ps"]))
    lrs = sorted({a["lr"] for a in base["arms"]})
    print(f"\nmerged {len(paths)} file(s): {len(base['arms'])} arms, "
          f"p in {base['ps']}, lr in {[f'{x:.0e}' for x in lrs]}")
    for f in ("deeponet", "deepokan"):
        for p in base["ps"]:
            n = len({a["lr"] for a in base["arms"] if a["family"] == f and a["p"] == p})
            if n != len(lrs):
                print(f"  NOTE: {f} p={p} covers {n}/{len(lrs)} learning rates")
    return base


def runs_of(r):
    """Flatten to one record per (family, p, lr, seed)."""
    out = []
    for a in r["arms"]:
        for sd, o in a["seeds"].items():
            out.append({
                "family": a["family"], "p": a["p"], "lr": a["lr"], "seed": int(sd),
                "width": a["width"], "n_params": a["n_params"],
                "train": o["train"]["c"], "novel": o["novel_material"]["c"],
                "v": np.array(o["novel_material"]["per_sample_nrmse_c"]),
                "mat": np.array(o["novel_material"]["material_ids"]),
            })
    return out


def mark_collapsed(runs):
    """Collapsed iff equal (to COLLAPSE_TOL) to a run with a DIFFERENT seed."""
    for x in runs:
        x["collapsed"] = False
    for i, x in enumerate(runs):
        for y in runs[i + 1:]:
            if x["seed"] == y["seed"] or x["v"].shape != y["v"].shape:
                continue
            if np.abs(x["v"] - y["v"]).max() < COLLAPSE_TOL:
                x["collapsed"] = y["collapsed"] = True
    return runs


def best_per_p(runs, family, ps, strict=False, min_seeds=3):
    """Mean per-condition vector at the best lr for each p.

    strict=False (primary): best lr judged over SURVIVING seeds -- generous to
    the competitor, as the protocol requires. strict=True: collapsed runs kept.

    `min_seeds` defaults to 3 because protocol rule 5 freezes three seeds as the
    minimum for any reported number. A learning rate that trains on only two of
    three seeds is not a usable configuration, and admitting it would let an
    unreliable arm be scored on its lucky runs. The `min_seeds=2` sensitivity
    variant is reported alongside, and both must agree.
    """
    out = {}
    for p in ps:
        cand = []
        for lr in sorted({x["lr"] for x in runs}):
            g = [x for x in runs
                 if x["family"] == family and x["p"] == p and x["lr"] == lr]
            keep = g if strict else [x for x in g if not x["collapsed"]]
            if len(keep) < min_seeds:
                continue
            V = np.mean([x["v"] for x in keep], axis=0)
            cand.append({"lr": lr, "n_seeds": len(keep),
                         "n_collapsed": sum(x["collapsed"] for x in g),
                         "V": V, "mean": float(V.mean()), "mat": keep[0]["mat"],
                         "train": float(np.mean([x["train"] for x in keep]))})
        if cand:
            out[p] = min(cand, key=lambda c: c["mean"])
    return out


def main():
    paths = sys.argv[1:] or ["results/l5_results.json"]
    r = merge(paths)
    path = " + ".join(paths)
    runs = mark_collapsed(runs_of(r))
    ps = r["ps"]

    print("\n" + "=" * 78)
    print("1. TRAINING COLLAPSE - a degenerate fixed point, found by seed-invariance")
    print("=" * 78)
    for fam in ("deeponet", "deepokan"):
        g = [x for x in runs if x["family"] == fam]
        c = [x for x in g if x["collapsed"]]
        print(f"  {fam:<9} {len(c):>2}/{len(g)} runs collapsed", end="")
        if c:
            worst = max(np.abs(x["v"] - c[0]["v"]).max() for x in c)
            print(f"   (all -> novel {c[0]['novel']:.5f}, agreeing to {worst:.1e})")
            byp = {}
            for x in c:
                byp.setdefault(x["p"], []).append(f"lr{x['lr']:.0e}/s{x['seed']}")
            for p in sorted(byp):
                print(f"             p={p:<4} {len(byp[p])} collapsed: {', '.join(byp[p])}")
        else:
            print()

    print("\n" + "=" * 78)
    print("2. THE n-WIDTH PREDICTION (protocol 6d) - error vs basis size p")
    print("=" * 78)
    tab = {f: best_per_p(runs, f, ps) for f in ("deeponet", "deepokan")}
    print(f"  {'p':>5} {'POD floor':>10} | {'DeepONet':>18} {'lr':>6} |"
          f" {'DeepOKAN':>18} {'lr':>6}")
    for p in ps:
        fl = r["pod_floor"][str(p)]["novel_material"]
        line = f"  {p:>5} {fl:>10.5f} |"
        for f in ("deeponet", "deepokan"):
            b = tab[f].get(p)
            if b is None:
                line += f" {'ALL SEEDS COLLAPSED':>18} {'--':>6} |"
            else:
                tag = f"{b['mean']:.4f} ({b['n_seeds']}s)"
                line += f" {tag:>18} {b['lr']:>6.0e} |"
        print(line)
    fl8 = r["pod_floor"][str(ps[0])]["novel_material"]
    fl128 = r["pod_floor"][str(ps[-1])]["novel_material"]
    print(f"\n  POD floor falls {fl8 / fl128:.1f}x from p={ps[0]} to p={ps[-1]}.")
    for f in ("deeponet", "deepokan"):
        if ps[0] in tab[f] and ps[-1] in tab[f]:
            a, b = tab[f][ps[0]], tab[f][ps[-1]]
            print(f"  {f:<9} moves {a['mean']:.4f} -> {b['mean']:.4f} "
                  f"({b['mean'] / a['mean']:.2f}x), and sits {b['mean'] / fl128:.0f}x "
                  f"above the floor at p={ps[-1]}.")

    print("\n" + "=" * 78)
    print(f"3. PAIRED CLUSTER-ROBUST TESTS (alpha = {metrics.ALPHA_CALIBRATED})")
    print("=" * 78)
    tests = []

    def cmp(na, a, nb, b):
        res = metrics.compare(metrics.ArmResult(na, a["mat"], a["V"]),
                              metrics.ArmResult(nb, b["mat"], b["V"]))
        print("  " + metrics.format_comparison(res))
        tests.append(res)
        return res

    print("\n  Is DeepONet flat in p?  (the n-width prediction says it must fall)")
    for p in ps[1:]:
        if p in tab["deeponet"]:
            cmp(f"deeponet p={ps[0]}", tab["deeponet"][ps[0]],
                f"p={p}", tab["deeponet"][p])

    print("\n  DeepONet vs DeepOKAN, each at its own best lr, same p:")
    for p in ps:
        if p in tab["deeponet"] and p in tab["deepokan"]:
            cmp(f"deeponet p={p}", tab["deeponet"][p],
                f"deepokan p={p}", tab["deepokan"][p])

    print("\n  Best configuration anywhere, family vs family:")
    ba = min(tab["deeponet"].values(), key=lambda c: c["mean"])
    bb = min(tab["deepokan"].values(), key=lambda c: c["mean"])
    best = cmp("deeponet BEST", ba, "deepokan BEST", bb)

    print("\n  Sensitivity — the verdict must survive every scoring rule:")
    variants = {
        "strict (collapsed runs kept)": dict(strict=True, min_seeds=3),
        "lenient (2 surviving seeds allowed)": dict(strict=False, min_seeds=2),
    }
    agree = True
    for label, kw in variants.items():
        vt = {f: best_per_p(runs, f, ps, **kw) for f in ("deeponet", "deepokan")}
        if not vt["deeponet"] or not vt["deepokan"]:
            continue
        va = min(vt["deeponet"].values(), key=lambda c: c["mean"])
        vb = min(vt["deepokan"].values(), key=lambda c: c["mean"])
        print(f"    [{label}]")
        res = cmp("deeponet BEST", va, "deepokan BEST", vb)
        if (res["significant"] != best["significant"]
                or np.sign(res["mean_diff"]) != np.sign(best["mean_diff"])):
            agree = False
    print(f"  -> all scoring rules "
          f"{'AGREE' if agree else 'DISAGREE - do not report'}")

    out = {"path": path, "collapse_tol": COLLAPSE_TOL,
           "collapsed": {f: [{k: x[k] for k in ("p", "lr", "seed", "novel")}
                             for x in runs if x["family"] == f and x["collapsed"]]
                         for f in ("deeponet", "deepokan")},
           "best_per_p": {f: {str(p): {k: b[k] for k in ("lr", "mean", "n_seeds",
                                                         "n_collapsed", "train")}
                              for p, b in tab[f].items()} for f in tab},
           "pod_floor": r["pod_floor"], "tests": tests,
           "scoring_variants_agree": bool(agree)}
    json.dump(out, open("results/l5_analysis.json", "w"), indent=2)
    print("\nwrote results/l5_analysis.json")


if __name__ == "__main__":
    main()
