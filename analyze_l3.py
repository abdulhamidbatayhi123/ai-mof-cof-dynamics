"""L3 analysis: does the edge-function family matter at matched parameters?

This is the direct test of H2, and of the premise behind PIKAN/DeepOKAN. The
verdict must be stated in words, because a null here is the result — not a
failure to find one.

Two things are checked separately and must not be conflated:

  ACCURACY  — is any family significantly better at matched parameters?
  ROBUSTNESS — is any family more variable across seeds? Shukla et al. report
               that orthogonal-polynomial KANs "may diverge for different random
               seeds", which is a defect that a mean-only comparison hides.
"""
from __future__ import annotations

import json

import numpy as np

from metrics import ALPHA_CALIBRATED, ArmResult, compare, format_comparison

FAMILIES = ("mlp", "rbf_kan", "cheby_kan")


def load(path="results/l3_results.json"):
    return json.load(open(path))


def assert_wellformed(r):
    """Refuse to analyse a results file that does not match its own run configuration.

    A results file was once silently clobbered by a stale background process
    writing to the same path: the analysis had already been run on the correct
    file, but the figure built later from the same path plotted an older,
    handicapped run — and the figure disagreed with the table by a factor of two.
    Nothing in the pipeline noticed.

    Structural assertions are cheap and catch exactly that. See defect B15.
    """
    arms = r["arms"]
    if not arms:
        raise AssertionError("results file contains no arms")
    n_lr = len({a.get("lr") for a in arms})
    if any("lr" not in a for a in arms):
        raise AssertionError(
            "some arms have no 'lr' key — this file predates the learning-rate "
            "sweep and is stale. Re-run run_l3.py."
        )
    fams = {a["family"] for a in arms}
    budgets = {a["budget"] for a in arms}
    expected = len(fams) * len(budgets) * n_lr
    if len(arms) != expected:
        raise AssertionError(
            f"expected {expected} arms ({len(fams)} families x {len(budgets)} "
            f"budgets x {n_lr} learning rates) but found {len(arms)} — the file is "
            f"incomplete or was overwritten mid-run"
        )
    for a in arms:
        if set(a["seeds"]) != {str(s) for s in r["seeds"]}:
            raise AssertionError(f"arm {a['family']}@{a['budget']} is missing seeds")

    # THE NEVER-TRAINED GUARD (defect B24, audit 2026-08-30).
    #
    # `best_step == 0` means the validation loss never improved on the randomly
    # initialised network, so the recorded error is the error of that
    # initialisation. In the original 54-run sweep this happened 11 times, and
    # `best_lr_arms` — which picks the LOWEST error per (budget, family) — had no
    # way to see it. For cheby_kan at the 200k budget BOTH learning rates were
    # untrained, so the published cell (0.1263) was 3/3 random initialisation
    # presented as an architecture measurement.
    #
    # An untrained network losing to a trained one is an observation about
    # optimisation, not about generalisation, and the two are not interchangeable.
    # Refuse the file rather than let one through again.
    # A never-trained ARM is excluded by best_lr_arms (below). That is the right
    # response: a learning rate at which a family cannot train is a real and
    # informative observation about optimisation, and discarding the whole sweep
    # because one configuration diverged would throw away the evidence.
    #
    # What is NOT survivable is a (budget, family) cell with no clean arm left,
    # because then there is no honest number to report for it — which is exactly
    # what produced A19, where BOTH of cheby_kan@200k's learning rates were
    # untrained and `best_lr_arms` reported the initialisation error as a result.
    cells = {}
    for a in arms:
        cells.setdefault((a["budget"], a["family"]), []).append(a)
    empty = [f"{fam}@{bud:,}" for (bud, fam), v in cells.items()
             if all(_is_untrained(a) for a in v)]
    if empty:
        raise AssertionError(
            "these (budget, family) cells have NO configuration that trained — every "
            "learning rate returned the random initialisation, so there is no honest "
            "number to report for them:\n    " + "\n    ".join(sorted(empty)) +
            "\n  This is the condition that produced retraction A19. Widen the "
            "learning-rate grid or raise `steps` for these cells (defect B24)."
        )
    return True


def _is_untrained(arm):
    """True if ANY seed of this arm failed to improve on its initialisation."""
    for rec in arm["seeds"].values():
        if rec.get("never_trained") or rec.get("early_stop", {}).get("best_step") == 0:
            return True
    return False


def untrained_report(r):
    """Every arm excluded for never training, so exclusions are visible not silent."""
    return [f"{a['family']}@{a['budget']:,} lr={a.get('lr'):.0e}"
            for a in r["arms"] if _is_untrained(a)]


def best_lr_arms(r):
    """Collapse the lr sweep, keeping each (budget, family) at ITS best lr.

    Protocol section 3: an arm is compared against the STRONGEST configuration of
    its competitor. Reporting all learning rates would let a family look bad
    purely because one of its settings was poor.
    """
    best = {}
    for a in r["arms"]:
        # EXCLUDE never-trained arms (defect B24 / retraction A19). Without this,
        # an arm whose error IS its random initialisation can win the min() and be
        # reported as an architecture result — which is what happened at
        # cheby_kan@200k, where both learning rates were untrained.
        if _is_untrained(a):
            continue
        key = (a["budget"], a["family"])
        nv = np.mean([a["seeds"][s]["novel_material"]["c"] for s in a["seeds"]])
        if key not in best or nv < best[key][0]:
            best[key] = (nv, a)
    return [v[1] for v in best.values()]


