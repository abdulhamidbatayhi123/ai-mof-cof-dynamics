"""PREREG_P2 §4.3 estimands, fixed before the freeze.

boundary(successes_by_da): Da*_disc -- the 50 % crossing of P(success) from a logistic
fit in log10(Da) (maximum likelihood on the replicate-level outcomes), with a
percentile bootstrap CI that resamples replicates WITHIN each Da level (the design is
fixed; only the stochastic replicates are resampled). Returns (None, None, None) when
there is no crossing inside the tested range -- all successes or all failures, or a
fitted slope with the wrong sign -- because extrapolating a boundary off the grid is
exactly the unsupported number rule 10 forbids.
"""
from collections import defaultdict

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


def boundary_draws(successes_by_da, n_boot=2000, seed=0, rising=False):
    """The log10 50 % crossing and its n_boot bootstrap draws (replicates resampled within
    each level). A draw without a crossing is NaN, so draws from two boundaries made with
    the same n_boot can be paired index by index. Returns (b or None, array of n_boot)."""
    das = sorted(successes_by_da)
    x = np.concatenate([[np.log10(d)] * len(successes_by_da[d]) for d in das])
    y = np.concatenate([np.asarray(successes_by_da[d], float) for d in das])
    b = _fit(x, y, rising)
    draws = np.full(n_boot, np.nan)
    if b is None:
        return None, draws
    rng = np.random.default_rng(seed)
    for i in range(n_boot):
        xs, ys = [], []
        for d in das:
            s = np.asarray(successes_by_da[d], float)
            idx = rng.integers(0, len(s), len(s))
            xs.append(np.full(len(s), np.log10(d)))
            ys.append(s[idx])
        bb = _fit(np.concatenate(xs), np.concatenate(ys), rising)
        if bb is not None:
            draws[i] = bb
    return b, draws


def _ci(draws):
    """Percentile 95 % interval of the finite draws, or (None, None) if there are none
    (A2: an empty set of draws no longer raises)."""
    d = np.asarray(draws, float)
    d = d[np.isfinite(d)]
    if d.size == 0:
        return None, None
    lo, hi = np.percentile(d, [2.5, 97.5])
    return float(lo), float(hi)


def boundary(successes_by_da, n_boot=2000, seed=0, rising=False):
    b, draws = boundary_draws(successes_by_da, n_boot, seed, rising)
    if b is None:
        return None, None, None
    lo, hi = _ci(draws)
    return 10 ** b, (None if lo is None else 10 ** lo), (None if hi is None else 10 ** hi)


def paired_shift(pairs_by_da, n_boot=2000, seed=0):
    """A2.5 as written: log10 Da*(a) - log10 Da*(b) where a and b were run on the SAME
    replicate observations; pairs_by_da = {Da: [(a_outcome, b_outcome), ...]}, one pair per
    shared replicate. Each bootstrap draw resamples the replicate indices within each Da
    level once and applies them to both, so the interval keeps the pairing.
    Returns (shift or None, lo, hi)."""
    das = sorted(d for d in pairs_by_da if len(pairs_by_da[d]))
    if not das:
        return None, None, None
    arr = {d: np.asarray(pairs_by_da[d], float) for d in das}
    x = np.concatenate([np.full(len(arr[d]), np.log10(d)) for d in das])
    fa = _fit(x, np.concatenate([arr[d][:, 0] for d in das]))
    fb = _fit(x, np.concatenate([arr[d][:, 1] for d in das]))
    if fa is None or fb is None:
        return None, None, None
    rng = np.random.default_rng(seed)
    draws = np.full(n_boot, np.nan)
    for i in range(n_boot):
        ya, yb = [], []
        for d in das:
            idx = rng.integers(0, len(arr[d]), len(arr[d]))
            ya.append(arr[d][idx, 0])
            yb.append(arr[d][idx, 1])
        a, b = _fit(x, np.concatenate(ya)), _fit(x, np.concatenate(yb))
        if a is not None and b is not None:
            draws[i] = a - b
    lo, hi = _ci(draws)
    return float(fa - fb), lo, hi


