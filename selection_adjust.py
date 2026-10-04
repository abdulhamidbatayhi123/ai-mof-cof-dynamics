"""Selection-adjusted intervals for a best-of-K comparison (referee 2026-10-04, M3).

Several verdicts compare the BEST of K candidate arms -- chosen on the held-out
materials -- against one reference, with the per-pair interval of metrics.compare.
That interval is valid for a pair fixed in advance; for a pair chosen after looking
at the same data it is anti-conservative, because the winner is partly the arm whose
noise happened to fall the right way.

The correction is the standard max-statistic (simultaneous) cluster bootstrap:
  1. resample MATERIALS with replacement -- the same draw for every arm, so the
     dependence between arms is kept;
  2. for each arm a, the centred bootstrap deviation  D*_a - d_a  of its mean paired
     difference (reference minus arm), STUDENTISED by that arm's bootstrap standard
     error se_a;
  3. q = the (1 - alpha) quantile over draws of  max_a |D*_a - d_a| / se_a;
  4. every arm's simultaneous interval is d_a +/- q * se_a.
Studentising matters: an unscaled max is set by the noisiest arm (a badly weighted
physics arm swings ten times more than a good one), which widened every interval
about tenfold in the first version of this module -- a correction that strong would
erase any effect and is not the max-T procedure (Romano & Wolf 2005).
Holding for all K arms at once, it holds in particular for whichever arm is selected,
however it was selected. It is wider than the per-pair interval, and that width is
the price of choosing on the test set.

    from selection_adjust import simultaneous
"""
import numpy as np


def simultaneous(diffs, material_ids, alpha, n_boot=4000, seed=0):
    """diffs: {arm: per-sample (reference - arm)}; returns {arm: {...}} and q.

    Positive difference = the arm is better than the reference."""
    arms = list(diffs)
    D = np.vstack([np.asarray(diffs[a], float) for a in arms])          # (K, n)
    mats = np.unique(material_ids)
    rows = [np.where(material_ids == m)[0] for m in mats]
    d = D.mean(1)
    rng = np.random.default_rng(seed)
    B = np.empty((n_boot, len(arms)))
    for b in range(n_boot):
        take = np.concatenate([rows[i] for i in rng.integers(0, len(mats), len(mats))])
        B[b] = D[:, take].mean(1)
    se = B.std(0, ddof=1)
    q = float(np.quantile(np.max(np.abs(B - d) / se, axis=1), 1 - alpha))
    out = {a: {"mean_diff": float(d[k]), "se": float(se[k]),
               "sim_lo": float(d[k] - q * se[k]), "sim_hi": float(d[k] + q * se[k]),
               "significant_simultaneous": bool(d[k] - q * se[k] > 0 or d[k] + q * se[k] < 0)}
           for k, a in enumerate(arms)}
    return out, q
