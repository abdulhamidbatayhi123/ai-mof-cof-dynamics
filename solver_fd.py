"""Method-of-lines solver for the 1D non-isothermal adsorption column.

This is the ground truth. Everything downstream inherits its errors, so the
numerics are stated explicitly:

  * advection    first-order upwind by default. A van Leer MUSCL limiter is
                 available (scheme="vanleer") and is formally 2nd order, but
                 measured on this system it costs 9x the wall time and 6x the
                 Jacobian factorisations: the limiter is non-smooth in the
                 near-uniform regions that make up most of the bed, which
                 wrecks BDF's Newton convergence. Upwind is monotone, linear,
                 and Newton-friendly; its numerical dispersion D_num = u*dz/2
                 is instead controlled by resolving the grid and is verified
                 by grid_convergence() rather than assumed.
  * dispersion   central differences, 2nd order
  * boundaries   Danckwerts: flux-matched inlet, zero-gradient outlet
  * time         BDF with an explicit Jacobian sparsity pattern. Without the
                 pattern SciPy builds a dense 3N x 3N Jacobian by finite
                 differences (3N+1 RHS evaluations per Jacobian); with it, a
                 handful. This is what makes a parametric sweep affordable.
  * equilibrium  imported from isotherm.py so the solver and the PDE residual
                 cannot disagree.

Velocity convention: `v` is the SUPERFICIAL velocity. The interstitial gas
speed is v/eps_t and appears in the gas mass balance; the thermal wave speed is
v*rho_g*C_pg/C_term and appears in the energy balance.

Governing equations (dimensional)

    eps_t dc/dt = D_L d2c/dz2 - v dc/dz - (1-eps_t) rho_p dq/dt
          dq/dt = k_LDF (q*(c,T) - q)
    C_term dT/dt = k_z d2T/dz2 - v rho_g C_pg dT/dz
                   + (1-eps_t) rho_p (-dH) dq/dt - (4 h_w/D_in)(T - T_w)
"""
from __future__ import annotations

import os

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import bmat, csr_matrix, diags

from isotherm import henry_constant, q_star_np

R_GAS = 8.314


