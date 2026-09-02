"""L2 on dataset v2 — the capacity rung. Design frozen in PREREG_L1L2L7_v2.md.

The sweep is identical to legacy `run_l2.py` (28 configurations, both directions
around the L1 setting), on the same POD basis and inputs as run_l1_v2's fold
design: 64 modes/channel fitted on fold-train only, 128x128 on load, the L6-v2
fold map, 3 seeds. Train error is recorded alongside held-out error so that
underfitting is ruled out rather than assumed (defect B14).

Families run cheapest first (mlp_width, mlp_depth, rf_leaf, xgb_depth) so that a
shutdown costs the least; the order is recorded and has no effect on any number.
Every (config, fold, seed) cell is written as it completes and skipped on resume.

    python run_l2_v2.py
    python run_l2_v2.py --families mlp_width --only-folds 0
"""
from __future__ import annotations

import argparse
import gc
import time

import numpy as np

import ladder_data
from run_l2 import sweep_configs
from v2_common import (FIELD_RES, ROOT_V2, FoldPOD, evaluate_coeffs, get_path,
                       load_folds, load_or_init, per_sample_lists, set_path,
                       summarise_rows, write_atomic)

FAMILY_ORDER = ("mlp_width", "mlp_depth", "rf_leaf", "xgb_depth")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--modes", type=int, default=64)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--families", nargs="+", default=None)
    ap.add_argument("--only-folds", type=int, nargs="+", default=None)
    ap.add_argument("--field-res", type=int, default=FIELD_RES)
    ap.add_argument("--train-eval-cap", type=int, default=600)
    ap.add_argument("--out", default="results/l2_v2_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load(args.root, field_res=args.field_res)
    fold_of, n_folds, fold_seed = load_folds(d.material_ids)

    configs = sweep_configs()
    if args.families:
        configs = [c for c in configs if c[0] in args.families]
    configs.sort(key=lambda c: FAMILY_ORDER.index(c[0]) if c[0] in FAMILY_ORDER else 99)
    labels = [f"{fam}/{lab}" for fam, lab, _, _ in configs]

    header = {"root": args.root, "design_of_data": d.meta.get("design", "legacy"),
              "field_res": args.field_res, "field_shape": list(d.fields.shape[2:]),
              "modes": args.modes, "seeds": args.seeds,
              "fold_file": "results/l6_v2_folds.json", "fold_seed": fold_seed,
              "n_folds": n_folds, "families": sorted({c[0] for c in configs}),
              "configs": [{"family": fam, "label": lab, "capacity": cap} for fam, lab, cap, _ in configs]}
    res, resumed = load_or_init(args.out, header,
                                ("root", "field_res", "modes", "seeds", "fold_seed", "n_folds"))
    if resumed:
        print(f"  resuming {args.out}")

    folds = args.only_folds if args.only_folds is not None else list(range(n_folds))
    print(f"\n{len(configs)} configurations x {len(args.seeds)} seeds x {len(folds)} folds")

    # POD per fold, fitted ONCE and cached: the bases are identical for every
    # configuration, and refitting them per configuration would cost more than
    # the cheap families themselves. ~65 MB for five folds at 128x128.
    pods = {}
    for f in folds:
        pending = any(get_path(res, "cells", f"{fam}/{lab}", str(f), str(s)) is None
                      for fam, lab, _, _ in configs for s in args.seeds)
        if not pending:
            continue
        te, tr = np.where(fold_of == f)[0], np.where(fold_of != f)[0]
        print(f"\n--- POD for fold {f}: {len(tr)} train / {len(te)} held-out ---")
        pods[f] = FoldPOD(d, tr, te, args.modes, f"fold {f}")
        if get_path(res, "folds", str(f), "pod_floor") is None:
            fl, _ = pods[f].floor(d, te)
            set_path(res, fl, "folds", str(f), "pod_floor")
            set_path(res, {"n_train": int(len(tr)), "n_test": int(len(te))}, "folds", str(f), "sizes")
            write_atomic(res, args.out)
            print(f"  POD floor held-out c={fl['c']:.4e}")
    if not pods:
        print("  every requested cell is complete; nothing to run")
        return

    for (fam, lab, cap, factory), key in zip(configs, labels):
        for f in folds:
            if f not in pods:
                continue
            te, tr = pods[f].held_idx, pods[f].fit_idx
            rng = np.random.default_rng(f)
            tr_eval = np.sort(rng.choice(tr, size=min(args.train_eval_cap, len(tr)), replace=False))
            for seed in args.seeds:
                if get_path(res, "cells", key, str(f), str(seed)) is not None:
                    continue
                t1 = time.time()
                pod = pods[f]
                model = factory(seed)
                model.fit(pod.params_z[tr], pod.coeffs[tr])
                rec = {"family": fam, "label": lab, "capacity": cap}
                rows = evaluate_coeffs(model.predict(pod.params_z[tr_eval]), d.fields[tr_eval],
                                       pod.bases, d.t_final[tr_eval])
                rec["train"] = {"mean": summarise_rows(rows)}
                rows = evaluate_coeffs(model.predict(pod.params_z[te]), d.fields[te],
                                       pod.bases, d.t_final[te])
                rec["test"] = {"mean": summarise_rows(rows), **per_sample_lists(rows, d, te)}
                del model
                gc.collect()
                set_path(res, rec, "cells", key, str(f), str(seed))
                write_atomic(res, args.out)
                print(f"  {fam:<10} {lab:<7} fold {f} seed {seed}: "
                      f"train={rec['train']['mean']['c']:.4f}  held-out={rec['test']['mean']['c']:.4f}"
                      f"  [{time.time() - t1:.0f}s]", flush=True)

    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
