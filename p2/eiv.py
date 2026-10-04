"""M5 as run on the grid: errors-in-variables sparse regression on the single rate law.

Why not the ODR-BINDy port directly (decided 2026-10-04, before the freeze): the port
(p2/odr_bindy.py, verified on its authors' Lorenz example) learns AUTONOMOUS polynomial
systems -- it denoises every state and fits an equation for each. Paper 2's target is
ONE rate equation, dq/dt = f(c, q, T, q*_meas), inside a PDE whose c and T are driven
from outside, with the dominant error in a REGRESSOR (the measured isotherm). That is
not the problem ODR-BINDy was written for, and extending it would be new method
development. What H2c asks -- does treating the regressors as error-carrying move the
boundary? -- is answered by the canonical errors-in-variables estimator applied to the
same search as M4:

  for every support of size <= max_terms (M4's exact enumeration), fit by MIXED
  LS-TLS (Golub, Hoffman & Stewart 1987; total least squares, Golub & Van Loan 1980):
  exact columns (the constant) by least squares, error-carrying columns and the target
  by total least squares after scaling each by its DECLARED error SD (from the
  observation model); select by the same floored BIC as M4.

TLS is computed directly by SVD. scipy.odr was tried first and crashed the process with
a Windows access violation inside ODRPACK, so it is not used.

Labelled "EIV best-subset (classical mixed LS-TLS)". The ODR-BINDy port is reported on
its own published example, with its accuracy gap, as the prereg declares.
"""
import itertools

import numpy as np


def mixed_ls_tls(X, y, sd_cols, sd_y):
    """Coefficients for y ~ X with per-column error SDs sd_cols (0 = exact column) and
    target error SD sd_y (scalars). Exact columns are projected out (LS), the rest solved
    by TLS on SD-scaled columns, then the exact columns' coefficients by LS on the
    remainder."""
    sd_cols = np.asarray(sd_cols, float)
    exact = sd_cols <= 0
    noisy = ~exact
    beta = np.zeros(X.shape[1])
    if not noisy.any():
        return np.linalg.lstsq(X, y, rcond=None)[0]
    E, N = X[:, exact], X[:, noisy]
    if E.shape[1]:
        Q, _ = np.linalg.qr(E)
        P = lambda A: A - Q @ (Q.T @ A)
        Np, yp = P(N), P(y)
    else:
        Np, yp = N, y
    w = sd_cols[noisy]
    Z = np.column_stack([Np / w, yp / sd_y])
    _, _, Vt = np.linalg.svd(Z, full_matrices=False)
    v = Vt[-1]
    if abs(v[-1]) < 1e-14:                       # TLS solution does not exist (nongeneric)
        b_n = np.linalg.lstsq(Np, yp, rcond=None)[0]
    else:
        b_n = (-v[:-1] / v[-1]) * sd_y / w
    beta[noisy] = b_n
    if E.shape[1]:
        beta[exact] = np.linalg.lstsq(E, y - N @ b_n, rcond=None)[0]
    return beta


def eiv_best_subset(F, y, sd_cols, sd_y, max_terms=4, floor=2e-3):
    """F: {term: column}; sd_cols: {term: error SD of that column} (0 for exact columns,
    e.g. the constant); sd_y: error SD of y. Returns {term: coefficient}."""
    names = list(F)
    X = np.column_stack([F[n] for n in names]).astype(float)
    s = np.array([float(np.mean(np.asarray(sd_cols.get(n, 0.0), float))) for n in names])
    sdy = max(float(np.mean(np.asarray(sd_y, float))), 1e-300)
    n = len(y)
    var_floor = (floor * float(np.std(y))) ** 2
    best, best_bic = None, np.inf
    for m in range(1, max_terms + 1):
        for sup in itertools.combinations(range(len(names)), m):
            sup = list(sup)
            beta = mixed_ls_tls(X[:, sup], y, s[sup], sdy)
            rss = float(np.sum((y - X[:, sup] @ beta) ** 2))
            bic = n * np.log(max(rss / n, var_floor)) + m * np.log(n)
            if bic < best_bic:
                best_bic, best = bic, (sup, beta)
    sup, beta = best
    return {names[j]: float(b) for j, b in zip(sup, beta)}
