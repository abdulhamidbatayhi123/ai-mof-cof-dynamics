"""L2 — the capacity rung.

Hypothesis under test: *"the model is too small."*

L1 showed every data-driven arm sitting ~33x above the POD floor, and the L1
audit showed that gap is flat in POD rank (1.01x from 8 to 128 modes) and stable
across holdout sets. So the failure is in the parameter->coefficient map. The
obvious next explanation is that the map is under-parameterised.

Design
------
Capacity is swept in BOTH directions around the L1 setting, not just upward.
Sweeping only upward cannot distinguish "capacity helps" from "we happened to
start below the optimum", and cannot detect the U-shape that indicates the
optimum has already been passed.

The signature to look for, on the NOVEL-MATERIAL split:

    monotonically falling  -> capacity WAS the constraint; L2 is not eliminated
    flat                   -> capacity is irrelevant; eliminate and move to L3
    U-shaped               -> optimum already passed at L1 settings; eliminate

Train error is reported alongside test error throughout, so underfitting can be
ruled out rather than assumed — L1's MLP arm looked terrible purely because it
underfitted, and that cost a retraction (B14).

The POD basis, splits, inputs and seeds are identical to L1. Only capacity moves.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import time

import numpy as np
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

import ladder_data
from run_l1 import CHANNELS, evaluate, fit_pod, project

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


def sweep_configs():
    """(family, label, capacity_scalar, factory) — capacity_scalar is the x-axis."""
    out = []

    # MLP: width at fixed depth, then depth at fixed width
    for w in (16, 32, 64, 128, 256, 512, 1024):
        out.append(("mlp_width", f"w{w}", w, lambda s, w=w: TransformedTargetRegressor(
            regressor=MLPRegressor(hidden_layer_sizes=(w, w, w), max_iter=3000,
                                   early_stopping=True, n_iter_no_change=30,
                                   random_state=s, learning_rate_init=1e-3),
            transformer=StandardScaler())))
    for dpt in (1, 2, 3, 4, 5, 6, 8, 10):
        out.append(("mlp_depth", f"d{dpt}", dpt, lambda s, dpt=dpt: TransformedTargetRegressor(
            regressor=MLPRegressor(hidden_layer_sizes=(256,) * dpt, max_iter=3000,
                                   early_stopping=True, n_iter_no_change=30,
                                   random_state=s, learning_rate_init=1e-3),
            transformer=StandardScaler())))

    # XGB: tree depth is the dominant capacity knob
    if HAS_XGB:
        for md in (2, 3, 4, 5, 6, 8, 10):
            out.append(("xgb_depth", f"md{md}", md, lambda s, md=md: XGBRegressor(
                n_estimators=400, max_depth=md, learning_rate=0.06,
                subsample=0.85, colsample_bytree=0.85, random_state=s,
                n_jobs=-1, verbosity=0, multi_strategy="multi_output_tree",
                tree_method="hist")))

    # RF: leaf size is the capacity knob (smaller leaf = more capacity)
    for leaf in (1, 2, 4, 8, 16, 32):
        out.append(("rf_leaf", f"leaf{leaf}", 1.0 / leaf, lambda s, leaf=leaf:
                    RandomForestRegressor(n_estimators=300, min_samples_leaf=leaf,
                                          random_state=s, n_jobs=-1)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modes", type=int, default=64)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--families", nargs="+", default=None)
    ap.add_argument("--out", default="results/l2_results.json")
    args = ap.parse_args()

    t0 = time.time()
    d = ladder_data.load()
    shape = d.fields.shape[2:]
    tr = d.idx("train")

    print(f"\nPOD ({args.modes} modes/channel, train split only) — identical to L1:")
    bases, spectra = fit_pod(d.fields, tr, args.modes)
    coeffs = project(d.fields, bases)
    gc.collect()

    floor = {}
    for split in ladder_data.SPLITS:
        idx = d.idx(split)
        rows = evaluate(coeffs[idx], d.fields[idx], bases, shape, d.t_final[idx])
        floor[split] = float(np.nanmean([r["c"] for r in rows]))
    print(f"POD floor (novel-material): {floor['novel_material']:.4e}\n")

    configs = sweep_configs()
    if args.families:
        configs = [c for c in configs if c[0] in args.families]
    print(f"{len(configs)} configurations x {len(args.seeds)} seeds\n")

    results = {"modes": args.modes, "seeds": args.seeds, "pod_floor": floor,
               "splits": d.summary(), "sweep": []}

    for fam, label, cap, factory in configs:
        rec = {"family": fam, "label": label, "capacity": cap, "seeds": {}}
        for seed in args.seeds:
            t1 = time.time()
            model = factory(seed)
            model.fit(d.params_z[tr], coeffs[tr])
            per = {}
            for split in ("train", "novel_material"):
                idx = d.idx(split)
                pred = model.predict(d.params_z[idx])
                rows = evaluate(pred, d.fields[idx], bases, shape, d.t_final[idx])
                per[split] = {
                    "c": float(np.nanmean([r["c"] for r in rows])),
                    "dt_bt50": float(np.nanmean([r["dt_bt50"] for r in rows])),
                    "per_sample_nrmse_c": [float(r["c"]) for r in rows],
                    "material_ids": d.material_ids[idx].tolist(),
                }
            rec["seeds"][str(seed)] = per
            del model
            gc.collect()
            print(f"  {fam:<10} {label:<7} seed {seed}: "
                  f"train={per['train']['c']:.4f}  novel={per['novel_material']['c']:.4f}"
                  f"  [{time.time() - t1:.0f}s]", flush=True)
        results["sweep"].append(rec)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w") as f:      # checkpoint after every config
            json.dump(results, f, indent=2)

    print(f"\nwrote {args.out}  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
