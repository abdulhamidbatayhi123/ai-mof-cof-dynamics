"""The coarse-solve baseline against EVERY full-design surrogate, paired by sample.

Why this exists (Digital Discovery rework, 2026-10-25): the pre-registered B-COARSE
baseline compared the coarse finite-volume solve only with the L1 and L2 perceptrons
(3.1 % / 2.4 % nRMSE). The paper's most accurate full-design surrogate is DeepONet
(L5-v2, about 1.0 %), on the same c channel, 128x128 grid and per-sample-range nRMSE.
A comparison against a weaker competitor than the best available breaks the project's
own rule 4, so this script repeats the comparison against the strongest arm. It is an
exploratory re-analysis of stored results, labelled as such; nothing is re-trained
and no solve is re-run.

Inputs (all tracked):
  results/coarse_solver_baseline.json   per-sample coarse-solve errors (one sample per
                                         material, five grid sizes) and solve costs
  results/l5_v2_results_24k.json        per-sample DeepONet errors, five folds, 3 seeds
  results/l5_v2_verdict_24k.json        the selected learning rate per basis size
  results/l1_v2_results.json            per-sample L1 perceptron errors
  results/calibration_v2.json           the calibrated level for 240 clusters
  results/cost_accounting.json          training-set size and query cost

Pairing: a surrogate's error on (material, condition) is the seed mean of its
out-of-fold prediction for that sample. Each coarse sample is matched to the same
(material, condition) in every surrogate; failed coarse solves are handled two ways:
  'fallback'  the failed sample is re-solved at production resolution: its error is
              the production solver's (0 against the reference) and its cost is one
              full solve-equivalent;
  'excluded'  the pre-registered handling (dropped), for comparison.

Break-even, two costings of the training data:
  production  every training simulation costs one production solve-equivalent (the
              paper's original costing);
  coarse      training simulations are generated at the coarse grid instead, which is
              legitimate whenever the coarse solve is more accurate than the surrogate.
Query cost is neglected (it is about 1e-4 solve-equivalents for the perceptron and is
not timed for DeepONet), so both break-evens are lower bounds.

    python coarse_vs_surrogates.py
Writes results/coarse_vs_surrogates.json.
"""
from __future__ import annotations

import json

import numpy as np

from metrics import _cluster_bootstrap

NZ = "50"
N_BOOT = 4000
SEED = 20261025


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def surrogate_by_sample(folds, getter):
    """{(mat, cond): seed-mean per-sample nRMSE} over all out-of-fold samples."""
    out = {}
    for fk, fold in folds.items():
        mats, conds, vals = getter(fold)
        for m, c, v in zip(mats, conds, vals):
            out[(int(m), int(c))] = float(v)
    return out


def deeponet_getter(p, lr):
    def g(fold):
        seeds = fold["arms"]["deeponet"][p][lr]
        first = next(iter(seeds.values()))["test"]
        vals = np.mean([np.asarray(s["test"]["per_sample_nrmse_c"], float) for s in seeds.values()], axis=0)
        return first["material_ids"], first["condition_ids"], vals
    return g


def l1_getter(arm):
    def g(fold):
        ids = fold["pod_floor_per_sample"]
        seeds = fold["arms"][arm]
        vals = np.mean([np.asarray(s["test"]["per_sample_nrmse_c"], float) for s in seeds.values()], axis=0)
        return ids["material_ids"], ids["condition_ids"], vals
    return g


def main():
    coarse = load("results/coarse_solver_baseline.json")
    l5 = load("results/l5_v2_results_24k.json")
    l5v = load("results/l5_v2_verdict_24k.json")
    l1 = load("results/l1_v2_results.json")
    alpha = load("results/calibration_v2.json")["v2_5fold"]["alpha"]
    cost = load("results/cost_accounting.json")
    n_sims = cost["frontier"][4]["n_train_sims_mean_over_folds"]

    cells = [v for v in coarse["cells"].values() if str(v["nz"]) == NZ]
    coarse_se = coarse["summary"]["per_nz"][NZ]["solve_equivalents"]

    arms = {}
    for p in ("16", "128"):
        lr = l5v["selected"][f"deeponet_p{p}"]["lr"]
        key = next(k for k in l5["folds"]["0"]["arms"]["deeponet"][p] if abs(float(k) - lr) < 1e-12)
        arms[f"deeponet_p{p}"] = surrogate_by_sample(l5["folds"], deeponet_getter(p, key))
    arms["l1_mlp"] = surrogate_by_sample(l1["folds"], l1_getter("mlp"))

    rng = np.random.default_rng(SEED)
    out = {"_what": __doc__.split("\n\n")[0], "alpha": alpha, "n_boot": N_BOOT, "coarse_nz": int(NZ),
           "coarse_solve_equivalents": coarse_se, "n_train_sims": n_sims, "arms": {}}

    for name, table in arms.items():
        for handling in ("fallback", "excluded"):
            mats, a_err, s_err = [], [], []
            n_failed = 0
            for v in cells:
                key = (int(v["mat"]), int(v["cond"]))
                if key not in table:
                    continue
                if not v["accepted"]:
                    n_failed += 1
                    if handling == "excluded":
                        continue
                    a = 0.0
                else:
                    a = float(v["c"])
                mats.append(key[0]); a_err.append(a); s_err.append(table[key])
            mats = np.asarray(mats); a_err = np.asarray(a_err); s_err = np.asarray(s_err)
            diff = s_err - a_err                       # > 0: the coarse solve is more accurate
            boots = _cluster_bootstrap(diff, mats, N_BOOT, rng)
            lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
            # expected cost per query of the coarse route, failures re-solved at full cost
            fail_frac = n_failed / max(1, len(cells))
            se_q = coarse_se if handling == "excluded" else coarse_se * (1 - fail_frac) + 1.0 * fail_frac
            out["arms"].setdefault(name, {})[handling] = {
                "n_samples": int(len(mats)), "n_materials": int(np.unique(mats).size),
                "n_coarse_failed": int(n_failed),
                "surrogate_mean_nrmse_c": float(s_err.mean()),
                "coarse_mean_nrmse_c": float(a_err.mean()),
                "accuracy_ratio": float(s_err.mean() / a_err.mean()) if a_err.mean() > 0 else None,
                "mean_diff": float(diff.mean()), "ci_low": float(lo), "ci_high": float(hi),
                "coarse_more_accurate": bool(lo > 0),
                "coarse_solve_equivalents_per_query": float(se_q),
                "break_even_queries_production_training": float(n_sims / se_q),
                "break_even_queries_coarse_training": float(n_sims * coarse_se / se_q),
            }
    with open("results/coarse_vs_surrogates.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    for name, h in out["arms"].items():
        r = h["fallback"]
        print(f"{name:14s} surrogate {r['surrogate_mean_nrmse_c']:.4f}  coarse {r['coarse_mean_nrmse_c']:.4f}  "
              f"ratio {r['accuracy_ratio']:.2f}  diff CI [{r['ci_low']:.4f}, {r['ci_high']:.4f}]  "
              f"break-even prod {r['break_even_queries_production_training']:,.0f} / coarse {r['break_even_queries_coarse_training']:,.0f}  "
              f"(n={r['n_samples']}, failed={r['n_coarse_failed']})")


if __name__ == "__main__":
    main()
