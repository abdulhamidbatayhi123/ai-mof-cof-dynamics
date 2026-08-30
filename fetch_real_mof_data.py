"""MOF-303 water-harvesting benchmark case.

MOF-303 (Al(OH)(PZDC), Yaghi group) is the reference framework for atmospheric
water harvesting from low-humidity air. Its defining feature is a **Type V**
water isotherm: near-zero uptake until a threshold relative humidity, then a
near-vertical cooperative pore-filling step, then saturation. That step is the
entire reason the material works -- it delivers a large working capacity across
a narrow humidity swing and regenerates at low temperature.

A single-site Langmuir isotherm cannot represent this. It is strictly concave
with no inflection point, so it predicts the largest uptake gradient at the
*lowest* humidity, which is the opposite of the real behaviour and inverts both
the working-capacity and the regeneration-energy conclusions.

We use the dual-term Do--Do form from isotherm.py: a Langmuir primary-site term
carrying the Henry limit, plus a cooperative cluster term producing the step.

Parameter provenance
--------------------
    q_max   25 mol/kg (~0.45 g/g)   representative MOF-303 saturation uptake
    dH      -50 kJ/mol              water isosteric heat, MOF-303 range
    step    ~15 % RH at 298 K       cooperative pore-filling threshold
    n       4.0                     cooperativity; controls step sharpness
    f_H     0.06                    primary-site fraction (sets the Henry slope)
    rho_p   1100 kg/m3              packed particle density
    k_LDF   0.01 1/s                slow intracrystalline diffusion

  !! These are representative literature-range values, NOT digitised from a
  !! specific paper. Before submission every one must be replaced with a cited
  !! value, and the isotherm refitted to a published MOF-303 water isotherm.
  !! Tracked as an open item in the ladder protocol.
"""
from __future__ import annotations

import os

import numpy as np

from isotherm import calibrate_step, henry_constant, q_star_np
from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data, grid_convergence

R_GAS = 8.314


def p_sat_water(T):
    """Saturation vapour pressure of water (Pa), Tetens/Magnus form. T in K."""
    Tc = T - 273.15
    return 610.94 * np.exp(17.625 * Tc / (Tc + 243.04))


def rh_to_conc(rh, T):
    """Relative humidity (0-1) -> molar concentration (mol/m3) via the ideal gas law."""
    return rh * p_sat_water(T) / (R_GAS * T)


def get_mof303_physics():
    phys = AdsorptionPhysicsConfig()

    # ── framework ──
    phys.rho_p = 1100.0
    phys.eps_t = 0.35
    phys.q_max = 25.0
    phys.delta_H = -50000.0

    # ── Type V cooperative isotherm ──
    phys.isotherm_n = 4.0          # step sharpness
    phys.henry_fraction = 0.06     # primary-site weight; carries Henry's law
    T_ref = 298.15
    c_step = rh_to_conc(0.15, T_ref)          # step centred at 15 % RH
    phys.b0 = calibrate_step(phys, c_step, T_ref)     # cluster affinity
    phys.b_H0 = phys.b0 / 20.0                # weaker primary sites

    # ── kinetics ──
    phys.k_LDF = 0.01

    # ── column / operating point ──
    phys.L = 0.10
    phys.v = 0.10
    phys.d_p = 0.002
    phys.D_L = 0.7 * 2.5e-5 + 0.5 * phys.d_p * (phys.v / phys.eps_t)
    phys.T_in = 303.15             # 30 C ambient
    phys.T_w = 303.15

    return phys


def report(phys, c_in, T):
    """Print the isotherm diagnostics that decide whether this case is well posed."""
    rh = np.linspace(0.001, 0.95, 4000)
    c = rh_to_conc(rh, T)
    q = q_star_np(c, np.full_like(c, T), phys)
    d2 = np.gradient(np.gradient(q, c), c)
    flips = int(np.sum(np.diff(np.sign(d2[5:-5])) != 0))
    step_rh = rh[int(np.argmax(np.gradient(q, rh)))]
    w, N = phys.mtz_width(c_in, T)

    print(f"  T = {T:.2f} K,  p_sat = {p_sat_water(T):.1f} Pa")
    print(f"  Henry constant K_H       = {henry_constant(T, phys):.4g} mol/kg per mol/m3")
    print(f"  inflection points        = {flips}   (Type V requires >= 1)")
    print(f"  steepest uptake at RH    = {100 * step_rh:.1f} %")
    for r in (0.05, 0.10, 0.15, 0.20, 0.30, 0.60):
        qq = float(q_star_np(np.array([rh_to_conc(r, T)]), np.array([T]), phys)[0])
        print(f"    RH {100 * r:4.0f} %  ->  q* = {qq:6.3f} mol/kg   ({100 * qq / phys.q_max:5.1f} % of q_max)")
    print(f"  feed c_in                = {c_in:.4g} mol/m3")
    print(f"  MTZ width                = {w * 1e3:.3f} mm  -> N_z for 20 cells = {N}")
    print(f"  stoichiometric time      = {phys.stoichiometric_time(c_in, T) / 3600:.2f} h")


def generate(N_z=2000, rh_feed=0.30, run_convergence=True, horizon=2.5):
    phys = get_mof303_physics()
    T = phys.T_in
    c_in = rh_to_conc(rh_feed, T)

    print(f"MOF-303 water harvesting, feed {100 * rh_feed:.0f} % RH at {T - 273.15:.0f} C")
    report(phys, c_in, T)

    t_final = horizon * phys.stoichiometric_time(c_in, T)
    z, t, y = generate_breakthrough_data(phys, N_z=N_z, t_final=t_final, c_in=c_in, T_in=T)

    err = np.nan
    if run_convergence:
        print("  grid-convergence study (N_z/2 -> N_z)...")
        err = grid_convergence(phys, c_in, t_final, N_coarse=N_z // 2, N_fine=N_z, T_in=T)
        print(f"    exit-curve change: {100 * err:.3f} %")

    os.makedirs("data", exist_ok=True)
    np.savez(
        "data/mof303_breakthrough.npz",
        z=z, t=t, y=y,
        c_in=c_in, rh_feed=rh_feed, N_z=N_z, T_in=T,
        scheme="upwind", grid_convergence_err=err,
    )
    n = len(z)
    print(f"  exit c/c_in = {y[n - 1, -1] / c_in:.4f} | q_max = {y[n:2 * n].max():.3f} "
          f"| T_peak = {y[2 * n:].max():.2f} K")
    print("Saved data/mof303_breakthrough.npz")


if __name__ == "__main__":
    generate()