def table(r):
    r = dict(r, arms=best_lr_arms(r))
    floor = r["pod_floor"]["novel_material"]
    print("=" * 100)
    print(f"L3 — architecture family at MATCHED PARAMETERS | depth {r['depth']} | "
          f"{r['steps']} steps | seeds {r['seeds']}")
    print(f"POD floor (novel-material) {floor:.3e}")
    print("=" * 100)
    budgets = sorted({a["budget"] for a in r["arms"]})
    for b in budgets:
        print(f"\nparameter budget ~{b:,}")
        print(f"  {'family':<11} {'width':>6} {'params':>10} {'train':>18} "
              f"{'novel-material':>20} {'seed sd':>9} {'x floor':>9}")
        print("  " + "-" * 88)
        for a in [x for x in r["arms"] if x["budget"] == b]:
            tr = [a["seeds"][s]["train"]["c"] for s in a["seeds"]]
            nv = [a["seeds"][s]["novel_material"]["c"] for s in a["seeds"]]
            print(f"  {a['family']:<11} {a['width']:>6} {a['n_params']:>10,} "
                  f"{np.mean(tr):>9.4f}+-{np.std(tr):<7.4f} "
                  f"{np.mean(nv):>11.4f}+-{np.std(nv):<7.4f} "
                  f"{np.std(nv):>9.4f} {np.mean(nv) / floor:>8.1f}x")


def head_to_head(r):
    print("\n" + "=" * 100)
    print(f"PAIRED COMPARISONS at matched parameters (calibrated alpha={ALPHA_CALIBRATED})")
    print("=" * 100)
    out = {}
    for b in sorted({a["budget"] for a in r["arms"]}):
        arms = {a["family"]: a for a in r["arms"] if a["budget"] == b}
        if len(arms) < 2:
            continue
        print(f"\n  budget ~{b:,}")
        s0 = str(r["seeds"][0])
        any_fam = next(iter(arms.values()))
        mats = np.array(any_fam["seeds"][s0]["novel_material"]["material_ids"])
        score = {f: np.mean([np.array(a["seeds"][s]["novel_material"]["per_sample_nrmse_c"])
                             for s in a["seeds"]], axis=0) for f, a in arms.items()}
        fams = list(arms)
        for i in range(len(fams)):
            for j in range(i + 1, len(fams)):
                A, B = fams[i], fams[j]
                res = compare(ArmResult(A, mats, score[A]), ArmResult(B, mats, score[B]),
                              n_boot=4000)
                print("    " + format_comparison(res))
                out[(b, A, B)] = res["significant"]
    return out


def robustness(r):
    print("\n" + "=" * 100)
    print("ROBUSTNESS — seed-to-seed variability (a mean-only comparison hides this)")
    print("=" * 100)
    print(f"  {'family':<11} {'mean sd across budgets':>24} {'worst single-budget sd':>24}")
    print("  " + "-" * 62)
    for f in FAMILIES:
        sds = [np.std([a["seeds"][s]["novel_material"]["c"] for s in a["seeds"]])
               for a in r["arms"] if a["family"] == f]
        if sds:
            print(f"  {f:<11} {np.mean(sds):>24.5f} {max(sds):>24.5f}")


def verdict(r, sig):
    print("\n" + "=" * 100)
    print("L3 VERDICT")
    print("=" * 100)
    floor = r["pod_floor"]["novel_material"]
    best = min(((np.mean([a["seeds"][s]["novel_material"]["c"] for s in a["seeds"]]),
                 a["family"], a["budget"]) for a in r["arms"]))
    print(f"  best arm anywhere: {best[1]} at budget {best[2]:,} = {best[0]:.4f}"
          f"  ({best[0] / floor:.0f}x floor)")
    n_sig = sum(1 for v in sig.values() if v)
    print(f"  significant pairwise differences: {n_sig} of {len(sig)}")
    print()
    if n_sig == 0:
        print("  No family is distinguishable from any other at matched parameters.")
        print("  H2 is SUPPORTED: architecture family does not govern generalisation here.")
        print("  The basis is eliminated. Proceed to L4 (physics as a loss).")
    else:
        print("  Some pairs differ. Report WHICH, at WHICH budget, and whether the")
        print("  ordering is consistent across budgets — a difference that flips sign")
        print("  between budgets is not an architecture effect.")


if __name__ == "__main__":
    raw = load()
    assert_wellformed(raw)
    # Collapse the learning-rate sweep ONCE, here, so every downstream function
    # sees the same arms. Doing it per-function invites one of them to drift.
    r = dict(raw, arms=best_lr_arms(raw))
    n_lr = len({a.get("lr") for a in raw["arms"]})
    print(f"(learning-rate sweep: {n_lr} values; each family reported at ITS best — "
          f"{len(raw['arms'])} runs -> {len(r['arms'])} arms)\n")
    table(raw)          # table() collapses internally; pass raw to keep it identical
    sig = head_to_head(r)
    robustness(r)
    verdict(r, sig)
