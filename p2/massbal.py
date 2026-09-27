"""M1b: recover the uptake q(z,t) from gas-phase concentration alone (observation O2).

The solver's gas balance is
    dc/dt = D_L c_zz - u c_z - S dq/dt,   u = v / eps_t,   S = (1 - eps_t) rho_p / eps_t
so the uptake rate follows from concentration data:
    dq/dt = (D_L c_zz - u c_z - c_t) / S
and q by time integration from a clean bed (q = 0). This is how an experimentalist
with interior probes obtains uptake; it needs no training. Material and flow
constants (eps_t, rho_p, v, D_L) are treated as known -- they are measured, not fitted.

Derivatives: Savitzky-Golay in t (p2.features.derivative); centred finite differences
in z (probe spacing is fixed by the observation model, so no smoothing window in z is
tuned to the answer).
"""
import numpy as np
from scipy.integrate import cumulative_trapezoid

from p2.features import derivative


def invert_uptake(c, z, t, phys, c_in):
    c = np.asarray(c, float)
    z = np.asarray(z, float)
    t = np.asarray(t, float)
    c_t = np.vstack([derivative(row, t) for row in c])
    c_z = np.gradient(c, z, axis=0)
    c_zz = np.gradient(c_z, z, axis=0)
    u = phys.v / phys.eps_t
    S = (1.0 - phys.eps_t) * phys.rho_p / phys.eps_t
    dq_dt = (phys.D_L * c_zz - u * c_z - c_t) / S
    return cumulative_trapezoid(dq_dt, t, axis=1, initial=0.0)
