"""The column of solver_fd.py, re-expressed in JAX so a rate law can be LEARNED through
it (paper 2's M1, observation models O2/O3).

Same discretisation as solver_fd.generate_breakthrough_data with scheme="upwind":
first-order upwind advection with the feed as the inlet ghost value, a dispersion /
conduction Laplacian with ZERO dispersive flux at the inlet face (the Danckwerts
treatment that closed B8's 1.02 % mass gap) and zero gradient at the outlet, LDF
uptake, and the heat balance with adsorption heat and wall loss. The only change is
the uptake rate, which is a function argument:

    rate(c, q, T, qstar) -> dq/dt

so the known LDF (for verification) and a neural network (M1) run through identical
code. Verified against solver_fd on the same grid before any timing is trusted.
"""
import jax
import jax.numpy as jnp
import numpy as np
import diffrax

from isotherm import R_GAS, _params

jax.config.update("jax_enable_x64", True)


def make_qstar(phys):
    n, f_H, b_H0, b_C0 = (float(np.asarray(v)) for v in _params(phys))
    q_max, dH = float(phys.q_max), float(phys.delta_H)
    pure = (n == 1.0 and f_H == 1.0)

    def qstar(c, T):
        kT = jnp.exp(-dH / (R_GAS * T))
        cp = jnp.clip(c, 0.0, None)
        henry = (b_H0 * kT * cp) / (1.0 + b_H0 * kT * cp)
        if pure:
            return q_max * henry
        bcn = (b_C0 * kT * cp) ** n
        return q_max * (f_H * henry + (1.0 - f_H) * bcn / (1.0 + bcn))
    return qstar


def make_rhs(phys, n_z, c_in, rate):
    dz = phys.L / n_z
    C_term = phys.C_term
    u_gas = phys.v / phys.eps_t
    u_th = phys.v * phys.rho_g * phys.C_pg / C_term
    src = (1 - phys.eps_t) * phys.rho_p / phys.eps_t
    heat = (1 - phys.eps_t) * phys.rho_p * (-phys.delta_H) / C_term
    wall = (4 * phys.h_w / phys.D_in) / C_term
    alpha_T = phys.k_z / C_term
    T_in, T_w, D_L = phys.T_in, phys.T_w, phys.D_L
    qstar = make_qstar(phys)

    def lap(f):
        inner = (f[2:] - 2.0 * f[1:-1] + f[:-2]) / dz ** 2
        return jnp.concatenate([((f[1] - f[0]) / dz ** 2)[None], inner,
                                ((f[-2] - f[-1]) / dz ** 2)[None]])

    def adv(f, f_in, u):
        return u * (f - jnp.concatenate([jnp.array([f_in]), f[:-1]])) / dz

    def rhs(t, y, args):
        c, q, T = y[:n_z], y[n_z:2 * n_z], y[2 * n_z:]
        dq = rate(c, q, T, qstar(c, T), args)
        dc = D_L * lap(c) - adv(c, c_in, u_gas) - src * dq
        dT = alpha_T * lap(T) - adv(T, T_in, u_th) + heat * dq - wall * (T - T_w)
        return jnp.concatenate([dc, dq, dT])
    return rhs


def ldf_rate(c, q, T, qs, args):
    return args["k"] * (qs - q)


def solve(phys, n_z, c_in, t_final, ts, rate=ldf_rate, args=None, rtol=1e-6, atol=1e-9):
    rhs = make_rhs(phys, n_z, c_in, rate)
    y0 = jnp.concatenate([jnp.zeros(n_z), jnp.zeros(n_z), jnp.full(n_z, phys.T_w)])
    sol = diffrax.diffeqsolve(
        diffrax.ODETerm(rhs), diffrax.Kvaerno5(), t0=0.0, t1=t_final, dt0=1e-3, y0=y0,
        args=args if args is not None else {"k": phys.k_LDF},
        saveat=diffrax.SaveAt(ts=jnp.asarray(ts)),
        stepsize_controller=diffrax.PIDController(rtol=rtol, atol=atol),
        max_steps=200_000)
    return sol.ys   # (n_t, 3 n_z)
