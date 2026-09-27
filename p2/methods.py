"""Discovery methods, each fit(features, target) -> {term: coefficient}.

M4 best_subset: exhaustive enumeration of every support up to max_terms, least squares
on standardised columns, selection by BIC. Solves the MIOSR objective EXACTLY (the
library is small), without a Gurobi licence.
M2 stlsq: sequentially thresholded least squares on standardised columns.
M3 ensemble: bagged STLSQ (E-SINDy) with per-term inclusion probabilities."""
import itertools

import numpy as np


def _standardise(F):
    names = list(F)
    X = np.column_stack([F[n] for n in names]).astype(float)
    sd = X.std(0)
    sd[sd == 0] = 1.0            # the constant column keeps scale 1
    return names, X / sd, sd


def best_subset(F, y, max_terms=4, floor=1e-3):
    """BIC with a residual-variance FLOOR at `floor` x std(y). Found on the known-answer
    test: at zero noise plain BIC keeps terms of relative size ~1e-4 (c, q^2) because it
    rewards fitting the derivative estimator's own systematic error without limit. The
    floor is the Savitzky-Golay estimator's verified accuracy (test_derivative_...),
    so no support can be bought by fitting below what the derivative can resolve."""
    names, Xs, sd = _standardise(F)
    n = len(y)
    var_floor = (floor * float(np.std(y))) ** 2
    best, best_bic = None, np.inf
    for m in range(1, max_terms + 1):
        for S in itertools.combinations(range(len(names)), m):
            A = Xs[:, S]
            beta, *_ = np.linalg.lstsq(A, y, rcond=None)
            rss = float(np.sum((y - A @ beta) ** 2))
            bic = n * np.log(max(rss / n, var_floor)) + m * np.log(n)
            if bic < best_bic:
                best_bic, best = bic, (S, beta)
    S, beta = best
    return {names[j]: float(b / sd[j]) for j, b in zip(S, beta)}


def stlsq(F, y, threshold=0.05, alpha=1e-6):
    """Threshold is on standardised coefficients relative to the largest."""
    names, Xs, sd = _standardise(F)
    keep = np.ones(len(names), bool)
    beta = np.zeros(len(names))
    for _ in range(20):
        beta = np.zeros(len(names))
        A = Xs[:, keep]
        beta[keep] = np.linalg.solve(A.T @ A + alpha * np.eye(A.shape[1]), A.T @ y)
        new = np.abs(beta) >= threshold * np.abs(beta).max()
        if (new == keep).all():
            break
        keep = new
    return {names[j]: float(beta[j] / sd[j]) for j in range(len(names)) if keep[j]}


def ensemble(F, y, n_models=100, frac=0.6, threshold=0.05, inclusion=0.6, seed=0):
    rng = np.random.default_rng(seed)
    n = len(y)
    fits = []
    for _ in range(n_models):
        idx = rng.choice(n, int(frac * n), replace=True)
        fits.append(stlsq({k: v[idx] for k, v in F.items()}, y[idx], threshold))
    out = {}
    for name in F:
        vals = [f[name] for f in fits if name in f]
        if len(vals) / n_models >= inclusion:
            out[name] = float(np.median(vals))
    return out


def slow_manifold(F_alg, q, max_terms=3):
    """M9: regress the STATE q (not its rate) on q-free features. Near local
    equilibrium the bed lies on the slow manifold q = q*(c, T); what is discoverable
    there is that algebraic law, not k. Exact best-subset on the algebraic problem."""
    return best_subset(F_alg, np.asarray(q, float), max_terms=max_terms)
