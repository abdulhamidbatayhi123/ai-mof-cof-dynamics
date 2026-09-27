"""Profile likelihood of k with the LDF law KNOWN (PREREG_P2 §4.3): the classical
practical-identifiability test the discovery boundary is compared against. For each k
on a log grid, integrate dq/dt = k (q*(c(t)) - q) with c(t) interpolated from data;
Gaussian log-likelihood against observed q; the 95 % interval is where
2 * (max loglik - loglik) <= 3.84. 'Practically identifiable' iff the interval lies
within [k/2, 2k]."""
import numpy as np
from scipy.integrate import solve_ivp


def _loglik(k, t, c, q_obs, qstar_fn, sigma):
    sol = solve_ivp(lambda tt, q: k * (qstar_fn(np.interp(tt, t, c)) - q), (t[0], t[-1]),
                    [q_obs[0]], t_eval=t, rtol=1e-8, atol=1e-10)
    if not sol.success:
        return -np.inf
    return -0.5 * np.sum((sol.y[0] - q_obs) ** 2) / sigma ** 2


def profile_interval(t, c, q_obs, qstar_fn, sigma, k_grid=None):
    k_grid = np.logspace(-5, 1, 241) if k_grid is None else k_grid
    ll = np.array([_loglik(k, t, c, q_obs, qstar_fn, sigma) for k in k_grid])
    ok = np.where(2.0 * (ll.max() - ll) <= 3.84)[0]
    # Second pass: at low noise the interval is narrower than one coarse step (found on
    # the known-answer test -- it collapsed onto one grid point below the truth), so
    # refine between the coarse neighbours of the interval's ends.
    i0, i1 = max(ok.min() - 1, 0), min(ok.max() + 1, len(k_grid) - 1)
    fine = np.logspace(np.log10(k_grid[i0]), np.log10(k_grid[i1]), 201)
    llf = np.array([_loglik(k, t, c, q_obs, qstar_fn, sigma) for k in fine])
    m = max(ll.max(), llf.max())
    okf = 2.0 * (m - llf) <= 3.84
    return float(fine[okf].min()), float(fine[okf].max())


def identifiable(lo, hi, k_true):
    return lo >= k_true / 2 and hi <= 2 * k_true
