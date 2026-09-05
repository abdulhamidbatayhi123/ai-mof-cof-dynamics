"""Adsorption equilibrium models — single source of truth for solver and PDE residual.

Both the NumPy path (ground-truth solver) and the Torch path (autograd residuals)
are defined here from the same parameters, so the two can never drift apart.

Type V / cooperative water uptake
---------------------------------
Water in AWH frameworks (MOF-303, MOF-801, CAU-10) does not follow Langmuir.
Uptake is negligible until a threshold relative humidity, then rises almost
vertically as pore filling proceeds cooperatively, then saturates. That step is
the entire reason these materials work at low humidity.

A bare Hill/cooperative form, q = q_max (bc)^n / (1 + (bc)^n), reproduces the
step but is thermodynamically invalid: as c -> 0 it gives q ~ c^n with n > 1,
so dq/dc -> 0 at the origin. Every real isotherm must be LINEAR as c -> 0
(Henry's law). Violating it makes the low-loading limit unphysical and breaks
the link between the isotherm and the Henry constant.

We therefore use a dual-term form **in the spirit of Do & Do (2000)**: a primary-site
term that carries the Henry limit, plus a cooperative cluster term that produces the
step.

Say "in the spirit of", not "the Do--Do form" -- defect B56. Do & Do's published
model superposes an **n-layer BET** primary term with a **Sips** cooperative term
(verified through Buttersack, PCCP 21:5614, 2019, eqns 29-30). Ours superposes a
**single-site Langmuir** primary term with a Sips cooperative term. What we take from
them is the two-term construction and, crucially, the fact that **only the primary
term carries the Henry slope** -- their Sips term, like ours, has slope exactly zero
at the origin. A Langmuir is not an n-layer BET, and a referee who knows the model
will open this equation and see the substitution. Their cluster exponent is also
FIXED (a = 5, m = 6) whereas `isotherm_n` here is a sampled material parameter
spanning 1.01-5.98, which is closer to Do, Junpirom & Do (2009). And "Type V" is our
own IUPAC-grounded label: Buttersack calls this family type IV.

    q*(c,T) = q_max [ f_H * (b_H c)/(1 + b_H c)
                    + (1 - f_H) * (b_C c)^n / (1 + (b_C c)^n) ]

    b_H(T) = b_H0 exp(-dH/(R T))        primary sites
    b_C(T) = b_C0 exp(-dH/(R T))        cluster / pore-filling

As c -> 0:  q* -> q_max f_H b_H c + O(c^n),  so Henry's law holds with
K_H = q_max f_H b_H, while the cluster term still delivers the step at
c ~ 1/b_C. Both affinities carry the same dH, so the isosteric heat is exactly
-dH at every loading and Clausius-Clapeyron is satisfied by construction.

Setting isotherm_n = 1.0 and f_H = 1.0 recovers single-site Langmuir exactly,
which keeps the Type I baseline available for ablation.
"""
from __future__ import annotations

R_GAS = 8.314  # J/mol/K


def _keep(v):
    """Preserve arrays/tensors; coerce plain numbers to float.

    A parametric PINN evaluates a BATCH whose rows have different materials, so
    the isotherm parameters arrive as (N,1) tensors. Forcing them to float would
    silently apply one row's isotherm — or, worse, the batch mean — to every row.
    """
    return v if hasattr(v, "shape") else float(v)


def _params(physics):
    """Pull isotherm parameters off a physics config, with Langmuir defaults.

    Each may be a scalar (single material) or an (N,1) array/tensor (a batch of
    materials); everything downstream broadcasts element-wise either way.
    """
    n = _keep(getattr(physics, "isotherm_n", 1.0))
    default_fH = 1.0 if (not hasattr(n, "shape") and n == 1.0) else 0.08
    f_H = _keep(getattr(physics, "henry_fraction", default_fH))
    b_H0 = _keep(getattr(physics, "b_H0", physics.b0))
    b_C0 = _keep(getattr(physics, "b0"))
    return n, f_H, b_H0, b_C0


def _is_pure_langmuir(n, f_H):
    """True only when BOTH are plain scalars equal to 1 — never for a batch."""
    return (not hasattr(n, "shape") and not hasattr(f_H, "shape")
            and n == 1.0 and f_H == 1.0)


def q_star_np(c, T, physics):
    """Equilibrium loading (mol/kg) for NumPy arrays. Used by the FD solver."""
    import numpy as np

    n, f_H, b_H0, b_C0 = _params(physics)
    kT = np.exp(-physics.delta_H / (R_GAS * T))
    b_H = b_H0 * kT
    b_C = b_C0 * kT

    c_pos = np.clip(c, 0.0, None)  # guard the fractional power against solver undershoot

    henry = (b_H * c_pos) / (1.0 + b_H * c_pos)
    if _is_pure_langmuir(n, f_H):
        return physics.q_max * henry

    bc_n = (b_C * c_pos) ** n
    cluster = bc_n / (1.0 + bc_n)
    return physics.q_max * (f_H * henry + (1.0 - f_H) * cluster)


def q_star_torch(c, T, physics):
    """Equilibrium loading (mol/kg) for Torch tensors. Used by the PDE residual."""
    import torch

    n, f_H, b_H0, b_C0 = _params(physics)
    # The van't Hoff factor exp(-dH/(R T)) is unbounded as T -> 0. A network's
    # raw temperature output is not sign-constrained, so during training T can
    # cross zero and the exponential overflows to inf, which then poisons every
    # downstream gradient. Clamping to a physically impossible-to-exceed band
    # keeps the residual finite while leaving the useful range untouched.
    T_safe = torch.clamp(T, min=150.0, max=800.0)
    kT = torch.exp(-physics.delta_H / (R_GAS * T_safe))
    b_H = b_H0 * kT
    b_C = b_C0 * kT

    # clamp_min keeps the fractional power differentiable and real-valued
    c_pos = torch.clamp(c, min=0.0)

    henry = (b_H * c_pos) / (1.0 + b_H * c_pos)
    if _is_pure_langmuir(n, f_H):
        return physics.q_max * henry

    # add a tiny floor so d/dc of c^n stays finite at c = 0 for n < 1 and
    # so the gradient is well-defined at the origin for n > 1
    bc_n = (b_C * c_pos + 1e-30) ** n
    cluster = bc_n / (1.0 + bc_n)
    return physics.q_max * (f_H * henry + (1.0 - f_H) * cluster)


def henry_constant(T, physics):
    """K_H = dq*/dc as c -> 0  (mol/kg per mol/m3). Finite and positive iff Henry's law holds."""
    import numpy as np

    n, f_H, b_H0, _ = _params(physics)
    b_H = b_H0 * np.exp(-physics.delta_H / (R_GAS * T))
    return physics.q_max * f_H * b_H


def calibrate_step(physics, c_step, T_step, theta_target=0.5):
    """Return the cluster affinity b_C0 that puts the cooperative step at c_step.

    The step centre is where the cluster term reaches half saturation, i.e.
    b_C(T_step) * c_step = 1.
    """
    import numpy as np

    return (1.0 / c_step) / np.exp(-physics.delta_H / (R_GAS * T_step))
