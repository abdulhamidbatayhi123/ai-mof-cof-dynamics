"""L5, scored over EVERY learning rate ever run, with a grid-boundary guard.

Why this file exists
--------------------
`analyze_l5.py` scores one results file. L5's learning-rate grid was extended
three times after the first run (`l5_fill1`, `l5_fill2`, `l5_refine`), and the
tables in `RESULTS.md` and `03_LADDER_PROTOCOL.md` were never regenerated from
the union. Two consequences were found in the 2026-08-30 audit:

  * DeepOKAN at p = 64 and 128 is materially better at lr = 2e-4 than at the
    recorded 1e-4 (0.0818 -> 0.0652 and 0.0884 -> 0.0710, both significant).
    `CONTINUE_HERE.md` section 3 explicitly instructed this update and it was
    never made.
  * DeepONet is better at lr = 3e-3 -- ABOVE the original top of the grid -- at
    every single p. The published numbers are all stale.

Protocol rule 4 requires every arm to be scored at the STRONGEST configuration
of its competitor. A table built from a subset of the runs violates it silently,
which is how defects B14, B22 and B23 happened. So this script reads all of
them, every time, and refuses to stay quiet about a boundary.

THE GRID-BOUNDARY GUARD
-----------------------
A hyper-parameter search whose optimum sits on the edge of the swept grid is not
a search -- the true optimum is outside it and the arm is under-tuned. That is
the B14/B22/B23 failure mode, and it recurred a fifth time in L5. Every selected
arm is therefore checked against the min and max of its own family's swept grid,
and a boundary selection is reported as UNBRACKETED. It is a warning, not an
error: the number is still the best measured, but it is a lower bound on the
family's achievable performance and may not be quoted as its optimum.

Usage
    python analyze_l5_merged.py
    python analyze_l5_merged.py --markdown     # emit the tables for RESULTS.md
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np

from metrics import ALPHA_CALIBRATED, ArmResult, compare

SOURCES = (
    "results/l5_results.json",
    "results/l5_fill1.json",
    "results/l5_fill2.json",
    "results/l5_refine.json",
    "results/l5_fill1b.json",     # may not exist; the chain that wrote it died
    "results/l5_okan_hi.json",    # deepokan at 3e-3 and 1e-2 (guard: 30-35%% off)
    "results/l5_onet_hi.json",    # deeponet at 1e-2
    "results/l5_onet_3e2.json",   # deeponet p=8,16 at 3e-2: 1e-2 was still the TOP edge and moving 4-6 %
)
MIN_SEEDS = 3                      # protocol section 3 rule 5. Not negotiable.
WITHDRAWN = "results/l5_singlelr_WITHDRAWN.json"


def load_arms(sources=SOURCES, verbose=True):
    """Merge every L5 results file, keyed by (family, p, lr).

    Refuses to read the withdrawn single-learning-rate file (defect B22): it
    trained both operator families at one lr, which saturated the RBF-KAN stack.
    """
    arms, floors, encodings = {}, {}, set()
    for path in sources:
        if not os.path.exists(path):
            if verbose:
                print(f"  (absent: {path})")
            continue
        if os.path.abspath(path) == os.path.abspath(WITHDRAWN):
            raise ValueError(f"{WITHDRAWN} is withdrawn (defect B22) and may not be analysed")
        d = json.load(open(path))
        encodings.add((d["nz_s"], d["nt_s"], d["budget"], d["steps"]))
        # pod_floor is {p: {"train": .., "novel_material": ..}}; we score on the
        # novel-material split throughout, so take that leg.
        floors.update({int(k): (v["novel_material"] if isinstance(v, dict) else v)
                       for k, v in d["pod_floor"].items()})
        for a in d["arms"]:
            key = (a["family"], a["p"], float(f"{a['lr']:.10g}"))
            if key in arms:
                raise ValueError(f"duplicate arm {key} in {path} — two files disagree")
            a["_src"] = os.path.basename(path)
            arms[key] = a
        if verbose:
            print(f"  {os.path.basename(path):24s} {len(d['arms']):3d} arms")

    if len(encodings) != 1:
        raise ValueError(
            f"arms were produced under different encodings/budgets: {encodings}. "
            "Merging them would violate information parity (protocol section 3)."
        )
    return arms, floors, encodings.pop()


def arm_result(a, name, split="novel_material"):
    """Pool the per-sample scores across seeds, carrying material ids for clustering."""
    v, m = [], []
    for s in sorted(a["seeds"]):
        rec = a["seeds"][s][split]
        v.append(np.asarray(rec["per_sample_nrmse_c"]))
        m.append(np.asarray(rec["material_ids"]))
    return ArmResult(name=name, values=np.concatenate(v), material_ids=np.concatenate(m))


def n_seeds(a):
    return len(a["seeds"])


def edge_is_binding(curve, best_lr, tol=0.02):
    """Is an edge selection actually a problem, or has the metric saturated there?

    A selected hyperparameter sitting on the boundary of its swept grid usually
    means the search did not bracket the optimum — that is defects B14/B22/B23 and
    retraction A20, five recurrences. But it is not ALWAYS a problem, and treating
    it as one wastes compute on cells that are already converged.

    The distinction is whether the metric is still MOVING at the edge. Measured on
    L3 (2026-08-31), the two cases look completely different:

        mlp@50k    bottom edge:  3e-5 0.0564  vs  1e-4 0.0566   -> 0.4 % apart
        cheby@50k  top edge:     3e-2 0.1063  vs  1e-2 0.1189   -> 11.9 % apart

    The MLP has saturated in learning rate and extending the grid downward cannot
    materially help; the Chebyshev-KAN is still climbing and its number is a real
    lower bound on what the family achieves. Reporting both as "unbracketed" is
    true but not useful.

    `curve` is {lr: score}; lower is better. Returns (binding, relative_change).
    """
    ok = {k: v for k, v in curve.items() if v is not None}
    if len(ok) < 2:
        return True, float("inf")
    lrs = sorted(ok)
    i = lrs.index(best_lr)
    # the neighbour on the interior side — the direction the grid DOES cover
    j = i + 1 if i == 0 else i - 1
    nb = ok[lrs[j]]
    rel = abs(nb - ok[best_lr]) / max(abs(ok[best_lr]), 1e-30)
    return bool(rel > tol), float(rel)


def select(arms, verbose=True):
    """Best lr per (family, p) at >= MIN_SEEDS, with the grid-boundary guard."""
    fams = sorted({f for f, _, _ in arms})
    ps = sorted({p for _, p, _ in arms})
    grid = {f: sorted({lr for ff, _, lr in arms if ff == f}) for f in fams}

    chosen, warnings = {}, []
    for f in fams:
        for p in ps:
            cands = [(np.mean([a["seeds"][s]["novel_material"]["c"] for s in a["seeds"]]), lr, a)
                     for (ff, pp, lr), a in arms.items()
                     if ff == f and pp == p and n_seeds(a) >= MIN_SEEDS]
            if not cands:
                continue
            mean, lr, a = min(cands, key=lambda t: t[0])
            g = grid[f]
            at_edge = (lr == min(g) or lr == max(g)) and len(g) > 1
            curve = {ll: (np.mean([aa["seeds"][s]["novel_material"]["c"]
                                   for s in aa["seeds"]])
                          if n_seeds(aa) >= MIN_SEEDS else None)
                     for (ff, pp, ll), aa in arms.items() if ff == f and pp == p}
            binding, rel = (edge_is_binding(curve, lr) if at_edge else (False, 0.0))
            chosen[(f, p)] = {"mean": float(mean), "lr": lr, "arm": a,
                              "unbracketed": bool(at_edge),
                              "edge_binding": bool(binding),
                              "edge_sensitivity": rel,
                              "grid": g, "n_lr_tried": len(g)}
            if at_edge and binding:
                side = "BOTTOM" if lr == min(g) else "TOP"
                warnings.append(
                    f"{f} p={p}: best lr {lr:.0e} is the {side} of the swept grid "
                    f"{[f'{x:.0e}' for x in g]} and the metric is STILL MOVING there "
                    f"({rel*100:.1f} % to the next point) — UNBRACKETED, extend the grid"
                )
            elif at_edge:
                warnings.append(
                    f"{f} p={p}: best lr {lr:.0e} is on the grid edge but the metric "
                    f"has SATURATED there ({rel*100:.1f} % to the next point) — "
                    f"benign, no extension needed"
                )
    return chosen, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markdown", action="store_true", help="emit tables for RESULTS.md")
    args = ap.parse_args()

    print("Merging every L5 results file:")
    arms, floors, enc = load_arms()
    nz, nt, budget, steps = enc
    print(f"\n  encoding {nz}x{nt}, budget ~{budget:,} params, {steps} steps — identical across all arms")
    print(f"  {len(arms)} distinct (family, p, lr) arms\n")

    chosen, warnings = select(arms)
    fams = sorted({f for f, _ in chosen})
    ps = sorted({p for _, p in chosen})

    # ── the table ────────────────────────────────────────────────────────────
    hdr = f"{'p':>5s} {'POD floor':>10s}"
    for f in fams:
        hdr += f" | {f:>10s} {'lr':>7s} {'x floor':>8s}"
    print(hdr)
    print("-" * len(hdr))
    for p in ps:
        row = f"{p:5d} {floors[p]:10.5f}"
        for f in fams:
            c = chosen.get((f, p))
            if c is None:
                row += f" | {'—':>10s} {'':>7s} {'':>8s}"
            else:
                flag = ("*" if c["edge_binding"] else "~") if c["unbracketed"] else " "
                row += f" | {c['mean']:10.5f}{flag} {c['lr']:7.0e} {c['mean']/floors[p]:8.1f}"
        print(row)
    print("\n  * = best lr on a grid edge AND still moving there (needs extension)")
    print("  ~ = best lr on a grid edge but saturated there (benign)")

    # ── paired comparisons vs the smallest p, per family ─────────────────────
    print(f"\nPaired vs p = {ps[0]}, cluster-robust by material, alpha = {ALPHA_CALIBRATED}")
    verdicts = {}
    for f in fams:
        if (f, ps[0]) not in chosen:
            continue
        base = arm_result(chosen[(f, ps[0])]["arm"], f"{f} p={ps[0]}")
        print(f"\n  {f}:")
        for p in ps[1:]:
            if (f, p) not in chosen:
                continue
            other = arm_result(chosen[(f, p)]["arm"], f"p={p}")
            r = compare(base, other)
            verdicts[(f, p)] = r
            tag = "NO DIFFERENCE" if not r["significant"] else \
                  ("WORSE at larger p" if r["mean_diff"] < 0 else "BETTER at larger p")
            print(f"    p={p:4d}  diff {r['mean_diff']:+.5f}  "
                  f"CI [{r['ci_low']:+.5f}, {r['ci_high']:+.5f}]   {tag}")

    # ── family comparison at each family's best configuration anywhere ───────
    print("\nFamily verdict, each family at its best configuration anywhere:")
    bests = {f: min((c for (ff, _), c in chosen.items() if ff == f), key=lambda c: c["mean"])
             for f in fams}
    for f, c in bests.items():
        p = [pp for (ff, pp), cc in chosen.items() if ff == f and cc is c][0]
        print(f"    {f:10s} {c['mean']:.5f}  (p={p}, lr={c['lr']:.0e})")
    if len(fams) == 2:
        a, b = fams
        r = compare(arm_result(bests[a]["arm"], a), arm_result(bests[b]["arm"], b))
        tag = "NO DIFFERENCE DETECTED" if not r["significant"] else "SIGNIFICANT"
        print(f"    {a} vs {b}: diff {r['mean_diff']:+.5f} "
              f"CI [{r['ci_low']:+.5f}, {r['ci_high']:+.5f}]   {tag}")
        if not r["significant"]:
            print("    -> 'no difference DETECTED'. Never 'equivalent' — see the power note below.")

    # ── flatness headline ────────────────────────────────────────────────────
    print("\nFlatness of each family across the basis-size sweep:")
    for f in fams:
        lo = chosen.get((f, ps[0])); hi = chosen.get((f, ps[-1]))
        if lo and hi:
            fl = floors[ps[0]] / floors[ps[-1]]
            print(f"    {f:10s} {lo['mean']:.4f} -> {hi['mean']:.4f} "
                  f"({lo['mean']/hi['mean']:.2f}x) while the POD floor falls {fl:.1f}x; "
                  f"at p={ps[-1]} it sits {hi['mean']/floors[ps[-1]]:.0f}x above its own bound")

    # ── the guard's verdict ──────────────────────────────────────────────────
    if warnings:
        print("\n" + "=" * 78)
        print("GRID-BOUNDARY WARNINGS — protocol rule 4 (strongest competitor configuration)")
        print("=" * 78)
        for w in warnings:
            print(f"  ! {w}")
        print("\n  These numbers are the best MEASURED, but they are LOWER BOUNDS on what the")
        print("  family achieves. They may not be quoted as the family's optimum until the")
        print("  grid is extended and the selected lr is interior.")
    else:
        print("\n  Every selected learning rate is interior to its grid. Optima are bracketed.")

    if args.markdown:
        print("\n\n" + "=" * 78 + "\nMARKDOWN FOR RESULTS.md\n" + "=" * 78 + "\n")
        print("| p | POD floor | " + " | ".join(fams) + " |")
        print("|---|---|" + "---|" * len(fams))
        for p in ps:
            cells = []
            for f in fams:
                c = chosen.get((f, p))
                cells.append("—" if c is None else
                             f"**{c['mean']:.4f}**" + ("\\*" if c["unbracketed"] else ""))
            print(f"| {p} | {floors[p]:.5f} | " + " | ".join(cells) + " |")

    out = {
        "encoding": {"nz_s": nz, "nt_s": nt, "budget": budget, "steps": steps},
        "sources": [os.path.basename(s) for s in SOURCES if os.path.exists(s)],
        "pod_floor": floors,
        "selected": {f"{f}_p{p}": {k: v for k, v in c.items() if k != "arm"}
                     for (f, p), c in chosen.items()},
        "paired_vs_smallest_p": {f"{f}_p{p}": r for (f, p), r in verdicts.items()},
        "grid_boundary_warnings": warnings,
    }
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/l5_merged.json", "w"), indent=2)
    print("\nwrote results/l5_merged.json")


if __name__ == "__main__":
    main()
