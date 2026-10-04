"""selection_adjust.simultaneous must hold its family-wise level when the winner is
chosen after looking -- the property the paper relies on (referee M3)."""
import numpy as np

from selection_adjust import simultaneous


def _null_family(rng, k=8, n_mat=48, per_mat=4, noise_scale=None):
    """K arms, all with ZERO true difference to the reference; unequal noise per arm,
    material-level clustering, and correlation between arms (shared material effect)."""
    mats = np.repeat(np.arange(n_mat), per_mat)
    shared = rng.normal(0, 1.0, n_mat)[mats]
    scales = noise_scale if noise_scale is not None else np.geomspace(0.5, 5.0, k)
    diffs = {f"a{j}": scales[j] * (0.7 * shared + rng.normal(0, 1.0, mats.size)
                                   + rng.normal(0, 0.8, n_mat)[mats]) for j in range(k)}
    return diffs, mats


def test_selected_arm_false_positive_rate_is_held():
    rng = np.random.default_rng(1)
    alpha, trials, fp_sel, fp_naive = 0.10, 120, 0, 0
    for t in range(trials):
        diffs, mats = _null_family(rng)
        res, q = simultaneous(diffs, mats, alpha, n_boot=400, seed=t)
        best = max(res, key=lambda a: res[a]["mean_diff"] / res[a]["se"])   # pick the "winner"
        fp_sel += res[best]["significant_simultaneous"]
        fp_naive += abs(res[best]["mean_diff"] / res[best]["se"]) > 1.645
    # the selected arm's simultaneous interval keeps (roughly) the nominal level ...
    assert fp_sel / trials <= alpha + 0.07, fp_sel / trials
    # ... while the naive per-pair test on the selected arm does not
    assert fp_naive / trials > fp_sel / trials


def test_real_effect_is_still_detected():
    rng = np.random.default_rng(2)
    diffs, mats = _null_family(rng)
    diffs["a0"] = diffs["a0"] + 1.5                       # one arm truly better
    res, _ = simultaneous(diffs, mats, 0.05, n_boot=1000)
    assert res["a0"]["significant_simultaneous"]
