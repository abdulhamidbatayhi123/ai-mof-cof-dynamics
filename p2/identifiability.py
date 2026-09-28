"""Profile likelihood of k with the LDF law KNOWN (PREREG_P2 §4.3): the classical
practical-identifiability test the discovery boundary is compared against. For each k
on a log grid, integrate dq/dt = k (q*(c(t)) - q) with c(t) interpolated from data;
Gaussian log-likelihood against observed q; the 95 % interval is where
2 * (max loglik - loglik) <= 3.84. 'Practically identifiable' iff the interval lies
within [k/2, 2k]."""
import numpy as np
from scipy.integrate import solve_ivp


def _loglik(k, t, c, q_obs, qstar_fn, sigma, T=None):
    # T given (non-isothermal grid): q* depends on the observed temperature history too
    # Cubic (PCHIP, monotone-preserving) interpolation of the observed drivers: linear
    # interpolation between 200 snapshots biased k_hat by +0.61 % on noise-free data
    # (0.17 % at 800), enough to exclude the truth from a low-noise interval.
    from scipy.interpolate import PchipInterpolator
    ci = PchipInterpolator(t, c)
    if T is None:
        qs = lambda tt: qstar_fn(ci(tt))
    else:
        Ti = PchipInterpolator(t, T)
        qs = lambda tt: qstar_fn(ci(tt), Ti(tt))
    sol = solve_ivp(lambda tt, q: k * (qs(tt) - q), (t[0], t[-1]),
                    [q_obs[0]], t_eval=t, rtol=1e-8, atol=1e-10)
    if not sol.success:
        return -np.inf
    return -0.5 * np.sum((sol.y[0] - q_obs) ** 2) / sigma ** 2


def profile_interval(t, c, q_obs, qstar_fn, sigma, k_grid=None, T=None):
    k_grid = np.logspace(-5, 1, 241) if k_grid is None else k_grid
    ll = np.array([_loglik(k, t, c, q_obs, qstar_fn, sigma, T) for k in k_grid])
    ok = np.where(2.0 * (ll.max() - ll) <= 3.84)[0]
    # Second pass: at low noise the interval is narrower than one coarse step (found on
    # the known-answer test -- it collapsed onto one grid point below the truth), so
    # refine between the coarse neighbours of the interval's ends.
    i0, i1 = max(ok.min() - 1, 0), min(ok.max() + 1, len(k_grid) - 1)
    lo_k, hi_k, m = k_grid[i0], k_grid[i1], ll.max()
    for _ in range(6):   # same adaptive refinement as profile_interval_outlet
        fine = np.logspace(np.log10(lo_k), np.log10(hi_k), 41)
        llf = np.array([_loglik(k, t, c, q_obs, qstar_fn, sigma, T) for k in fine])
        m = max(m, llf.max())
        okf = np.where(2.0 * (m - llf) <= 3.84)[0]
        j0, j1 = max(okf.min() - 1, 0), min(okf.max() + 1, len(fine) - 1)
        if okf.size >= 5 or fine[1] / fine[0] < 1.001:
            break
        lo_k, hi_k = fine[j0], fine[j1]
    return float(fine[j0]), float(fine[j1])


def _loglik_outlet(k, phys, c_in, t, c_obs, T_obs, sigma_c, sigma_T, n_z):
    """Refit the WHOLE column at rate k and score its outlet c(t), T(t) (observation O3)."""
    import copy
    from solver_fd import generate_breakthrough_data
    p = copy.copy(phys)
    p.k_LDF = float(k)
    try:
        _, tt, y = generate_breakthrough_data(p, N_z=n_z, t_final=float(t[-1]), c_in=c_in,
                                              n_snapshots=len(t), verbose=False)
    except RuntimeError:
        return -np.inf
    c_mod = np.interp(t, tt, y[n_z - 1])
    T_mod = np.interp(t, tt, y[3 * n_z - 1])
    return (-0.5 * np.sum((c_mod - c_obs) ** 2) / sigma_c ** 2
            - 0.5 * np.sum((T_mod - T_obs) ** 2) / sigma_T ** 2)


def profile_interval_outlet(phys, c_in, t, c_obs, T_obs, sigma_c, sigma_T, n_z=100,
                            k_grid=None):
    """Profile likelihood of k from OUTLET data only. Coarse 25-point log grid, then
    the same fine refinement as the ODE version -- each point is a full column solve,
    so the grid is coarser than the ODE's (PREREG_P2 §3 applicability matrix)."""
    k_grid = np.logspace(-6, 0, 25) if k_grid is None else k_grid
    f = lambda k: _loglik_outlet(k, phys, c_in, t, c_obs, T_obs, sigma_c, sigma_T, n_z)
    ll = np.array([f(k) for k in k_grid])
    ok = np.where(2.0 * (ll.max() - ll) <= 3.84)[0]
    i0, i1 = max(ok.min() - 1, 0), min(ok.max() + 1, len(k_grid) - 1)
    lo_k, hi_k, m = k_grid[i0], k_grid[i1], ll.max()
    # Refine until the interval spans >= 5 grid points (or the grid is finer than 0.1 %).
    # A single fixed refinement collapsed onto one point just below the truth on the
    # known-answer test -- the interval was narrower than the fine step.
    for _ in range(6):
        fine = np.logspace(np.log10(lo_k), np.log10(hi_k), 21)
        llf = np.array([f(k) for k in fine])
        m = max(m, llf.max())
        okf = np.where(2.0 * (m - llf) <= 3.84)[0]
        j0, j1 = max(okf.min() - 1, 0), min(okf.max() + 1, len(fine) - 1)
        if okf.size >= 5 or fine[1] / fine[0] < 1.001:
            break
        lo_k, hi_k = fine[j0], fine[j1]
    # the interval ends lie between the last in-set point and its outside neighbour;
    # report the outside neighbours so the interval is conservative, never truncated
    return float(fine[j0]), float(fine[j1])


def identifiable(lo, hi, k_true):
    return lo >= k_true / 2 and hi <= 2 * k_true
