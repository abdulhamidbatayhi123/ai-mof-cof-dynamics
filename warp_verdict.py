"""Does the two-wave frame actually beat the fixed frame? Seeds, pairing, CI.

Why this file exists (defect B28)
---------------------------------
`warp_predict.py` ends by printing "two-wave frame now BEATS the fixed frame" and
writing `"beats_fixed_frame": true` into its results file. That verdict came from

    0.0508  (predicted two-wave warp, this run)
    0.0510  (fixed frame, a HARD-CODED LITERAL imported from comoving.py:57)

with **one seed**, **no bootstrap**, **no confidence interval**, and a baseline that
was not recomputed alongside it. A 0.4 % margin declared on a single deterministic
run against a frozen constant is exactly what protocol section 3 rule 5 forbids
("single-seed numbers may not appear in any table, including appendices") and
section 4 forbids ("a difference whose CI includes zero is reported as no
difference, in words").

This is the project's best positive result. It is therefore the place where an
overclaim would cost the most, and the one number a referee is most likely to
probe. So it gets the full protocol:

  * both arms computed IN THE SAME RUN, on the same encoding, the same split, and
    the same regressor family -- no imported constants
  * three seeds, varying every stochastic component (the randomised SVD and the
    gradient-boosting early-stopping split)
  * the paired cluster-robust bootstrap by material at the calibrated alpha
  * the oracle arm reported alongside, and labelled as an upper bound that leaks
    the answer, never as a result

The arms
--------
  fixed        POD on the raw field + HGB on the parameters. This is L5's
               strongest non-operator arm and the thing to beat.
  two_wave     the same, in the frame sigma = (t - t_lo(z)) / (t_hi(z) - t_lo(z)),
               with t_lo and t_hi PREDICTED from the parameters. Honest.
  two_wave_oracle
               the same, handed the true t_lo and t_hi. NOT a result -- it is the
               ceiling the honest arm is trying to reach, and it is reported only
               to size the remaining headroom.

Output: results/warp_verdict.json
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor

from comoving import arrival_time, load_c_light, nrmse
from comoving2 import N_SIG, SIG_HI, SIG_LO, unwarp2, warp2
from metrics import ALPHA_CALIBRATED, ArmResult, compare

LEVELS = (0.05, 0.95)      # the pair comoving2 ranked best
P_SHAPE = 32               # flat over 8..128 in both frames; any value represents it
P_WARP = 4                 # warp_predict: 4 modes was optimal for start_logspan
SEEDS = (42, 43, 44)


def pod_hgb(target, Pz, tr, n_comp, seed):
    """POD on the training split + per-mode gradient boosting. Returns predictions.

    Both the randomised SVD and HGB's internal early-stopping split are seeded, so
    a change of `seed` moves every stochastic part of the arm and the seed spread
    is a real estimate of run-to-run variation rather than of nothing.
    """
    flat = target.reshape(target.shape[0], -1)
    n_comp = min(n_comp, len(tr) - 1, flat.shape[1])
    pca = PCA(n_components=n_comp, svd_solver="randomized", random_state=seed).fit(flat[tr])
    A = pca.transform(flat)
    mu, sd = A[tr].mean(0), A[tr].std(0)
    sd[sd == 0] = 1.0
    Az = (A - mu) / sd
    P = np.empty_like(Az)
    for k in range(n_comp):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          early_stopping=True, random_state=seed)
        m.fit(Pz[tr], Az[tr, k])
        P[:, k] = m.predict(Pz)
    return pca.inverse_transform(P * sd + mu).reshape(target.shape)


def predict_warp(t_lo, span, Pz, tr, seed):
    """Predict the two front trajectories in the (start, log-span) parameterisation.

    warp_predict measured this to be the better-conditioned target: predicting
    t_lo and t_hi independently ignores that they are strongly correlated, while
    (start, log span) separates WHERE the transition begins from HOW WIDE it is --
    and the span varies 136x across this dataset, so its log is far better scaled.
    """
    lo_p = pod_hgb(t_lo, Pz, tr, P_WARP, seed)
    lg_p = pod_hgb(np.log(span), Pz, tr, P_WARP, seed)
    return lo_p, np.exp(lg_p)


def r2(pred, true, idx):
    return float(1.0 - ((pred[idx] - true[idx]) ** 2).sum()
                 / max(((true[idx] - true[idx].mean()) ** 2).sum(), 1e-30))


def main():
    t0 = time.time()
    X, Pz, mat, split = load_c_light()
    tr = np.where(split == "train")[0]
    nm = np.where(split == "novel_material")[0]
    N, NZ, NT = X.shape
    u = np.linspace(0.0, 1.0, NT)
    sig = np.linspace(SIG_LO, SIG_HI, N_SIG)

    lo, hi = LEVELS
    t_lo, _ = arrival_time(X, u, lo)
    t_hi, _ = arrival_time(X, u, hi)
    span = np.maximum(t_hi - t_lo, 1e-3)
    t_hi = t_lo + span
    print(f"\nlevels {lo} -> {hi}; span median {np.median(span):.4f}, "
          f"range {span.min():.5f}-{span.max():.4f} ({span.max()/span.min():.0f}x)")

    # The interpolation floor is the error of warping and unwarping with the TRUE
    # trajectories and the TRUE shape. It bounds everything the frame can achieve
    # and must be small relative to the effect, or the frame is manufacturing it.
    W_true = warp2(X, u, t_lo, t_hi, sig)
    floor = float(nrmse(unwarp2(W_true, u, t_lo, t_hi, sig), X)[nm].mean())
    print(f"interpolation floor (oracle warp + oracle shape): {floor:.5f}")

    per_seed = {"fixed": [], "two_wave": [], "two_wave_oracle": []}
    samples = {}
    for seed in SEEDS:
        # ── arm 1: the fixed frame, recomputed here, not imported ────────────
        rec_fixed = pod_hgb(X, Pz, tr, P_SHAPE, seed)
        e_fixed = nrmse(rec_fixed, X)

        # ── arm 2: two-wave frame with a PREDICTED warp (the honest arm) ─────
        lo_p, span_p = predict_warp(t_lo, span, Pz, tr, seed)
        hi_p = lo_p + np.maximum(span_p, 1e-3)
        W_p = warp2(X, u, lo_p, hi_p, sig)
        shape_p = pod_hgb(W_p, Pz, tr, P_SHAPE, seed)
        e_two = nrmse(unwarp2(shape_p, u, lo_p, hi_p, sig), X)

        # ── arm 3: two-wave frame handed the true warp (an upper bound) ──────
        shape_o = pod_hgb(W_true, Pz, tr, P_SHAPE, seed)
        e_orc = nrmse(unwarp2(shape_o, u, t_lo, t_hi, sig), X)

        for k, e in (("fixed", e_fixed), ("two_wave", e_two), ("two_wave_oracle", e_orc)):
            per_seed[k].append(float(e[nm].mean()))
            samples.setdefault(k, []).append(e[nm])

        print(f"  seed {seed}: fixed {e_fixed[nm].mean():.5f} | "
              f"two-wave {e_two[nm].mean():.5f} | oracle {e_orc[nm].mean():.5f} | "
              f"warp R2 lo {r2(lo_p, t_lo, nm):+.3f} hi {r2(hi_p, t_hi, nm):+.3f} "
              f"[{time.time()-t0:.0f}s]", flush=True)

    print(f"\n{'arm':18s} {'mean':>8s} {'sd':>8s}   (3 seeds, novel-material split)")
    for k in ("fixed", "two_wave", "two_wave_oracle"):
        v = np.array(per_seed[k])
        print(f"{k:18s} {v.mean():8.5f} {v.std(ddof=1):8.5f}")

    # ── the verdict, paired and cluster-robust ───────────────────────────────
    mids = np.concatenate([mat[nm]] * len(SEEDS))
    def arm(k):
        return ArmResult(name=k, values=np.concatenate(samples[k]), material_ids=mids)

    print(f"\nPaired, cluster-robust by material, alpha = {ALPHA_CALIBRATED}:")
    r_main = compare(arm("fixed"), arm("two_wave"))
    print(f"  fixed {r_main['mean_a']:.5f} vs two-wave {r_main['mean_b']:.5f} | "
          f"diff {r_main['mean_diff']:+.5f} CI [{r_main['ci_low']:+.5f}, {r_main['ci_high']:+.5f}]")
    if not r_main["significant"]:
        verdict = ("NO DIFFERENCE. The two-wave frame does not beat the fixed frame "
                   "at the calibrated alpha. The frame's measured gain is entirely "
                   "consumed by the error in locating the two fronts.")
    elif r_main["mean_diff"] > 0:
        verdict = ("The two-wave frame is SIGNIFICANTLY BETTER than the fixed frame.")
    else:
        verdict = ("The two-wave frame is SIGNIFICANTLY WORSE than the fixed frame.")
    print(f"  -> {verdict}")

    r_orc = compare(arm("fixed"), arm("two_wave_oracle"))
    print(f"\n  fixed {r_orc['mean_a']:.5f} vs ORACLE warp {r_orc['mean_b']:.5f} | "
          f"diff {r_orc['mean_diff']:+.5f} CI [{r_orc['ci_low']:+.5f}, {r_orc['ci_high']:+.5f}]"
          f"  {'significant' if r_orc['significant'] else 'NO DIFFERENCE'}")
    head = np.mean(per_seed["two_wave"]) / np.mean(per_seed["two_wave_oracle"])
    print(f"  headroom between the honest arm and the oracle: {head:.2f}x")
    print("  NOTE: the oracle arm is handed the true front trajectories. It is an "
          "upper\n        bound on what a perfect front-locating model could buy, "
          "not a result,\n        and it may not be quoted against any arm that "
          "does not get the same.")

    if floor > 0.1 * np.mean(per_seed["two_wave_oracle"]):
        print(f"\n  WARNING: interpolation floor {floor:.5f} is >10% of the oracle "
              f"arm — the frame may be manufacturing part of the effect.")

    out = {
        "levels": list(LEVELS), "p_shape": P_SHAPE, "p_warp": P_WARP,
        "seeds": list(SEEDS), "interp_floor": floor,
        "per_seed": per_seed,
        "means": {k: float(np.mean(v)) for k, v in per_seed.items()},
        "sds": {k: float(np.std(v, ddof=1)) for k, v in per_seed.items()},
        "fixed_vs_two_wave": r_main,
        "fixed_vs_oracle": r_orc,
        "headroom_to_oracle": float(head),
        "verdict": verdict,
    }
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/warp_verdict.json", "w"), indent=2)
    print(f"\nwrote results/warp_verdict.json  [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