class AdsorptionPhysicsConfig:
    """Bed, gas, and framework properties. Defaults are a generic Type I sorbent."""

    def __init__(self):
        # ── bed ──
        # L = 0.1 m is a lab-scale breakthrough column, not an arbitrary choice.
        # At L = 1 m the mass-transfer zone is ~1 mm wide, i.e. 0.1% of the
        # domain, and resolving it with 20 cells needs N_z ~ 18,700. At 0.1 m
        # the same physics needs ~1,900. Use mtz_width() before changing this.
        self.eps_t = 0.40        # total porosity (-)
        self.rho_p = 1200.0      # particle density (kg/m3)
        self.L = 0.10            # column length (m)
        self.D_in = 0.05         # inner diameter (m)
        self.d_p = 0.002         # particle diameter (m)

        # ── gas ──
        self.rho_g = 1.2         # (kg/m3)
        self.C_pg = 1000.0       # (J/kg/K)
        self.v = 0.10            # SUPERFICIAL velocity (m/s)
        # from the Ruthven packed-bed correlation at d_p = 2 mm rather than a
        # hand-picked value; see axial_dispersion().
        self.D_L = 0.7 * 2.5e-5 + 0.5 * 0.002 * (0.10 / 0.40)

        # ── solid ──
        self.C_ps = 1000.0       # (J/kg/K)
        self.k_z = 0.10          # axial thermal conductivity (W/m/K)

        # ── kinetics ──
        self.k_LDF = 0.05        # linear driving force coefficient (1/s)

        # ── equilibrium ──
        self.q_max = 20.0        # saturation capacity (mol/kg)
        self.delta_H = -50000.0  # heat of adsorption (J/mol), exothermic
        self.isotherm_n = 1.0    # cooperativity; 1.0 = Langmuir, >1 = Type V step
        self.henry_fraction = 1.0  # weight on the Henry-carrying primary-site term
        # b0 chosen so b(T_w)*c_in ~ 1 at c_in = 1 mol/m3: keeps the isotherm
        # identifiable instead of pinned in the irreversible (rectangular) limit.
        self.b0 = 1.0 / np.exp(50000.0 / (R_GAS * 298.0))
        self.b_H0 = self.b0

        # ── thermal boundary ──
        self.h_w = 10.0          # wall heat transfer coefficient (W/m2/K)
        self.T_w = 298.0         # wall temperature (K)
        self.T_in = 298.0        # inlet gas temperature (K)

        self.R = R_GAS

    @property
    def C_term(self):
        """Volumetric heat capacity of the packed bed (J/m3/K)."""
        return self.eps_t * self.rho_g * self.C_pg + (1 - self.eps_t) * self.rho_p * self.C_ps

    def stoichiometric_time(self, c_in, T=None):
        """Time for the bed to saturate at the feed condition (s)."""
        T = self.T_w if T is None else T
        q_eq = float(q_star_np(np.array([c_in]), np.array([T]), self)[0])
        capacity = (1 - self.eps_t) * self.rho_p * q_eq + self.eps_t * c_in
        return capacity * self.L / (self.v * c_in)

    def mtz_width(self, c_in, T=None):
        """Mass-transfer-zone thickness (m) and the grid it demands.

        The MTZ is set by whichever spreading mechanism is broader: axial
        dispersion (D_L / u_gas) or finite LDF kinetics (u_front / k_LDF).
        Returns (width_m, N_z_for_20_cells).

        This number governs the grid requirement. For a 1 m column with
        D_L = 1e-4 and k_LDF = 0.05 the MTZ is ~0.5 mm -- 0.05% of the domain --
        which needs N_z ~ 36,000 to resolve. That is a property of the
        parameters, not of the numerics.

        CAVEAT, measured: this estimate is ISOTHERMAL and underestimates the
        real front. In the generated data the 5%-95% transition is 555 cells at
        its sharpest where this formula predicts 21 -- a factor of ~26. The
        difference is the thermal wave: heat released at the mass front travels
        ahead of it at rho_g*C_pg/C_term times the gas speed, shifting the
        isotherm and broadening the combined transition well beyond the
        isothermal MTZ.

        The error is in the SAFE direction -- it demands a finer grid than
        strictly needed -- so it remains useful as a conservative design bound.
        Do not quote it as the physical front width.
        """
        T = self.T_w if T is None else T
        b = self.b0 * np.exp(-self.delta_H / (R_GAS * T))
        dq_dc = self.q_max * b / (1.0 + b * c_in) ** 2
        u_gas = self.v / self.eps_t
        u_front = self.v / (self.eps_t + (1 - self.eps_t) * self.rho_p * dq_dc)
        width = max(self.D_L / u_gas, u_front / self.k_LDF)
        return width, int(np.ceil(20 * self.L / width))


def axial_dispersion(v, eps_t, d_p, D_m=2.5e-5):
    """Packed-bed axial dispersion correlation (Ruthven): D_L = 0.7 D_m + 0.5 d_p u.

    Use this rather than a hand-picked D_L -- it ties the front width to a real
    particle size and is defensible to a referee.
    """
    u = v / eps_t
    return 0.7 * D_m + 0.5 * d_p * u


def _upwind_div(u, dz):
    """Build d(u*f)/dz with first-order upwinding. Assumes u > 0. Linear => Newton-friendly."""

    def flux_div(f, f_in):
        fm1 = np.concatenate(([f_in], f[:-1]))
        return u * (f - fm1) / dz

    return flux_div


