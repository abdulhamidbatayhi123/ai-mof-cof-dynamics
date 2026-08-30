"""L0 — verify the ground-truth solver against closed-form solutions.

Everything downstream inherits this solver's errors, so "high-fidelity ground
truth" has to be a measured claim, not an assertion. Each check below switches
off part of the physics so that an exact analytic solution exists, then compares.

  1. inert tracer         advection + dispersion + Danckwerts BC
                          -> van Genuchten & Alves (1982) third-type solution
                             (NOT Ogata-Banks, which solves the Dirichlet inlet
                             and differs by 3.5% of c0 at Pe ~ 93)
  2. retarded front       equilibrium limit with a linear isotherm
                          -> front velocity u_i / R, R = 1 + (1-e) rho_p K / e
  3. thermal wave         energy equation with adsorption switched off
                          -> wave speed v rho_g Cpg / C_term
  4. LDF kinetics         linear isotherm, no dispersion, isothermal
                          -> Anzelius (1926) / Schumann J-function

Run:  python verify_solver.py
Writes verify_solver.json; validate.py gates on it.
"""
from __future__ import annotations

import copy
import json
import time

import numpy as np
from scipy.special import erfc, erfcx, i0
from scipy.integrate import quad

from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data

RESULTS = {}


def _base(**over):
    p = AdsorptionPhysicsConfig()
    for k, v in over.items():
        setattr(p, k, v)
    return p


def _linear_isotherm(p, K_target):
    """Force a strictly linear isotherm q* = K c by pushing b*c << 1."""
    p.isotherm_n = 1.0
    p.henry_fraction = 1.0
    # q* = q_max b c /(1 + b c) -> q_max b c when b c << 1, so K = q_max * b
    b = K_target / p.q_max
    p.b0 = b / np.exp(-p.delta_H / (8.314 * p.T_w))
    p.b_H0 = p.b0
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 1. inert tracer vs van Genuchten & Alves (third-type / flux inlet)
# ─────────────────────────────────────────────────────────────────────────────

def check_tracer():
    p = _base(k_LDF=0.0, h_w=0.0, L=0.10)
    u = p.v / p.eps_t
    D = p.D_L
    t_end = 0.7 * p.L / u
    N = 4000

    z, t, y = generate_breakthrough_data(
        p, N_z=N, t_final=t_end, c_in=1.0, n_snapshots=60, verbose=False
    )
    num = y[:N, -1]

    # The analytic reference must match OUR inlet boundary condition.
    #
    # Ogata & Banks (1961) solves the FIRST-type (Dirichlet) inlet, c(0,t) = c0.
    # We impose the Danckwerts THIRD-type (flux) condition,
    # v c_in = v c(0+) - D dc/dz|_0+, whose closed form is van Genuchten & Alves
    # (1982), solution A3.
    #
    # The two differ by a "reflection" term that is NOT confined to a thin inlet
    # layer -- at Pe ~ 93 it travels with the front and is worth 3.5% of c0 right
    # at the half-height. Comparing our solver against Ogata-Banks therefore
    # reports a 3.5% error that is entirely an artifact of using the wrong
    # reference, and would have led either to "fixing" a correct solver or to
    # accepting a 3.5% floor that does not exist.
    #
    # erfcx(x) = exp(x^2) erfc(x) keeps exp(u z/D) erfc(a2) stable; the identity
    # u z / D - a2^2 = -a1^2 makes that term exp(-a1^2) erfcx(a2).
    tt = t[-1]
    a1 = (z - u * tt) / (2.0 * np.sqrt(D * tt))
    a2 = (z + u * tt) / (2.0 * np.sqrt(D * tt))
    gauss = np.exp(-(a1**2))

    ana = (
        0.5 * erfc(a1)
        + np.sqrt(u * u * tt / (np.pi * D)) * gauss
        - 0.5 * (1.0 + u * z / D + u * u * tt / D) * gauss * erfcx(a2)
    )
    ana = np.clip(ana, 0.0, 1.0)

    # keep the Dirichlet form as a diagnostic, to quantify the BC difference
    ana_dirichlet = np.clip(0.5 * (erfc(a1) + gauss * erfcx(a2)), 0.0, 1.0)

    diff = np.abs(num - ana)
    err = float(diff.max())
    zf_num = float(np.interp(0.5, num[::-1], z[::-1]))
    zf_ana = u * tt
    RESULTS["tracer_van_genuchten"] = {
        "max_abs_err_vs_third_type": err,
        "z_at_max_err_m": float(z[int(np.argmax(diff))]),
        "max_abs_err_vs_dirichlet": float(np.abs(num - ana_dirichlet).max()),
        "bc_difference_max": float(np.abs(ana - ana_dirichlet).max()),
        "Pe": u * p.L / D,
        "front_num_m": zf_num,
        "front_analytic_m": zf_ana,
        "front_rel_err": abs(zf_num - zf_ana) / zf_ana,
        "N_z": N,
    }
    return err, abs(zf_num - zf_ana) / zf_ana


# ─────────────────────────────────────────────────────────────────────────────
# 2. retarded front velocity, equilibrium limit
# ─────────────────────────────────────────────────────────────────────────────

