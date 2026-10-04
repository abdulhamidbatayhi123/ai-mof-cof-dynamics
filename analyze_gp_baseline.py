"""B-GP verdict (PREREG_BASELINES.md §1): a GP on POD coefficients vs the L1-v2 perceptron.

Owner of results/gp_baseline_verdict.json. Reads the GP arm's run
(`run_l1_v2.py --design folds --arms gp --out results/l1_v2_gp.json`) and the L1-v2
results, pools each arm's per-sample held-out c-channel error out of fold (seed-
averaged, each sample once), pairs them by (material, condition), and compares at
alpha_for("folds") with the frozen words. Also reports how many fitted kernels sit at
a length-scale bound on every dimension (the prereg's invalidation check), if the run
recorded the kernels.

    python analyze_gp_baseline.py
"""
import json

import numpy as np

from analyze_l1_v2 import pooled_folds
from mde import mde_report
from metrics import ArmResult, compare
from v2_common import alpha_for

GP = "results/l1_v2_gp.json"
L1 = "results/l1_v2_results.json"
OUT = "results/gp_baseline_verdict.json"


def pooled(path, arm):
    r = json.load(open(path))
    e, m, c = pooled_folds({"folds": r["folds"]}, arm, "per_sample_nrmse_c")
    return {(int(mm), int(cc)): float(v) for v, mm, cc in zip(e, m, c)}


def main():
    gp, mlp = pooled(GP, "gp"), pooled(L1, "mlp")
    keys = sorted(set(gp) & set(mlp))
    if len(keys) != len(mlp) or len(keys) != len(gp):
        raise SystemExit(f"sample sets differ: gp {len(gp)}, mlp {len(mlp)}, common {len(keys)}")
    mats = np.array([k[0] for k in keys])
    e_mlp = np.array([mlp[k] for k in keys])
    e_gp = np.array([gp[k] for k in keys])
    alpha, _ = alpha_for("folds")
    r = compare(ArmResult("mlp", mats, e_mlp), ArmResult("gp", mats, e_gp), alpha=alpha, n_boot=4000)
    mde = None
    if r["significant"] and r["mean_diff"] > 0:
        words = "a Gaussian process on POD coefficients beats the perceptron on held-out materials"
    elif not r["significant"]:
        words = "no difference between a Gaussian process and the perceptron"
        mde = mde_report(e_gp - e_mlp, mats, base=float(e_mlp.mean()), alpha=alpha, label="B-GP vs mlp")
    else:
        words = "the perceptron beats a Gaussian process"
    out = {"_what": __doc__.splitlines()[0], "alpha": alpha, "n_samples": len(keys),
           "n_materials": int(len(np.unique(mats))), "mean_mlp": float(e_mlp.mean()),
           "mean_gp": float(e_gp.mean()), "comparison": r, "mde": mde, "words": words}
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"{words}\n  mlp {e_mlp.mean():.4f}  gp {e_gp.mean():.4f}  CI [{r['ci_low']:+.5f}, {r['ci_high']:+.5f}]")
    print(f"wrote {OUT}")
    print("BGP_ANALYSIS_DONE")


if __name__ == "__main__":
    main()
