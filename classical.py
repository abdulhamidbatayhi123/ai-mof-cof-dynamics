"""Fast closed-form adsorption theory — the L7 classical control.

These cost microseconds and require NO training, so they serve two purposes:

  * a speed/accuracy reference the neural surrogates must beat to justify
    themselves at all;
  * a **zero-parameter transfer baseline** on held-out materials — nothing is
    fitted, so there is nothing to overfit, and any ML arm that fails to beat it
    on novel materials has not earned its parameters.

This is the analogue of the prior project's finding that a 128-number linear
convolution beat every deep operator tested.

Three levels, in increasing fidelity:

  equilibrium_shock  — Rhee/Aris/Amundson: infinitely fast kinetics, no
                       dispersion. The breakthrough is a step at the
                       stoichiometric time. Zero free parameters.
  klinkenberg        — Klinkenberg (1948) closed form for LDF kinetics with a
                       linear isotherm: an erfc in (xi, tau). Captures the finite
                       mass-transfer zone.
  constant_pattern   — for a FAVOURABLE isotherm the MTZ reaches a fixed shape,
                       so the breakthrough curve follows from the isotherm alone
                       by integrating the LDF rate along the front.

None of them can represent the two-wave structure a Type V isotherm produces
(section 6c), which is precisely what makes this an informative baseline rather
than a formality: where they fail is diagnostic.
"""
from __future__ import annotations

import numpy as np
from scipy.special import erfc

from isotherm import q_star_np

R_GAS = 8.314


def _stoich_time(p, c_in, T):
    q_eq = float(q_star_np(np.array([c_in]), np.array([T]), p)[0])
    capacity = (1 - p.eps_t) * p.rho_p * q_eq + p.eps_t * c_in
    return capacity * p.L / (p.v * c_in), q_eq


def equilibrium_shock(p, c_in, T, t):
    """Step at the stoichiometric time. The crudest possible reference."""
    t_st, _ = _stoich_time(p, c_in, T)
    return (t >= t_st).astype(float)


def klinkenberg(p, c_in, T, t):
    """Klinkenberg closed form: c/c0 = 0.5 erfc(sqrt(xi) - sqrt(tau) - 1/(8 sqrt(xi)) - 1/(8 sqrt(tau))).

    Derived for LDF kinetics with a LINEAR isotherm, so the effective Henry slope
    is taken as the chord q*(c_in)/c_in — the standard linearisation. That chord
    is exact for a linear isotherm and progressively wrong as the isotherm
    steepens, which is the error this baseline is meant to expose.
    """
    u = p.v / p.eps_t
    _, q_eq = _stoich_time(p, c_in, T)
    K = q_eq / c_in                                  # chord slope
    lam = (1 - p.eps_t) * p.rho_p * K / p.eps_t

    xi = p.k_LDF * lam * p.L / u
    tau = p.k_LDF * np.maximum(t - p.L / u, 0.0)

    sx = np.sqrt(np.maximum(xi, 1e-12))
    st = np.sqrt(np.maximum(tau, 1e-12))
    arg = sx - st - 1.0 / (8.0 * sx) - 1.0 / (8.0 * st)
    out = 0.5 * erfc(arg)
    return np.clip(np.where(tau > 0, out, 0.0), 0.0, 1.0)


def constant_pattern(p, c_in, T, t, n_quad=400):
    """Constant-pattern breakthrough for a favourable isotherm.

    In the constant-pattern limit the MTZ stops spreading, and along the front

        dX/dN = (1 - X) - (1 - Y(X)) ,   Y = q/q*(c_in),  X = c/c_in

    with N = k_LDF * lambda * L / u transfer units. Integrating gives the time at
    which each concentration level exits, which is inverted onto the requested
    time grid.

    For a Type V isotherm the front is NOT constant-pattern over its whole range
    — the convex branch spreads — so this is expected to fail on the early wave.
    That failure is the point of including it.
    """
    u = p.v / p.eps_t
    t_st, q_eq = _stoich_time(p, c_in, T)
    lam = (1 - p.eps_t) * p.rho_p * (q_eq / c_in) / p.eps_t
    N = p.k_LDF * lam * p.L / u

    X = np.linspace(1e-4, 1 - 1e-4, n_quad)
    cs = X * c_in
    q_of_c = q_star_np(cs, np.full_like(cs, T), p)
    Y = q_of_c / max(q_eq, 1e-30)

    denom = (Y - X)
    denom = np.where(np.abs(denom) < 1e-9, np.sign(denom) * 1e-9 + 1e-12, denom)
    integrand = 1.0 / denom
    Nz = np.concatenate([[0.0], np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(X))])
    Nz -= np.interp(0.5, X, Nz)                      # anchor the midpoint at t_st

    t_of_X = t_st + Nz / max(p.k_LDF, 1e-30) / max(N, 1e-30) * N
    order = np.argsort(t_of_X)
    return np.clip(np.interp(t, t_of_X[order], X[order], left=0.0, right=1.0), 0.0, 1.0)


MODELS = {
    "equilibrium_shock": equilibrium_shock,
    "klinkenberg": klinkenberg,
    "constant_pattern": constant_pattern,
}


if __name__ == "__main__":
    import time

    from fetch_real_mof_data import get_mof303_physics, rh_to_conc

    p = get_mof303_physics()
    T = p.T_in
    c_in = rh_to_conc(0.30, T)
    d = np.load("data/mof303_breakthrough.npz")
    t = d["t"]
    n = len(d["z"])
    truth = d["y"][n - 1] / float(d["c_in"])

    print(f"{'model':<20} {'nRMSE':>9} {'dt50 err (h)':>14} {'wall (ms)':>11}")
    print("-" * 58)
    for name, fn in MODELS.items():
        t0 = time.time()
        pred = fn(p, c_in, T, t)
        ms = (time.time() - t0) * 1e3
        err = np.sqrt(np.mean((pred - truth) ** 2)) / (truth.max() - truth.min())

        def t50(c):
            i = int(np.argmax(c >= 0.5))
            return t[i] if i > 0 else np.nan

        print(f"{name:<20} {err:>9.4f} {(t50(pred) - t50(truth)) / 3600:>14.2f} {ms:>11.3f}")