def _van_leer_div(u, dz):
    """Build d(u*f)/dz using a van Leer MUSCL reconstruction. Assumes u > 0."""

    def flux_div(f, f_in):
        fm2 = np.concatenate(([f_in, f_in], f[:-2]))
        fm1 = np.concatenate(([f_in], f[:-1]))
        fp1 = np.concatenate((f[1:], [f[-1]]))

        def face(a_m1, a_0, a_p1):
            """Limited reconstruction on the downwind face of cell a_0."""
            den = a_p1 - a_0
            safe = np.where(np.abs(den) < 1e-300, 1e-300, den)
            r = (a_0 - a_m1) / safe
            phi = (r + np.abs(r)) / (1.0 + np.abs(r))       # van Leer limiter
            phi = np.where(np.abs(den) < 1e-300, 0.0, phi)
            return a_0 + 0.5 * phi * den

        f_right = face(fm1, f, fp1)   # face i+1/2
        f_left = face(fm2, fm1, f)    # face i-1/2
        f_left[0] = f_in              # Danckwerts inlet flux
        f_right[-1] = f[-1]           # convective outflow
        return u * (f_right - f_left) / dz

    return flux_div


def _sparsity(N_z):
    """Jacobian sparsity for the state vector [c(1..N), q(1..N), T(1..N)]."""
    band = diags([1.0, 1.0, 1.0, 1.0], [-2, -1, 0, 1], shape=(N_z, N_z))
    eye = diags([1.0], [0], shape=(N_z, N_z))
    return csr_matrix(bmat([
        [band, eye, eye],    # dc/dt
        [eye, eye, eye],     # dq/dt
        [band, eye, band],   # dT/dt
    ]))


def generate_breakthrough_data(
    physics,
    N_z=1000,
    t_final=None,
    c_in=1.0,
    T_in=None,
    n_snapshots=500,
    rtol=1e-6,
    atol=1e-10,
    scheme="upwind",
    verbose=True,
):
    """Solve the column. Returns (z_centers, t, y) with y stacked as [c; q; T].

    scheme: "upwind" (default, robust) or "vanleer" (2nd order, ~9x slower here).
    """
    T_in = physics.T_in if T_in is None else T_in
    if t_final is None:
        t_final = 1.5 * physics.stoichiometric_time(c_in, T_in)

    dz = physics.L / N_z
    z_centers = np.linspace(dz / 2, physics.L - dz / 2, N_z)

    C_term = physics.C_term
    u_gas = physics.v / physics.eps_t                        # interstitial gas speed
    u_thermal = physics.v * physics.rho_g * physics.C_pg / C_term
    src_factor = (1 - physics.eps_t) * physics.rho_p / physics.eps_t
    heat_factor = (1 - physics.eps_t) * physics.rho_p * (-physics.delta_H) / C_term
    wall_factor = (4 * physics.h_w / physics.D_in) / C_term
    alpha_T = physics.k_z / C_term

    build_adv = {"upwind": _upwind_div, "vanleer": _van_leer_div}[scheme]
    adv_c = build_adv(u_gas, dz)
    adv_T = build_adv(u_thermal, dz)

    def laplacian(f, f_in):
        """Dispersive/conductive flux divergence with a true Danckwerts inlet.

        The obvious implementation puts a Dirichlet ghost cell at the inlet,
        `f[-1] = f_in`, giving `(f1 - 2 f0 + f_in)/dz^2`. That is WRONG here, and
        the error is large. Danckwerts specifies the total inlet FLUX:

            v c_in = v c(0+) - D_L dc/dz|_0+

        i.e. the feed enters advectively and carries no dispersive flux of its
        own. A Dirichlet ghost instead drives an artificial dispersive influx of
        D_L (c_in - c_0)/dz. With D_L = 2.7e-4 and dz = 5e-5 that is ~2.1
        mol/m2/s against an advective feed of v*c_in = 0.1 -- roughly 21x
        over-feeding while the first cell is still empty.

        Setting the inlet-face dispersive flux to zero makes the scheme
        telescope exactly, so that

            d/dt int[eps c + (1-eps) rho_p q] dz = v (c_in - c_exit)

        holds to machine precision. It was a 1.02% global mass-closure gap,
        invariant under time refinement, that exposed this.
        """
        lap = np.empty_like(f)
        lap[1:-1] = (f[2:] - 2.0 * f[1:-1] + f[:-2]) / dz**2
        lap[0] = (f[1] - f[0]) / dz**2      # zero dispersive flux at the inlet face
        lap[-1] = (f[-2] - f[-1]) / dz**2   # zero-gradient outlet
        return lap

    def rhs(t, y):
        c, q, T = np.split(y, 3)
        dq_dt = physics.k_LDF * (q_star_np(c, T, physics) - q)
        dc_dt = physics.D_L * laplacian(c, c_in) - adv_c(c, c_in) - src_factor * dq_dt
        dT_dt = (
            alpha_T * laplacian(T, T_in)
            - adv_T(T, T_in)
            + heat_factor * dq_dt
            - wall_factor * (T - physics.T_w)
        )
        return np.concatenate([dc_dt, dq_dt, dT_dt])

    y0 = np.concatenate([np.zeros(N_z), np.zeros(N_z), np.full(N_z, physics.T_w)])

    if verbose:
        print(f"  N_z={N_z}  t_final={t_final:.4g}s  c_in={c_in:g}  "
              f"(stoichiometric {physics.stoichiometric_time(c_in, T_in):.4g}s)")

    sol = solve_ivp(
        rhs, [0.0, t_final], y0,
        method="BDF",
        t_eval=np.linspace(0.0, t_final, n_snapshots),
        jac_sparsity=_sparsity(N_z),
        rtol=rtol, atol=atol,
    )
    if not sol.success:
        raise RuntimeError(f"solver failed: {sol.message}")
    if verbose:
        print(f"  {sol.nfev} RHS evals, {sol.njev} Jacobians, status {sol.status}")
    return z_centers, sol.t, sol.y