def r_collapse(successes_by_cond, spread_ok=0.5, spread_fail=1.0, n_boot=2000):
    """H2a (PREREG_P2 §2). Each condition maps R-level -> replicate successes. The
    50 % crossing R* is estimated per condition; the spread is max - min of log10 R*.
    Pre-declared words: spread < half a decade -> "R collapses the boundary"; spread
    >= one decade -> "R does not collapse the boundary" (the falsifier); between the two
    -> "inconclusive", stated as such. A condition with no crossing is listed, never
    imputed."""
    rstar, missing, draws = {}, [], []
    for i, (cond, succ) in enumerate(successes_by_cond.items()):
        # success RISES with R (more driving force per unit error); a first version
        # used the falling-curve rule of the Da boundary and could never find a crossing
        b, d = boundary_draws(succ, n_boot=n_boot, seed=i, rising=True)
        if b is None:
            missing.append(cond)
        else:
            lo, hi = _ci(d)
            rstar[cond] = (10 ** b, None if lo is None else 10 ** lo, None if hi is None else 10 ** hi)
            draws.append(d)
    logs = [np.log10(v[0]) for v in rstar.values()]
    spread = float(max(logs) - min(logs)) if len(logs) >= 2 else None
    # A2: the bootstrap interval of the spread (stated in s.4.3, missing until A2)
    spread_ci = (None, None)
    if len(draws) >= 2 and n_boot > 0:
        D = np.vstack(draws)
        ok = np.all(np.isfinite(D), axis=0)
        spread_ci = _ci((D.max(axis=0) - D.min(axis=0))[ok])
    if spread is None:
        words = "no verdict: fewer than two conditions have a crossing"
    elif spread < spread_ok:
        words = f"R collapses the boundary (spread {spread:.2f} decade)"
    elif spread >= spread_fail:
        words = f"R does not collapse the boundary (spread {spread:.2f} decade)"
    else:
        words = f"inconclusive: R narrows the boundary to a spread of {spread:.2f} decades"
    return {"rstar": rstar, "no_crossing": missing, "spread_decades": spread,
            "spread_ci": list(spread_ci), "words": words}


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
    if not boots:                     # no draw has a crossing: the interval is undefined
        return best, pts[best], None, None
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return best, pts[best], 10 ** lo, 10 ** hi


def refine_levels(da_star, n=8, half_width=0.5):
    """H2c refinement grid (PREREG_P2 s.4.4, made exact by A1): n levels equally spaced in
    log10 Da strictly inside +-half_width decade of da_star (the two end points excluded)."""
    if da_star is None:
        return []
    x = np.linspace(np.log10(da_star) - half_width, np.log10(da_star) + half_width, n + 2)[1:-1]
    return [float(v) for v in 10.0 ** x]


def select_best(by_method_sel, rising=False):
    """Amendment A1 (PREREG_P2 s.9): the best method is chosen on the SELECTION replicates
    only, so its boundary can be estimated without selection bias on the independent
    ESTIMATION replicates. Chosen: the largest 50 % crossing (the smallest R* when
    rising). If no method has a crossing on the selection set, the method with the highest
    mean success is chosen (it may still have one on the estimation set). Returns the
    method label, or None if there is no method."""
    if not by_method_sel:
        return None
    pts = {m: boundary(s, n_boot=0, rising=rising)[0] for m, s in by_method_sel.items()}   # point estimate only (A2)
    pts = {m: v for m, v in pts.items() if v is not None}
    if pts:
        return (min if rising else max)(pts, key=pts.get)
    return max(by_method_sel, key=lambda m: np.mean([np.mean(v) for v in by_method_sel[m].values()]))


H2B_WORDS = ("discovery fails before identifiability", "discovery fails with identifiability",
             "discovery outlives identifiability")


def aggregate_h2b(slice_words, share=2.0 / 3.0):
    """Amendment A1: the hypothesis-level H2b verdict from the O1 slice verdicts. A word
    held by at least two thirds of the slices that have a verdict is the overall verdict;
    otherwise "mixed". Slices without a verdict (no crossing) are counted and listed,
    never imputed."""
    counted = {w: 0 for w in H2B_WORDS}
    none = []
    for sl, w in slice_words.items():
        if w in counted:
            counted[w] += 1
        else:
            none.append(sl)
    n = sum(counted.values())
    # A1.4 as written: the counts by each slicing axis (the slice key's '|'-separated parts)
    by_axis = defaultdict(lambda: {w: 0 for w in H2B_WORDS})
    for sl, w in slice_words.items():
        if w in H2B_WORDS:
            for part in str(sl).split("|"):
                by_axis[part][w] += 1
    if n == 0:
        return {"words": "no verdict: no slice has a boundary for both", "counts": counted,
                "counts_by_axis": dict(by_axis), "no_verdict": none}
    top = max(counted, key=counted.get)
    words = top if counted[top] >= share * n else (
        "mixed: the position of discovery relative to identifiability depends on the slice")
    return {"words": words, "counts": counted, "counts_by_axis": dict(by_axis),
            "n_with_verdict": n, "no_verdict": none}


def positive_control(success, identifiable, need=0.9):
    """Amendment A1, outcome-neutral check on the grid itself: at sigma = eps = 0, O1, the
    lowest Da level, the best method must succeed and k must be identifiable in at least
    `need` of the estimation replicates. Returns (passed, detail)."""
    fs = float(np.mean(success)) if len(success) else 0.0
    fi = float(np.mean(identifiable)) if len(identifiable) else 0.0
    return (fs >= need and fi >= need), {"success_fraction": fs, "identifiable_fraction": fi,
                                          "n_success": len(success), "n_ident": len(identifiable),
                                          "need": need}


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
    # Amendment A1: H2c HOLDS at an eps if the upward shift is detectable (>= the decision
    # threshold); the factor-2 words grade the size and are descriptive.
    holds = {e: v >= mde_decades for e, v in shifts.items()}
    return {"words": words, "shifts": shifts, "holds_by_eps": holds,
            "h2c_holds": any(holds.values()),
            "h2c_falsified": all(v < mde_decades for v in shifts.values())}
