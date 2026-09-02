"""L1 on dataset v2 — the data-driven arms. Design frozen in PREREG_L1L2L7_v2.md.

Two designs, both run, both recorded:

  manifest   the dataset's own split: 192 training materials, 48 held out, plus
             the 2-condition novel-condition split (descriptive only). This is the
             legacy-shaped single-split view at the 48-cluster calibration.
  folds      5-fold cross-validation over materials using the L6-v2 fold map
             (results/l6_v2_folds.json), so L1, L2 and L6 report over the SAME
             240 held-out materials in the SAME folds.

Arms and hyperparameters are identical to legacy `run_l1.py`; the POD basis (64
modes/channel) is fitted on the fit set only, per design and per fold. Fields are
subsampled to 128x128 on load, exactly as L5 and L6-v2.

Every completed (design, fold, arm, seed) cell is written immediately; re-running
skips completed cells.

    python run_l1_v2.py --design both
    python run_l1_v2.py --design folds --only-folds 3 4
"""
from __future__ import annotations

import argparse
import gc
import os
import time

import numpy as np

import ladder_data
from run_l1 import HAS_XGB, make_arm
from v2_common import (FIELD_RES, ROOT_V2, FoldPOD, evaluate_coeffs, get_path,
                       load_folds, load_or_init, per_sample_lists, set_path,
                       summarise_rows, write_atomic)