def check_retardation():
    K = 0.5  # mol/kg per mol/m3
    p = _linear_isotherm(_base(k_LDF=5.0, h_w=0.0, delta_H=-1.0, L=0.10), K)
    u = p.v / p.eps_t
    R = 1.0 + (1 - p.eps_t) * p.rho_p * K / p.eps_t
    u_front = u / R

    t_end = 0.6 * p.L / u_front
    N = 2000
    z, t, y = generate_breakthrough_data(
        p, N_z=N, t_final=t_end, c_in=1.0e-3, n_snapshots=60, verbose=False
    )
    c = y[:N, -1]
    c = c / c.max() if c.max() > 0 else c
    zf_num = float(np.interp(0.5, c[::-1], z[::-1]))
    zf_ana = u_front * t[-1]
    rel = abs(zf_num - zf_ana) / zf_ana
    RESULTS["retarded_front"] = {
        "K": K, "R": R,
        "u_interstitial": u, "u_front_analytic": u_front,
        "front_num_m": zf_num, "front_analytic_m": zf_ana, "rel_err": rel,
        "N_z": N,
    }
    return rel


# ─────────────────────────────────────────────────────────────────────────────
# 3. thermal wave speed, adsorption off
# ─────────────────────────────────────────────────────────────────────────────

def check_thermal_wave():
    p = _base(k_LDF=0.0, h_w=0.0, k_z=1e-6, L=0.10)
    u_T = p.v * p.rho_g * p.C_pg / p.C_term
    t_end = 0.6 * p.L / u_T
    N = 2000
    z, t, y = generate_breakthrough_data(
        p, N_z=N, t_final=t_end, c_in=0.0, T_in=p.T_w + 20.0, n_snapshots=60, verbose=False
    )
    T = y[2 * N :, -1]
    theta = (T - p.T_w) / 20.0
    if theta.max() < 0.4:
        return float("nan")
    zf_num = float(np.interp(0.5, theta[::-1], z[::-1]))
    zf_ana = u_T * t[-1]
    rel = abs(zf_num - zf_ana) / zf_ana
    RESULTS["thermal_wave"] = {
        "u_thermal_analytic": u_T, "front_num_m": zf_num,
        "front_analytic_m": zf_ana, "rel_err": rel, "N_z": N,
    }
    return rel


# ─────────────────────────────────────────────────────────────────────────────
# 4. LDF kinetics vs the Anzelius / Schumann J-function
# ─────────────────────────────────────────────────────────────────────────────

def _J(xi, tau):
    """J(xi,tau) = 1 - exp(-tau) * int_0^xi exp(-s) I0(2 sqrt(s tau)) ds."""
    if tau <= 0:
        return 0.0
    def integrand(s):
        return np.exp(-s + np.log(i0(2.0 * np.sqrt(s * tau))) if i0(2.0 * np.sqrt(s * tau)) > 0 else -np.inf)
    val, _ = quad(lambda s: np.exp(-s) * i0(2.0 * np.sqrt(s * tau)), 0.0, xi, limit=200)
    return float(1.0 - np.exp(-tau) * val)


def check_ldf_analytic():
    K = 0.5
    p = _linear_isotherm(_base(k_LDF=0.02, h_w=0.0, delta_H=-1.0, L=0.10, D_L=1e-9), K)
    u = p.v / p.eps_t
    N = 2000
    R_cap = (1 - p.eps_t) * p.rho_p * K / p.eps_t
    t_end = 3.0 * p.L * R_cap / u

    z, t, y = generate_breakthrough_data(
        p, N_z=N, t_final=t_end, c_in=1.0e-3, n_snapshots=200, verbose=False
    )
    c_exit = y[N - 1, :] / 1.0e-3

    z_end = p.L
    xi = p.k_LDF * R_cap * z_end / u
    errs = []
    for k in range(len(t)):
        tau = p.k_LDF * (t[k] - z_end / u)
        if tau <= 0:
            continue
        errs.append(abs(c_exit[k] - _J(xi, tau)))
    err = float(np.max(errs)) if errs else float("nan")
    RESULTS["ldf_anzelius_schumann"] = {
        "xi": xi, "max_abs_err": err, "n_points": len(errs), "N_z": N,
    }
    return err


def main():
    t0 = time.time()
    print("L0 — solver verification against closed-form solutions")
    print("=" * 70)

    e_prof, e_front = check_tracer()
    print(f"  1. inert tracer vs van Genuchten (third-type BC)")
    print(f"       max |c_num - c_analytic|   = {e_prof:.4e}")
    print(f"       front position rel. error  = {100 * e_front:.4f} %")

    e_ret = check_retardation()
    r = RESULTS["retarded_front"]
    print(f"  2. retarded front, linear isotherm (R = {r['R']:.1f})")
    print(f"       u_front  {r['front_num_m'] / 1:.6f} m vs {r['front_analytic_m']:.6f} m")
    print(f"       rel. error                 = {100 * e_ret:.4f} %")

    e_th = check_thermal_wave()
    tw = RESULTS.get("thermal_wave", {})
    print(f"  3. thermal wave, adsorption off")
    print(f"       u_thermal = {tw.get('u_thermal_analytic', float('nan')):.6g} m/s")
    print(f"       rel. error                 = {100 * e_th:.4f} %")

    e_ldf = check_ldf_analytic()
    print(f"  4. LDF kinetics vs Anzelius-Schumann J-function")
    print(f"       xi = {RESULTS['ldf_anzelius_schumann']['xi']:.3f}")
    print(f"       max |c/c0 - J(xi,tau)|     = {e_ldf:.4e}")

    RESULTS["_meta"] = {"elapsed_s": time.time() - t0}
    with open("verify_solver.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    print("=" * 70)
    print(f"Wrote verify_solver.json  [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
