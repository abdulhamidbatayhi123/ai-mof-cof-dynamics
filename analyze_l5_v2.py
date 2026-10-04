"""L5-v2 verdict: is operator error flat in the basis size p? 5-fold, 240 materials.

Port of `analyze_l5_merged.py` per audit_2026-09-24/audit_risk.md #6-#10:

  #8  per-sample scores are AVERAGED over seeds (identical sample order asserted),
      then pooled across folds so each held-out sample appears exactly once.
  #9  cells are keyed (family, p, lr, fold); several results files may be merged but
      only under one parity tuple (root, design_of_data, field_res, nz_s, nt_s,
      budget, steps); a duplicate (family, p, lr, fold, seed) cell aborts.
  #6  alpha from v2_common.alpha_for("folds"), n_boot 4000, both written out.
  #7  every non-significant comparison carries its MDE (mde_report); --no-mde marks
      the verdict PROVISIONAL.
  #10 the grid-boundary guard (analyze_l5_merged.edge_is_binding) is kept unchanged.

The step-sensitivity arm (#13, run_l5_v2.py --arm steps) is reported if its file
exists: one fold, so it is descriptive plus a paired test at the manifest-sized
(48-cluster) alpha, and it decides whether the budget is adequate.

    python analyze_l5_v2.py [--res results/l5_v2_results.json ...] [--no-mde]
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

from analyze_l5_merged import edge_is_binding
from mde import mde_report
from metrics import ArmResult, compare, format_comparison
from v2_common import alpha_for

RES = ["results/l5_v2_results.json"]
# PREREG_L5_v2 amendment A1 split the step arm into one file per p. The analyser
# kept reading the old single name, found nothing, and reported the pre-registered
# re-budget gate as "NOT RUN" on 2026-10-04 while both files sat on disk. It now reads
# every declared file and REFUSES if only some exist.
STEPS_RES = ["results/l5_v2_steps_p8.json", "results/l5_v2_steps_p128.json"]
OUT = "results/l5_v2_verdict.json"
MDE_EFFECTS = (0.0, 0.02, 0.05, 0.10, 0.20)
MIN_SEEDS = 3                        # protocol section 3 rule 5
STEP_MATERIAL_CHANGE = 0.05          # 24000 vs 8000 steps moving p=128 by >5 % = re-budget
PARITY = ("root", "design_of_data", "field_res", "nz_s", "nt_s", "budget", "steps")


def seed_avg(recs):
    """Mean per-sample vector over seeds; asserts identical (material, condition) order."""
    ids = [tuple(zip(r["material_ids"], r["condition_ids"])) for r in recs]
    if any(i != ids[0] for i in ids[1:]):
        raise AssertionError("seeds were scored on different samples or in a different order")
    return (np.mean([np.asarray(r["per_sample_nrmse_c"], float) for r in recs], axis=0),
            np.asarray(recs[0]["material_ids"]), np.asarray(recs[0]["condition_ids"]))


def load_cells(paths, verbose=True):
    """Merge runner files into {(family, p, lr, fold): {seed: test-record}} under one parity tuple."""
    cells, floors, parity, meta = {}, {}, set(), None
    for path in paths:
        if not os.path.exists(path):
            if verbose:
                print(f"  (absent: {path})")
            continue
        r = json.load(open(path))
        if r.get("design") != "folds" or r.get("arm") != "sweep":
            raise ValueError(f"{path}: design={r.get('design')} arm={r.get('arm')} — "
                             f"only the folds-design sweep enters the verdict")
        parity.add(tuple(json.dumps(r.get(k)) for k in PARITY))
        meta = meta or r
        for f, F in r.get("folds", {}).items():
            for p, fl in F.get("pod_floor_per_sample", {}).items():
                floors[(int(p), int(f))] = fl
            for fam, byp in F.get("arms", {}).items():
                for p, bylr in byp.items():
                    for lr, byseed in bylr.items():
                        key = (fam, int(p), float(lr), int(f))
                        slot = cells.setdefault(key, {})
                        for s, rec in byseed.items():
                            if s in slot:
                                raise ValueError(f"duplicate cell {key} seed {s} in {path}")
                            slot[s] = rec
    if len(parity) > 1:
        raise ValueError(f"results files differ in {PARITY}: {parity} — merging would break parity")
    if meta is None:
        raise SystemExit(f"none of {paths} exists — run run_l5_v2.py first")
    return cells, floors, meta


def pooled(cells, fam, p, lr, folds, min_seeds):
    """Seed-averaged held-out vectors, concatenated over folds (each sample once)."""
    v, m, c, train = [], [], [], []
    for f in folds:
        seeds = cells.get((fam, p, lr, f), {})
        if len(seeds) < min_seeds:
            return None
        recs = [seeds[s] for s in sorted(seeds)]
        vv, mm, cc = seed_avg([x["test"] for x in recs])
        v.append(vv); m.append(mm); c.append(cc)
        train += [x["train"]["c"] for x in recs]
    return np.concatenate(v), np.concatenate(m), np.concatenate(c), float(np.mean(train))


def same_samples(a, b):
    if not (np.array_equal(a[1], b[1]) and np.array_equal(a[2], b[2])):
        raise AssertionError("paired comparison on different sample sets / orders")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--res", nargs="+", default=RES)
    ap.add_argument("--steps-res", nargs="*", default=STEPS_RES)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--mde-trials", type=int, default=200)
    ap.add_argument("--no-mde", action="store_true")
    ap.add_argument("--min-seeds", type=int, default=MIN_SEEDS,
                    help="SMOKE ONLY below 3; a verdict below 3 seeds is marked provisional")
    args = ap.parse_args(argv)

    cells, floors, meta = load_cells(args.res)
    alpha, ncl = alpha_for("folds")                                           # #6
    n_folds = int(meta["n_folds"])
    all_folds = sorted({k[3] for k in cells} | {k[1] for k in floors})
    fams = sorted({k[0] for k in cells})
    ps = sorted({k[1] for k in cells})
    grid = {f: sorted({k[2] for k in cells if k[0] == f}) for f in fams}

    # folds usable for the verdict: complete for every (family, p, lr) present
    folds = [f for f in range(n_folds)
             if all(len(cells.get((fa, p, lr, f), {})) >= args.min_seeds
                    for fa in fams for p in ps for lr in grid[fa])
             and all((p, f) in floors for p in ps)]
    complete = len(folds) == n_folds and args.min_seeds >= MIN_SEEDS
    provisional = (not complete) or args.no_mde
    tag = "PROVISIONAL — " if provisional else ""
    print(f"L5-v2 — {meta['nz_s']}x{meta['nt_s']} encoding, budget ~{meta['budget']:,}, "
          f"steps {meta['steps']}, seeds {meta['seeds']}, alpha {alpha} ({ncl} clusters), n_boot 4000")
    print(f"  folds usable: {folds} of {n_folds} (present: {all_folds})"
          + ("" if complete else "   ⚠ INCOMPLETE — nothing below may be reported"))

    out = {"source": args.res, "parity": {k: meta.get(k) for k in PARITY},
           "alpha": alpha, "n_clusters_calibrated": ncl, "n_boot": 4000,
           "folds_used": folds, "complete": complete, "min_seeds": args.min_seeds,
           "mde_computed": not args.no_mde, "provisional": provisional}

    def dump():
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        json.dump(out, open(args.out, "w"), indent=2)

    if not folds:
        print("  no fold is complete — nothing to analyse")
        dump(); return out

    # ── floors, pooled ────────────────────────────────────────────────────────
    floor = {}
    for p in ps:
        floor[p] = float(np.concatenate([floors[(p, f)]["per_sample_nrmse_c"] for f in folds]).mean())

    # ── lr selection per (family, p) with the grid-boundary guard (#10) ─────
    chosen, warnings, scores = {}, [], {}
    for fam in fams:
        g = grid[fam]
        for p in ps:
            curve = {}
            for lr in g:
                pl = pooled(cells, fam, p, lr, folds, args.min_seeds)
                curve[lr] = None if pl is None else float(pl[0].mean())
                if pl is not None:
                    scores[(fam, p, lr)] = pl
            ok = {k: v for k, v in curve.items() if v is not None}
            if not ok:
                continue
            lr = min(ok, key=ok.get)
            at_edge = len(g) > 1 and lr in (min(g), max(g))
            binding, rel = edge_is_binding(curve, lr) if at_edge else (False, 0.0)
            pl = scores[(fam, p, lr)]
            chosen[(fam, p)] = {"mean": ok[lr], "lr": lr, "train_c": pl[3], "curve": curve,
                                "x_floor": ok[lr] / floor[p], "unbracketed": bool(at_edge),
                                "edge_binding": bool(binding), "edge_sensitivity": rel, "grid": g,
                                "per_fold": [float(pooled(cells, fam, p, lr, [f], args.min_seeds)[0].mean())
                                             for f in folds]}
            if at_edge:
                side = "BOTTOM" if lr == min(g) else "TOP"
                warnings.append(f"{fam} p={p}: best lr {lr:.0e} is the {side} of {[f'{x:.0e}' for x in g]} — "
                                + (f"STILL MOVING ({rel * 100:.1f} %) — UNBRACKETED, extend the grid"
                                   if binding else f"saturated ({rel * 100:.1f} %) — benign"))

    hdr = f"  {'p':>5} {'POD floor':>10}" + "".join(f" | {f:>10} {'lr':>7} {'x floor':>8}" for f in fams)
    print("\n" + hdr); print("  " + "-" * (len(hdr) - 2))
    for p in ps:
        row = f"  {p:5d} {floor[p]:10.5f}"
        for fam in fams:
            c = chosen.get((fam, p))
            row += (f" | {'—':>10} {'':>7} {'':>8}" if c is None else
                    f" | {c['mean']:10.5f}{('*' if c['edge_binding'] else '~') if c['unbracketed'] else ' '}"
                    f"{c['lr']:7.0e} {c['x_floor']:8.1f}")
        print(row)

    # ── paired vs the smallest p, per family, with MDE for every null (#7) ──
    comps, mdes = {}, {}
    print(f"\n{tag}paired vs smallest p, cluster-robust by material, alpha {alpha}")
    for fam in fams:
        if (fam, ps[0]) not in chosen:
            continue
        b = scores[(fam, ps[0], chosen[(fam, ps[0])]["lr"])]
        for p in ps[1:]:
            if (fam, p) not in chosen:
                continue
            o = scores[(fam, p, chosen[(fam, p)]["lr"])]
            same_samples(b, o)
            r = compare(ArmResult(f"{fam} p={ps[0]}", b[1], b[0]), ArmResult(f"{fam} p={p}", o[1], o[0]),
                        alpha=alpha, n_boot=4000)
            comps[f"{fam}_p{p}"] = r
            print("    " + format_comparison(r))
            if not r["significant"] and not args.no_mde:
                mdes[f"{fam}_p{p}"] = mde_report(o[0] - b[0], b[1], base=float(b[0].mean()), alpha=alpha,
                                                 effects=MDE_EFFECTS, trials=args.mde_trials,
                                                 label=f"L5-v2 {fam} p={p} vs p={ps[0]}")

    # ── family comparison, each at its best configuration ─────────────────
    fam_cmp = None
    bests = {fam: min(((p, c) for (ff, p), c in chosen.items() if ff == fam), key=lambda t: t[1]["mean"])
             for fam in fams if any(ff == fam for ff, _ in chosen)}
    if len(bests) == 2:
        (fa, (pa, ca)), (fb, (pb, cb)) = sorted(bests.items())
        A, B = scores[(fa, pa, ca["lr"])], scores[(fb, pb, cb["lr"])]
        same_samples(A, B)
        fam_cmp = compare(ArmResult(fa, A[1], A[0]), ArmResult(fb, B[1], B[0]), alpha=alpha, n_boot=4000)
        print("\n  family at best config: " + format_comparison(fam_cmp))
        if not fam_cmp["significant"] and not args.no_mde:
            mdes["family"] = mde_report(B[0] - A[0], A[1], base=float(A[0].mean()), alpha=alpha,
                                        effects=MDE_EFFECTS, trials=args.mde_trials,
                                        label=f"L5-v2 {fa} vs {fb} at best")

    if warnings:
        print("\n  GRID-BOUNDARY WARNINGS:")
        for w in warnings:
            print(f"   ! {w}")
    unbracketed = [w for w in warnings if "UNBRACKETED" in w]

    out.update({
        "pod_floor_pooled": {str(p): floor[p] for p in ps},
        "selected": {f"{f}_p{p}": c for (f, p), c in chosen.items()},
        "paired_vs_smallest_p": comps,
        "family_at_best": fam_cmp,
        "mde": mdes if not args.no_mde else "PENDING",
        "grid_boundary_warnings": warnings,
        "anchor_unbracketed": bool(unbracketed),
    })

    # ── step-sensitivity arm (#13) ─────────────────────────────────────────
    present = [p for p in (args.steps_res or []) if os.path.exists(p)]
    if present and len(present) != len(args.steps_res):
        raise SystemExit(f"step arm PARTIAL: {sorted(set(args.steps_res) - set(present))} missing; "
                         f"the re-budget gate needs every declared file")
    if present:
        a48, n48 = alpha_for("manifest")
        sens = {}
        for path in present:
          S = json.load(open(path))
          if tuple(json.dumps(S.get(k)) for k in PARITY[:-1]) != tuple(json.dumps(meta.get(k)) for k in PARITY[:-1]):
            raise ValueError(f"{path} differs from the sweep in {PARITY[:-1]}")
          for f, F in S.get("folds", {}).items():
            for fam, byp in F["arms"].items():
                for p, bylr in byp.items():
                    for lr, bysteps in bylr.items():
                        st = sorted(bysteps, key=int)
                        vecs = {s: seed_avg([bysteps[s][k]["test"] for k in sorted(bysteps[s])])
                                for s in st if len(bysteps[s]) >= args.min_seeds}
                        if len(vecs) < 2:
                            continue
                        lo, hi = vecs[st[0]], vecs[st[-1]]
                        same_samples(lo, hi)
                        r = compare(ArmResult(f"{st[0]} steps", lo[1], lo[0]),
                                    ArmResult(f"{st[-1]} steps", hi[1], hi[0]), alpha=a48, n_boot=4000)
                        rel = float((lo[0].mean() - hi[0].mean()) / lo[0].mean())
                        sens[f"{fam}_p{p}_lr{lr}_fold{f}"] = {
                            "means": {s: float(v[0].mean()) for s, v in vecs.items()},
                            "rel_improvement_long": rel, "comparison": r,
                            "material": bool(r["significant"] and abs(rel) > STEP_MATERIAL_CHANGE)}
                        print(f"  step arm {fam} p={p} lr {lr} fold {f}: "
                              f"{' -> '.join(f'{vecs[s][0].mean():.4f}' for s in vecs)} ({rel * 100:+.1f} %)"
                              f"  {'MATERIAL — RE-BUDGET THE SWEEP' if sens[f'{fam}_p{p}_lr{lr}_fold{f}']['material'] else ''}")
        out["step_sensitivity"] = {"alpha": a48, "n_clusters_calibrated": n48, "threshold": STEP_MATERIAL_CHANGE,
                                   "cells": sens, "rebudget_required": any(v["material"] for v in sens.values())}
    else:
        out["step_sensitivity"] = "NOT RUN — flat-in-p rests on an unmeasured budget (audit #13)"

    dump()
    print(f"\nwrote {args.out}")
    return out


if __name__ == "__main__":
    main()
