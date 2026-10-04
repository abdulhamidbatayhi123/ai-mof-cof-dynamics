"""PDE residuals for 1D non-isothermal adsorption, in dimensionless form.

Each equation is divided by its OWN dominant term, so all three residuals are
O(1) at initialisation and no loss weight has to repair a scale error. This is
the fix for the 4.5e10 : 0.38 : 1.0e6 imbalance the earlier version produced.

Dimensionless groups
--------------------
    Pe     = v L / D_L                       axial Peclet
    Da     = k_LDF t_ref                     Damkohler (kinetics vs convection)
    Lambda = (1-eps) rho_p q_ref / (eps c_ref)   solid/gas capacity ratio
    beta   = (1-eps) rho_p (-dH) q_ref / (C_term T_ref)   adiabatic rise
    St     = 4 h_w L / (D_in C_term v)       wall Stanton
    Pe_T   = C_term v L / k_z                thermal Peclet
    tau    = t_final / t_ref                 horizon in convective units

Lambda is the group that matters. For the default column it is ~3.6e4: the gas
holds four orders of magnitude less adsorbate than the solid, so gas-phase
accumulation is negligible and the system sits in the local-equilibrium
(frozen-gas) limit with 1/Lambda as the small parameter. Rather than fight that,
each residual below is normalised so the surviving dominant balance is O(1).

Scaling of each equation
------------------------
    gas mass    divided by the adsorption sink      -> sink coefficient 1
    kinetics    divided by (tau * Da)               -> driving force (q*-q), O(1)
    energy      divided by thermal accumulation     -> dT*/dt* coefficient 1

The isotherm is imported from isotherm.py, the same definition the ground-truth
solver uses, so the residual and the data can never disagree.
"""
from __future__ import annotations

import torch

from isotherm import q_star_torch


class NondimConfig:
    """Reference scales tying the network's [0,1] inputs to physical units.

    The network sees z* = z/L and t* = t/t_final, both in [0,1]. t_final must be
    supplied explicitly: it is a property of the dataset, not of the material.
    """

    def __init__(self, physics, t_final, c_in=1.0):
        self.L_ref = physics.L
        self.t_final = float(t_final)
        self.t_ref = physics.L / physics.v          # convective timescale
        self.c_ref = float(c_in)
        self.q_ref = physics.q_max
        self.T_ref = physics.T_in

    @property
    def tau(self):
        return self.t_final / self.t_ref

    def groups(self, physics):
        """Return the dimensionless groups as a plain dict (for logging/reporting)."""
        eps = physics.eps_t
        return {
            "Pe": physics.v * physics.L / physics.D_L,
            "Da": physics.k_LDF * self.t_ref,
            "Lambda": (1 - eps) * physics.rho_p * self.q_ref / (eps * self.c_ref),
            "beta": (1 - eps) * physics.rho_p * (-physics.delta_H) * self.q_ref
            / (physics.C_term * self.T_ref),
            "St": 4 * physics.h_w * physics.L / (physics.D_in * physics.C_term * physics.v),
            "Pe_T": physics.C_term * physics.v * physics.L / physics.k_z,
            "tau": self.tau,
        }


def term_coefficients(nondim, physics):
    """Coefficient of every term in every residual, before normalisation.

    These are pure functions of the dimensionless groups -- they do not depend on
    the network's weights. That makes them the right thing to test: measuring
    "residual magnitude on a randomly initialised network" conflates equation
    scaling with initialisation scale and will flag a correctly nondimensionalised
    system as broken.

    Returns {equation: {term: coefficient}}.
    """
    g = nondim.groups(physics)
    Pe, Da, Lam = g["Pe"], g["Da"], g["Lambda"]
    beta, St, Pe_T, tau = g["beta"], g["St"], g["Pe_T"], g["tau"]
    v_T = physics.rho_g * physics.C_pg / physics.C_term

    return {
        "mass_gas": {        # B72: gas at the interstitial speed v/eps_t
            "dc/dt": 1.0 / Lam,
            "dc/dz": tau / (physics.eps_t * Lam),
            "d2c/dz2": tau / (Pe * Lam),
            "dq/dt": 1.0,
        },
        "kinetics": {
            "dq/dt": 1.0 / (tau * Da),
            "q*-q": 1.0,
        },
        "energy": {
            "dT/dt": 1.0,
            "dT/dz": tau * v_T,
            "d2T/dz2": tau / Pe_T,
            "dq/dt": beta,
            "wall": tau * St,
        },
    }


def _normalisers(nondim, physics):
    """Per-equation divisor: the magnitude of that equation's dominant term."""
    coeffs = term_coefficients(nondim, physics)
    return {eq: max(abs(v) for v in terms.values()) for eq, terms in coeffs.items()}


