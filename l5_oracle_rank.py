"""L5: what a method's error is WORTH in modes -- the oracle-rank table, owned by a script.

RESULTS.md carried a table "equivalent oracle rank: POD+regressor ~2 modes, DeepOKAN
~3, DeepONet ~4", and the manuscript builds a bolded sentence on it ("Giving
DeepONet 128 basis functions buys it the accuracy of four") -- but no script
produced that table, and its DeepONet error (0.0281) is not the value the paper now
quotes (0.0265). An unowned number is indistinguishable from a wrong one (rule 10).
Same for "median R^2 below zero beyond about mode 24" and "modes two to five
partially": computed nowhere that a results file records.

This script owns all three, on EXACTLY the data, subsample and split of
l5_bottleneck.py (it imports its loader and metric):

  * ORACLE CURVE: held-out-material error when the reconstruction is handed the TRUE
    coefficients of its first k POD modes, k = 1..K. Exact SVD, so the k-mode bases
    are nested (a randomized PCA refitted per k would not be).
  * EQUIVALENT ORACLE RANK of each method: the smallest k whose oracle error is at or
    below the method's error, plus the log-linear interpolated fractional k, so the
    "about four" is a number and not a rounding.
  * PER-MODE R^2 BANDS at p = 128 from results/l5_bottleneck.json: the modes the
    coefficient map predicts well (R^2 > 0.5), partially (0.2-0.5), and the smallest
    mode index beyond which the MEDIAN R^2 of all remaining modes is below zero.

    python l5_oracle_rank.py     # writes results/l5_oracle_rank.json
"""
from __future__ import annotations

import json
import math
import time

import numpy as np

from l5_bottleneck import load_c_light, nrmse_per_sample

K_MAX = 32


def main():
    t0 = time.time()
    X, _, _, split = load_c_light()
    tr = np.where(split == "train")[0]
    nm = np.where(split == "novel_material")[0]

    mu = X[tr].mean(0)
    # economy SVD of the centred training snapshots: rows of Vt are the POD modes
    _, _, Vt = np.linalg.svd(X[tr] - mu, full_matrices=False)
    A = (X - mu) @ Vt[:K_MAX].T                                    # true coefficients
    oracle = []
    for k in range(1, K_MAX + 1):
        rec = mu + A[:, :k] @ Vt[:k]
        oracle.append(float(nrmse_per_sample(rec, X)[nm].mean()))

    # the methods, read from the files that own them -- never retyped
    bott = json.load(open("results/l5_bottleneck.json"))
    fno = json.load(open("results/l5_fno_verdict.json"))
    merged = json.load(open("results/l5_merged.json"))
    okan_best = min(v["mean"] for k, v in merged["selected"].items() if k.startswith("deepokan"))
    methods = {
        "pod_plus_regressor_best": min(r["coef_pred_novel"] for r in bott["rows"]),
        "deepokan_best": okan_best,
        "deeponet_best": fno["deeponet_best"],
        "fno_best": fno["fno_best"]["mean"] if isinstance(fno.get("fno_best"), dict) else fno.get("fno_best"),
    }

    def rank(err):
        ks = [k for k, e in enumerate(oracle, 1) if e <= err]
        if not ks:
            return None, None
        k = ks[0]
        if k == 1:
            return 1, 1.0
        # log-linear interpolation between k-1 and k
        e0, e1 = math.log(oracle[k - 2]), math.log(oracle[k - 1])
        frac = (math.log(err) - e0) / (e1 - e0)
        return k, (k - 1) + frac

    ranks = {}
    for name, err in methods.items():
        if err is None:
            continue
        k, kf = rank(float(err))
        ranks[name] = {"error": float(err), "oracle_rank": k, "oracle_rank_interp": kf}

    row128 = next(r for r in bott["rows"] if r["p"] == 128)
    r2 = row128["mode_r2_novel"]
    well = [i + 1 for i, v in enumerate(r2) if v > 0.5]
    partial = [i + 1 for i, v in enumerate(r2) if 0.2 < v <= 0.5]
    # "beyond about mode 24 the median R^2 is below zero" (RESULTS.md, manuscript) is
    # true but chose 24 arbitrarily: the median of the remaining modes is below zero
    # from mode 1 onward, because most of the 128 are unpredictable. The honest cut is
    # after the last predictable band -- the last mode with R^2 > 0.2 among the
    # leading run -- and the statistic is the median of everything after it.
    lead = 0
    while lead < len(r2) and r2[lead] > 0.2:
        lead += 1
    tail = r2[lead:]
    crossover = next((k for k in range(1, len(r2) + 1) if np.median(r2[k - 1:]) < 0), None)
    out = {
        "_source": "l5_bottleneck.py loader/split/metric; exact SVD; methods from "
                   "l5_bottleneck.json, l5_merged.json, l5_fno_verdict.json",
        "oracle_curve_novel": oracle,
        "ranks": ranks,
        "mode_r2_p128": {
            "n_modes": len(r2),
            "well_r2_gt_0.5": well,
            "partial_r2_0.2_to_0.5": partial,
            "median_below_zero_from_mode": crossover,
            "median_r2_from_crossover": float(np.median(r2[crossover - 1:])) if crossover else None,
            "leading_predictable_run": lead,
            "n_tail_modes": len(tail),
            "median_r2_tail": float(np.median(tail)),
            "frac_tail_below_zero": float(np.mean(np.array(tail) < 0)),
        },
    }
    json.dump(out, open("results/l5_oracle_rank.json", "w"), indent=2)
    for name, r in ranks.items():
        print(f"{name:<26} err {r['error']:.4f}  oracle rank {r['oracle_rank']}  "
              f"(interp {r['oracle_rank_interp']:.2f})" if r["oracle_rank"] else f"{name}: beyond K_MAX")
    print(f"R^2>0.5 modes {well}; partial {partial}; median<0 from mode {crossover} "
          f"(median {out['mode_r2_p128']['median_r2_from_crossover']:.3f})")
    print(f"oracle k=1..8: {[round(e, 4) for e in oracle[:8]]}   [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
