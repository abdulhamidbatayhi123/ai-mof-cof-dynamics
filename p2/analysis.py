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


def _fit(x, y, rising=False):
    """Logistic P = 1 / (1 + exp(a (x - b))); returns b (log10 x at 50 %) or None.
    rising=False: success must FALL with x (Da). rising=True: it must RISE (R)."""
    if y.all() or not y.any():
        return None
    from sklearn.linear_model import LogisticRegression
    # unpenalised maximum likelihood; P(success) = sigma(w x + c), crossing at -c / w
    m = LogisticRegression(penalty=None, max_iter=1000).fit(x[:, None], y.astype(int))
    w, c = float(m.coef_[0, 0]), float(m.intercept_[0])
    if (w <= 0) if rising else (w >= 0):   # the curve must go the declared way
        return None
    b = -c / w
    if not (x.min() <= b <= x.max()):
        return None
    return float(b)


def boundary(successes_by_da, n_boot=2000, seed=0, rising=False):
    das = sorted(successes_by_da)
    x = np.concatenate([[np.log10(d)] * len(successes_by_da[d]) for d in das])
    y = np.concatenate([np.asarray(successes_by_da[d], float) for d in das])
    b = _fit(x, y, rising)
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
        bb = _fit(np.concatenate(xs), np.concatenate(ys), rising)
        if bb is not None:
            boots.append(bb)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return 10 ** b, 10 ** lo, 10 ** hi


def r_collapse(successes_by_cond, spread_ok=0.5, spread_fail=1.0, n_boot=2000):
    """H2a (PREREG_P2 §2). Each condition maps R-level -> replicate successes. The
    50 % crossing R* is estimated per condition; the spread is max - min of log10 R*.
    Pre-declared words: spread < half a decade -> "R collapses the boundary"; spread
    >= one decade -> "R does not collapse the boundary" (the falsifier); between the two
    -> "inconclusive", stated as such. A condition with no crossing is listed, never
    imputed."""
    rstar, missing = {}, []
    for cond, succ in successes_by_cond.items():
        # success RISES with R (more driving force per unit error); a first version
        # used the falling-curve rule of the Da boundary and could never find a crossing
        est, lo, hi = boundary(succ, n_boot=n_boot, seed=0, rising=True)
        if est is None:
            missing.append(cond)
        else:
            rstar[cond] = (est, lo, hi)
    logs = [np.log10(v[0]) for v in rstar.values()]
    spread = float(max(logs) - min(logs)) if len(logs) >= 2 else None
    if spread is None:
        words = "no verdict: fewer than two conditions have a crossing"
    elif spread < spread_ok:
        words = f"R collapses the boundary (spread {spread:.2f} decade)"
    elif spread >= spread_fail:
        words = f"R does not collapse the boundary (spread {spread:.2f} decade)"
    else:
        words = f"inconclusive: R narrows the boundary to a spread of {spread:.2f} decades"
    return {"rstar": rstar, "no_crossing": missing, "spread_decades": spread, "words": words}


def disc_vs_ident(da_disc, da_ident, mde_decades):
    """H2b words, pre-declared. Compares log10 Da*_disc with log10 Da*_ident against the
    MDE measured before the freeze (0.25 decade, PREREG_P2 §4.4)."""
    if da_disc is None or da_ident is None:
        return {"gap_decades": None, "words": "no boundary on the grid for one of the two; "
                                               "reported as the range tested"}
    gap = float(np.log10(da_disc) - np.log10(da_ident))
    if gap <= -mde_decades:
        words = "discovery fails before identifiability"
    elif gap >= mde_decades:
        words = "discovery outlives identifiability"
    else:
        words = "discovery fails with identifiability"
    return {"gap_decades": gap, "words": words}


def best_method_boundary(by_method, n_boot=2000, seed=0):
    """H2a/H2b's 'best method' (PREREG_P2 §4.3): the method with the largest Da*_disc,
    with an interval that CARRIES the selection: each bootstrap draw resamples replicate
    indices per Da level ONCE and applies them to every method (replicate r is the same
    observation draw for all methods), recomputes every method's boundary and takes the
    largest. Returns (best_method, estimate, lo, hi), or (None, None, None, None) if no
    method has a crossing on the grid."""
    pts = {m: boundary(s, n_boot=0 or 1, seed=seed)[0] for m, s in by_method.items()}
    pts = {m: v for m, v in pts.items() if v is not None}
    if not pts:
        return None, None, None, None
    best = max(pts, key=pts.get)
    das = sorted(next(iter(by_method.values())))
    nrep = {d: len(next(iter(by_method.values()))[d]) for d in das}
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = {d: rng.integers(0, nrep[d], nrep[d]) for d in das}
        vals = []
        for s in by_method.values():
            x = np.concatenate([np.full(nrep[d], np.log10(d)) for d in das])
            y = np.concatenate([np.asarray(s[d], float)[idx[d]] for d in das])
            b = _fit(x, y)
            if b is not None:
                vals.append(b)
        if vals:
            boots.append(max(vals))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return best, pts[best], 10 ** lo, 10 ** hi


def h2c_verdict(shift_by_eps, mde_decades, factor2=float(np.log10(2.0))):
    """H2c words (PREREG_P2 §2, §4.4): shift = log10 Da*_disc(M5) - log10 Da*_disc(best
    non-EIV, strong form, O1), per eps > 0. Reported for the largest |shift|."""
    shifts = {e: v for e, v in shift_by_eps.items() if v is not None}
    if not shifts:
        return {"words": "no verdict: no boundary on the grid for one of the two", "shifts": {}}
    up = max(shifts.values())
    down = min(shifts.values())
    if up >= factor2:
        words = f"EIV moves the boundary by {10 ** up:.2f}x"
    elif up >= mde_decades:
        words = (f"EIV moves the boundary by {10 ** up:.2f}x, detectably but by less than the "
                 f"predicted factor 2")
    elif down <= -mde_decades:
        words = f"EIV moves the boundary DOWN by {10 ** -down:.2f}x"
    else:
        words = f"EIV does not move the boundary detectably (MDE {mde_decades} decade)"
    return {"words": words, "shifts": shifts}