def run_arm_on(pod, d, arm, seed, fit_idx, eval_sets):
    """Fit one arm on `fit_idx`, score on each named index set. Returns {name: rec}."""
    model = make_arm(arm, seed)
    model.fit(pod.params_z[fit_idx], pod.coeffs[fit_idx])
    out = {}
    for name, idx in eval_sets.items():
        pred = model.predict(pod.params_z[idx])
        rows = evaluate_coeffs(pred, d.fields[idx], pod.bases, d.t_final[idx])
        rec = {"mean": summarise_rows(rows)}
        if name != "train":                       # per-sample vectors for held-out sets only
            rec.update(per_sample_lists(rows, d, idx))
        out[name] = rec
    del model
    gc.collect()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT_V2)
    ap.add_argument("--design", choices=["manifest", "folds", "both"], default="both")
    ap.add_argument("--modes", type=int, default=64)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--arms", nargs="+", default=["ridge", "rf", "xgb", "mlp"])
    ap.add_argument("--only-folds", type=int, nargs="+", default=None)
    ap.add_argument("--field-res", type=int, default=FIELD_RES)
    ap.add_argument("--train-eval-cap", type=int, default=600,
                    help="train-split rows scored for the train error (cost control; "
                         "the train error is diagnostic, never a verdict)")
    ap.add_argument("--out", default="results/l1_v2_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load(args.root, field_res=args.field_res)
    fold_of, n_folds, fold_seed = load_folds(d.material_ids)
    arms = [a for a in args.arms if a != "xgb" or HAS_XGB]
    skipped = [a for a in args.arms if a not in arms]
    if skipped:
        print(f"  ARMS SKIPPED (unavailable): {skipped}")

    header = {"root": args.root, "design_of_data": d.meta.get("design", "legacy"),
              "field_res": args.field_res, "field_shape": list(d.fields.shape[2:]),
              "modes": args.modes, "seeds": args.seeds, "arms_requested": args.arms,
              "arms_skipped": skipped, "fold_file": "results/l6_v2_folds.json",
              "fold_seed": fold_seed, "n_folds": n_folds, "param_keys": list(d.param_keys)}
    res, resumed = load_or_init(args.out, header,
                                ("root", "field_res", "modes", "seeds", "fold_seed", "n_folds"))
    if resumed:
        print(f"  resuming {args.out}")

    # ── design 1: the manifest split ────────────────────────────────────────
    if args.design in ("manifest", "both"):
        tr, nc, nm = d.idx("train"), d.idx("novel_condition"), d.idx("novel_material")
        print(f"\n=== MANIFEST SPLIT: train {len(tr)} / novel_condition {len(nc)} / "
              f"novel_material {len(nm)} ({len(np.unique(d.material_ids[nm]))} materials) ===")
        todo = [(a, s) for a in arms for s in args.seeds
                if get_path(res, "manifest", "arms", a, str(s)) is None]
        if not todo:
            print("  manifest design complete, skipping")
        else:
            pod = FoldPOD(d, tr, np.concatenate([nc, nm]), args.modes, "manifest")
            if get_path(res, "manifest", "pod_floor") is None:
                floors = {}
                for split, idx in (("train", tr), ("novel_condition", nc), ("novel_material", nm)):
                    floors[split], _ = pod.floor(d, idx)
                    print(f"  POD floor {split:<16} c={floors[split]['c']:.4e} "
                          f"q={floors[split]['q']:.4e} T={floors[split]['T']:.4e} "
                          f"exit={floors[split]['exit_nrmse']:.4e}")
                set_path(res, floors, "manifest", "pod_floor")
                set_path(res, pod.spectrum_json(), "manifest", "spectrum")
                set_path(res, d.summary(), "manifest", "splits")
                write_atomic(res, args.out)
            rng = np.random.default_rng(0)
            tr_eval = np.sort(rng.choice(tr, size=min(args.train_eval_cap, len(tr)), replace=False))
            for arm, seed in todo:
                t1 = time.time()
                rec = run_arm_on(pod, d, arm, seed, tr,
                                 {"train": tr_eval, "novel_condition": nc, "novel_material": nm})
                set_path(res, rec, "manifest", "arms", arm, str(seed))
                write_atomic(res, args.out)
                m = rec["novel_material"]["mean"]
                print(f"  {arm:<6} seed {seed}: train c={rec['train']['mean']['c']:.4f} | "
                      f"novel-material c={m['c']:.4f} q={m['q']:.4f} T={m['T']:.4f} "
                      f"exit={m['exit_nrmse']:.4f} dt50={m['dt_bt50'] / 3600:.2f}h  "
                      f"[{time.time() - t1:.0f}s]", flush=True)
            del pod
            gc.collect()

    # ── design 2: 5-fold CV over materials, the L6-v2 folds ─────────────────
    if args.design in ("folds", "both"):
        folds = args.only_folds if args.only_folds is not None else list(range(n_folds))
        for f in folds:
            te = np.where(fold_of == f)[0]
            tr = np.where(fold_of != f)[0]
            todo = [(a, s) for a in arms for s in args.seeds
                    if get_path(res, "folds", str(f), "arms", a, str(s)) is None]
            print(f"\n=== FOLD {f}: train {len(tr)} conds / "
                  f"{len(np.unique(d.material_ids[tr]))} materials | held-out {len(te)} conds / "
                  f"{len(np.unique(d.material_ids[te]))} materials ===")
            if not todo:
                print("  fold complete, skipping")
                continue
            pod = FoldPOD(d, tr, te, args.modes, f"fold {f}")
            if get_path(res, "folds", str(f), "pod_floor") is None:
                fl_te, rows_te = pod.floor(d, te)
                fl_tr, _ = pod.floor(d, tr[:args.train_eval_cap])
                set_path(res, {"train": fl_tr, "test": fl_te}, "folds", str(f), "pod_floor")
                set_path(res, {"per_sample_nrmse_c": [float(r["c"]) for r in rows_te],
                               "per_sample_exit_nrmse": [float(r["exit_nrmse"]) for r in rows_te],
                               "material_ids": d.material_ids[te].tolist(),
                               "condition_ids": d.condition_ids[te].tolist()},
                         "folds", str(f), "pod_floor_per_sample")
                set_path(res, pod.spectrum_json(), "folds", str(f), "spectrum")
                set_path(res, {"n_train": int(len(tr)), "n_test": int(len(te)),
                               "test_materials": sorted(map(int, np.unique(d.material_ids[te])))},
                         "folds", str(f), "sizes")
                write_atomic(res, args.out)
                print(f"  POD floor test c={fl_te['c']:.4e} exit={fl_te['exit_nrmse']:.4e}")
            rng = np.random.default_rng(f)
            tr_eval = np.sort(rng.choice(tr, size=min(args.train_eval_cap, len(tr)), replace=False))
            for arm, seed in todo:
                t1 = time.time()
                rec = run_arm_on(pod, d, arm, seed, tr, {"train": tr_eval, "test": te})
                set_path(res, rec, "folds", str(f), "arms", arm, str(seed))
                write_atomic(res, args.out)
                m = rec["test"]["mean"]
                print(f"  {arm:<6} seed {seed}: train c={rec['train']['mean']['c']:.4f} | "
                      f"held-out c={m['c']:.4f} q={m['q']:.4f} T={m['T']:.4f} "
                      f"exit={m['exit_nrmse']:.4f} dt50={m['dt_bt50'] / 3600:.2f}h  "
                      f"[{time.time() - t1:.0f}s]", flush=True)
            del pod
            gc.collect()

    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
