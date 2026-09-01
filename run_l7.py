"""L7 — the classical control. Zero training, closed form, microseconds.

Hypothesis under test: *"deep learning is needed at all."*

Nothing here is fitted, so nothing can overfit, and the numbers on held-out
materials are a genuine zero-parameter transfer reference. Any learned arm that
does not beat this on novel materials has not earned its parameters.

Note on scope: the classical forms predict the EXIT breakthrough curve, not the
full (z,t) field. They are therefore scored on the exit curve, and the learned
arms are re-scored on the same quantity for a like-for-like comparison. Comparing
a curve-only model against a field metric would flatter it.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

import ladder_data
from classical import MODELS
from fetch_real_mof_data import rh_to_conc
from ladder_data import PARAM_KEYS
from metrics import breakthrough_times
from run_l4 import physics_from_params


def exit_curve_metrics(pred, truth, t_norm, t_final):
    rng = truth.max() - truth.min()
    m = {"nrmse": float(np.sqrt(np.mean((pred - truth) ** 2)) / (rng if rng > 0 else 1.0))}
    bp, bt = breakthrough_times(pred, t_norm), breakthrough_times(truth, t_norm)
    for lev in (0.05, 0.50, 0.95):
        a, b = bp[lev], bt[lev]
        m[f"dt_bt{int(lev * 100):02d}"] = (abs(a - b) * t_final
                                           if np.isfinite(a) and np.isfinite(b) else np.nan)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/l7_results.json")
    args = ap.parse_args()

    d = ladder_data.load()
    nt = d.fields.shape[3]
    t_norm = np.linspace(0.0, 1.0, nt)

    res = {"splits": d.summary(), "models": {}}
    print()
    for name, fn in MODELS.items():
        per_split = {}
        for split in ladder_data.SPLITS:
            idx = d.idx(split)
            rows, wall = [], 0.0
            for gi in idx:
                p = physics_from_params(d.params[gi], d.param_keys)
                c_in = rh_to_conc(d.params[gi][d.pidx("rh_feed")], p.T_in)
                t = t_norm * d.t_final[gi]
                t0 = time.perf_counter()
                pred = fn(p, c_in, p.T_in, t)
                wall += time.perf_counter() - t0
                rows.append(exit_curve_metrics(pred, d.fields[gi, 0, -1, :], t_norm, d.t_final[gi]))
            per_split[split] = {
                "nrmse": float(np.nanmean([r["nrmse"] for r in rows])),
                "dt_bt50": float(np.nanmean([r["dt_bt50"] for r in rows])),
                "per_sample_nrmse": [float(r["nrmse"]) for r in rows],
                "material_ids": d.material_ids[idx].tolist(),
                "ms_per_curve": 1e3 * wall / len(idx),
            }
        res["models"][name] = per_split
        nm = per_split["novel_material"]
        print(f"  {name:<20} novel-material nRMSE={nm['nrmse']:.4f}  "
              f"dt50={nm['dt_bt50'] / 3600:.2f}h  {nm['ms_per_curve']:.3f} ms/curve")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(res, open(args.out, "w"), indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
