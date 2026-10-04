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


UPSAMPLE = 4      # q*(t) evaluated on a 4x finer grid by PCHIP of the observed drivers


def _qstar_path(t, c, qstar_fn, T=None):
    """q*(t) on a UPSAMPLE-times finer grid, from PCHIP-interpolated observed drivers
    (the same interpolant _loglik uses)."""
    from scipy.interpolate import PchipInterpolator
    tf = np.linspace(t[0], t[-1], (len(t) - 1) * UPSAMPLE + 1)
    cf = PchipInterpolator(t, c)(tf)
    qs = qstar_fn(cf) if T is None else qstar_fn(cf, PchipInterpolator(t, T)(tf))
    return tf, np.asarray(qs, float)


def _ldf_exact(k, tf, qs, q0):
    """dq/dt = k (q*(t) - q), q* piecewise LINEAR on tf: the exact update per interval
    q1 = e q0 + (1 - e) qs1 - (qs1 - qs0) (1 - (1 - e) / (k h)),  e = exp(-k h),
    vectorised over k (array). Exact for the interpolated q*, no ODE solver."""
    k = np.atleast_1d(np.asarray(k, float))[:, None]
    h = np.diff(tf)[None, :]
    e = np.exp(-k * h)
    kh = k * h
    g = np.where(kh > 1e-8, (1 - e) / np.where(kh > 1e-8, kh, 1.0), 1 - kh / 2)
    q = np.empty((k.shape[0], tf.size))
    q[:, 0] = q0
    for i in range(tf.size - 1):
        q[:, i + 1] = (e[:, i] * q[:, i] + (1 - e[:, i]) * qs[i + 1]
                       - (qs[i + 1] - qs[i]) * (1 - g[:, i]))
    return q


def loglik_o1(k, t, cs, qs_obs, qstar_fn, sigma, Ts=None):
    """Summed Gaussian log-likelihood over all probes, for an ARRAY of k, by the exact
    LDF update -- the same model as _loglik (PCHIP drivers, LDF ODE), verified against
    it by test, at a small fraction of the cost."""
    Ts = [None] * len(cs) if Ts is None else Ts
    k = np.atleast_1d(np.asarray(k, float))
    ll = np.zeros(k.size)
    for c, q_obs, T in zip(cs, qs_obs, Ts):
        tf, qs = _qstar_path(t, c, qstar_fn, T)
        q = _ldf_exact(k, tf, qs, q_obs[0])[:, ::UPSAMPLE]
        ll += -0.5 * np.sum((q - q_obs[None, :]) ** 2, axis=1) / sigma ** 2
    return ll


def profile_interval_o1(t, cs, qs_obs, qstar_fn, sigma, Ts=None, k_grid=None):
    """O1 identifiability over ALL probes (information parity with discovery, which sees
    every probe): log-likelihoods summed over probes, by the exact LDF update. Same
    coarse grid and adaptive refinement as the other profiles (_profile). The solver-based
    version took ~540 s per replicate at the grid's size, ~860 h for the H2b design."""
    f = lambda ks: loglik_o1(ks, t, cs, qs_obs, qstar_fn, sigma, Ts)     # whole grid at once
    return _profile(f, np.logspace(-5, 1, 61) if k_grid is None else k_grid, vectorised=True)


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


def _loglik_probes(k, phys, c_in, t, z_obs, c_obs, T_obs, sigma_c, sigma_T, n_z):
    """Refit the WHOLE column at rate k and score c, T at the interior probes (O2).
    c_obs, T_obs: (n_probes, n_t); z_obs in metres, interpolated on the model's cells."""
    import copy
    from solver_fd import generate_breakthrough_data
    p = copy.copy(phys)
    p.k_LDF = float(k)
    try:
        zz, tt, y = generate_breakthrough_data(p, N_z=n_z, t_final=float(t[-1]), c_in=c_in,
                                               n_snapshots=len(t), verbose=False)
    except RuntimeError:
        return -np.inf
    c_f, T_f = y[:n_z], y[2 * n_z:3 * n_z]
    ll = 0.0
    for j, zj in enumerate(np.asarray(z_obs, float)):
        c_t = np.array([np.interp(zj, zz, c_f[:, i]) for i in range(len(tt))])
        T_t = np.array([np.interp(zj, zz, T_f[:, i]) for i in range(len(tt))])
        ll += (-0.5 * np.sum((np.interp(t, tt, c_t) - c_obs[j]) ** 2) / sigma_c ** 2
               - 0.5 * np.sum((np.interp(t, tt, T_t) - T_obs[j]) ** 2) / sigma_T ** 2)
    return ll


def profile_interval_probes(phys, c_in, t, z_obs, c_obs, T_obs, sigma_c, sigma_T, n_z=100,
                            k_grid=None):
    """Profile likelihood of k from INTERIOR c, T probes (observation O2, q latent):
    the identifiability side of H2b on O2. Same grid and refinement as the outlet
    version; only the scored positions differ."""
    f = lambda k: _loglik_probes(k, phys, c_in, t, z_obs, c_obs, T_obs, sigma_c, sigma_T, n_z)
    return _profile(f, k_grid)


def profile_interval_outlet(phys, c_in, t, c_obs, T_obs, sigma_c, sigma_T, n_z=100,
                            k_grid=None):
    """Profile likelihood of k from OUTLET data only. Coarse 25-point log grid, then
    the same fine refinement as the ODE version -- each point is a full column solve,
    so the grid is coarser than the ODE's (PREREG_P2 §3 applicability matrix)."""
    f = lambda k: _loglik_outlet(k, phys, c_in, t, c_obs, T_obs, sigma_c, sigma_T, n_z)
    return _profile(f, k_grid)


def _profile(f, k_grid=None, vectorised=False):
    """The shared coarse-then-adaptive 95 % profile interval for a log-likelihood f(k);
    vectorised=True: f takes the whole k array at once."""
    k_grid = np.logspace(-6, 0, 25) if k_grid is None else k_grid
    ev = (lambda ks: np.asarray(f(np.asarray(ks)), float)) if vectorised else (lambda ks: np.array([f(k) for k in ks]))
    ll = ev(k_grid)
    ok = np.where(2.0 * (ll.max() - ll) <= 3.84)[0]
    i0, i1 = max(ok.min() - 1, 0), min(ok.max() + 1, len(k_grid) - 1)
    lo_k, hi_k, m = k_grid[i0], k_grid[i1], ll.max()
    # Refine until the interval spans >= 5 grid points (or the grid is finer than 0.1 %).
    # A single fixed refinement collapsed onto one point just below the truth on the
    # known-answer test -- the interval was narrower than the fine step.
    for _ in range(6):
        fine = np.logspace(np.log10(lo_k), np.log10(hi_k), 21)
        llf = ev(fine)
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
