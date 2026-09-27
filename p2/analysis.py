"""PREREG_P2 §4.3 estimands, fixed before the freeze.

boundary(successes_by_da): Da*_disc -- the 50 % crossing of P(success) from a logistic
fit in log10(Da) (maximum likelihood on the replicate-level outcomes), with a
percentile bootstrap CI that resamples replicates WITHIN each Da level (the design is
fixed; only the stochastic replicates are resampled). Returns (None, None, None) when
there is no crossing inside the tested range -- all successes or all failures, or a
fitted slope with the wrong sign -- because extrapolating a boundary off the grid is
exactly the unsupported number rule 10 forbids.
"""
import numpy as np
from scipy.optimize import minimize


def _fit(x, y):
    """Logistic P = 1 / (1 + exp(a (x - b))); returns b (log10 Da at 50 %) or None."""
    if y.all() or not y.any():
        return None
    from sklearn.linear_model import LogisticRegression
    # unpenalised maximum likelihood; P(success) = sigma(w x + c), crossing at -c / w
    m = LogisticRegression(penalty=None, max_iter=1000).fit(x[:, None], y.astype(int))
    w, c = float(m.coef_[0, 0]), float(m.intercept_[0])
    if w >= 0:          # success must FALL with Da for a boundary to mean anything
        return None
    b = -c / w
    if not (x.min() <= b <= x.max()):
        return None
    return float(b)


def boundary(successes_by_da, n_boot=2000, seed=0):
    das = sorted(successes_by_da)
    x = np.concatenate([[np.log10(d)] * len(successes_by_da[d]) for d in das])
    y = np.concatenate([np.asarray(successes_by_da[d], float) for d in das])
    b = _fit(x, y)
    if b is None:
        return None, None, None
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        xs, ys = [], []
        for d in das:
            s = np.asarray(successes_by_da[d], float)
            idx = rng.integers(0, len(s), len(s))
            xs.append(np.full(len(s), np.log10(d)))
            ys.append(s[idx])
        bb = _fit(np.concatenate(xs), np.concatenate(ys))
        if bb is not None:
            boots.append(bb)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return 10 ** b, 10 ** lo, 10 ** hi