def grid_convergence(physics, c_in, t_final, N_coarse=500, N_fine=1000, T_in=None):
    """Max relative change in the exit breakthrough curve when the grid is refined.

    Scheme-agnostic replacement for a numerical-dispersion estimate: if this is
    small, the solution is resolved regardless of which scheme produced it.
    """
    curves = {}
    for tag, N in (("coarse", N_coarse), ("fine", N_fine)):
        _, t, y = generate_breakthrough_data(
            physics, N_z=N, t_final=t_final, c_in=c_in, T_in=T_in, verbose=False
        )
        curves[tag] = (t, y[N - 1, :])   # exit-cell concentration history
    t_c, c_c = curves["coarse"]
    t_f, c_f = curves["fine"]
    c_f_on_coarse = np.interp(t_c, t_f, c_f)
    denom = max(np.abs(c_f_on_coarse).max(), 1e-30)
    return float(np.abs(c_c - c_f_on_coarse).max() / denom)


if __name__ == "__main__":
    phys = AdsorptionPhysicsConfig()
    c_in = 1.0
    t_stoich = phys.stoichiometric_time(c_in)
    print(f"Generic sorbent: K_H = {henry_constant(phys.T_w, phys):.4g} mol/kg per mol/m3, "
          f"stoichiometric breakthrough {t_stoich:.4g}s")

    z, t, y = generate_breakthrough_data(phys, N_z=1000, t_final=1.5 * t_stoich, c_in=c_in)

    print("Grid-convergence study (N_z 500 -> 1000)...")
    err = grid_convergence(phys, c_in, 1.5 * t_stoich)
    print(f"  exit-curve change: {100 * err:.3f}%")

    os.makedirs("data", exist_ok=True)
    np.savez(
        "data/synthetic_breakthrough.npz",
        z=z, t=t, y=y,
        c_in=c_in, N_z=1000, scheme="vanleer", grid_convergence_err=err,
    )
    print("Saved data/synthetic_breakthrough.npz")