def compute_adsorption_pde_residuals(model, z_s, t_s, nondim, physics):
    """Return (res_mass_gas, res_kinetics, res_energy), each O(1) by construction."""
    z_s = z_s.requires_grad_(True)
    t_s = t_s.requires_grad_(True)

    out = model(z_s, t_s)
    c_s, q_s, T_s = out[:, 0:1], out[:, 1:2], out[:, 2:3]
    ones = torch.ones_like(z_s)

    def d(y, x):
        return torch.autograd.grad(y, x, ones, create_graph=True)[0]

    dcs_dzs, dcs_dts = d(c_s, z_s), d(c_s, t_s)
    dqs_dts = d(q_s, t_s)
    dTs_dzs, dTs_dts = d(T_s, z_s), d(T_s, t_s)
    d2cs_dzs2 = d(dcs_dzs, z_s)
    d2Ts_dzs2 = d(dTs_dzs, z_s)

    g = nondim.groups(physics)
    Pe, Da, Lam = g["Pe"], g["Da"], g["Lambda"]
    beta, St, Pe_T, tau = g["beta"], g["St"], g["Pe_T"], g["tau"]
    v_T = physics.rho_g * physics.C_pg / physics.C_term   # thermal-wave speed ratio

    # equilibrium loading, from the shared definition, in scaled units
    T_dim = nondim.T_ref * T_s
    c_dim = nondim.c_ref * c_s
    q_star_s = q_star_torch(c_dim, T_dim, physics) / nondim.q_ref

    # ── gas mass balance, normalised by the adsorption sink ──
    #   (1/Lam) dc*/dt* + (tau/(eps Lam)) dc*/dz* - (tau/(Pe Lam)) d2c*/dz*2 + dq*/dt* = 0
    # B72 (2026-10-04): the eps_t was missing, i.e. gas moved at v instead of v/eps_t.
    eps = physics.eps_t
    res_mass_g = (
        (1.0 / Lam) * dcs_dts
        + (tau / (eps * Lam)) * dcs_dzs
        - (tau / (Pe * Lam)) * d2cs_dzs2
        + dqs_dts
    )

    # ── kinetics, normalised by the driving-force term ──
    #   (1/(tau Da)) dq*/dt* - (q*_eq - q*) = 0
    res_kinetics = (1.0 / (tau * Da)) * dqs_dts - (q_star_s - q_s)

    # ── energy, normalised by thermal accumulation ──
    T_w_s = physics.T_w / nondim.T_ref
    res_energy = (
        dTs_dts
        + tau * v_T * dTs_dzs
        - (tau / Pe_T) * d2Ts_dzs2
        - beta * dqs_dts
        + tau * St * (T_s - T_w_s)
    )

    # Divide each equation by its own dominant-term coefficient, so that all
    # three residuals carry the same weight before any adaptive scheme is applied.
    nrm = _normalisers(nondim, physics)
    return (
        res_mass_g / nrm["mass_gas"],
        res_kinetics / nrm["kinetics"],
        res_energy / nrm["energy"],
    )


def boundary_residuals(model, t_s, nondim, physics):
    """Danckwerts inlet and zero-gradient outlet, as residuals.

    The previous training script imposed no boundary condition at all, which
    leaves the problem ill-posed regardless of how well the interior residual
    is minimised.
    """
    t_s = t_s.requires_grad_(True)
    z0 = torch.zeros_like(t_s, requires_grad=True)
    z1 = torch.ones_like(t_s, requires_grad=True)

    ones = torch.ones_like(t_s)
    Pe = nondim.groups(physics)["Pe"]

    out0 = model(z0, t_s)
    c0, T0 = out0[:, 0:1], out0[:, 2:3]
    dc0 = torch.autograd.grad(c0, z0, ones, create_graph=True)[0]
    dT0 = torch.autograd.grad(T0, z0, ones, create_graph=True)[0]

    # inlet: c* - (eps/Pe) dc*/dz* = 1   (flux matching at v/eps_t; B72, was 1/Pe)
    res_in_c = c0 - (physics.eps_t / Pe) * dc0 - 1.0
    # heat inlet is flux-type in the solver too (B72): T* - dT*/dz*/(Pe_T v_T) = T_in/T_ref
    g = nondim.groups(physics)
    v_T = physics.rho_g * physics.C_pg / physics.C_term
    res_in_T = T0 - dT0 / (g["Pe_T"] * v_T) - physics.T_in / nondim.T_ref

    out1 = model(z1, t_s)
    c1, T1 = out1[:, 0:1], out1[:, 2:3]
    dc1 = torch.autograd.grad(c1, z1, ones, create_graph=True)[0]
    dT1 = torch.autograd.grad(T1, z1, ones, create_graph=True)[0]

    return res_in_c, res_in_T, dc1, dT1
