"""PDE residual computation for 1D transient multiphysics adsorption dynamics via autograd.

The governing equations (dimensional form):

1. Mass Balance (Gas Phase):
    ε_t * ∂c/∂t = D_L * ∂²c/∂z² - v * ∂c/∂z - (1-ε_t) * ρ_p * ∂q/∂t

2. Mass Balance (Solid Phase - LDF Kinetics):
    ∂q/∂t = k_LDF * (q* - q)
    (where q* = q_max * b * c / (1 + b * c) is the Langmuir isotherm)

3. Energy Balance:
    (ε_t * ρ_g * C_pg + (1-ε_t) * ρ_p * C_ps) * ∂T/∂t = k_z * ∂²T/∂z² - v * ε_t * ρ_g * C_pg * ∂T/∂z + (1-ε_t) * ρ_p * (-ΔH) * ∂q/∂t - (4h/D_in) * (T - T_w)

The Neural Operator / PINN operates in nondimensional coordinates:
    c = c_ref * c*
    q = q_ref * q*
    T = T_ref * T*
    z = L_ref * z*
    t = t_ref * t*

All derivatives are computed via PyTorch autograd.
"""
import torch

def compute_adsorption_pde_residuals(model, z_s, t_s, nondim, physics):
    """Compute normalized PDE residuals for 1D transient adsorption.

    Args:
        model: PINN/PIKAN model that maps (z_s, t_s) -> (c_s, q_s, T_s)
        z_s, t_s: Scaled input tensors (N, 1), each in [0, 1]
        nondim: Nondimensionalizer config
        physics: PhysicsConfig (MOF properties)

    Returns:
        res_mass_gas, res_mass_solid, res_energy: Normalized residual tensors (N, 1)
    """
    # Enable gradient tracking
    z_s = z_s.requires_grad_(True)
    t_s = t_s.requires_grad_(True)

    # Forward pass: get nondimensional outputs
    outputs = model(z_s, t_s)
    c_s, q_s, T_s = outputs[:, 0:1], outputs[:, 1:2], outputs[:, 2:3]

    ones = torch.ones_like(z_s)

    # ── First derivatives ──
    dcs_dzs = torch.autograd.grad(c_s, z_s, ones, create_graph=True)[0]
    dcs_dts = torch.autograd.grad(c_s, t_s, ones, create_graph=True)[0]
    
    dqs_dts = torch.autograd.grad(q_s, t_s, ones, create_graph=True)[0]
    
    dTs_dzs = torch.autograd.grad(T_s, z_s, ones, create_graph=True)[0]
    dTs_dts = torch.autograd.grad(T_s, t_s, ones, create_graph=True)[0]

    # ── Second derivatives ──
    d2cs_dzs2 = torch.autograd.grad(dcs_dzs, z_s, ones, create_graph=True)[0]
    d2Ts_dzs2 = torch.autograd.grad(dTs_dzs, z_s, ones, create_graph=True)[0]

    # ── Convert to dimensional derivatives ──
    L = nondim.L_ref
    t_r = nondim.t_ref
    c_r = nondim.c_ref
    q_r = nondim.q_ref
    T_r = nondim.T_ref

    dc_dt = (c_r / t_r) * dcs_dts
    dc_dz = (c_r / L) * dcs_dzs
    d2c_dz2 = (c_r / L**2) * d2cs_dzs2

    dq_dt = (q_r / t_r) * dqs_dts

    dT_dt = (T_r / t_r) * dTs_dts
    dT_dz = (T_r / L) * dTs_dzs
    d2T_dz2 = (T_r / L**2) * d2Ts_dzs2

    # ── Dimensional fields ──
    c_dim = c_r * c_s
    q_dim = q_r * q_s
    T_dim = T_r * T_s

    # ── 1. Mass Balance (Gas) ──
    # ε_t * ∂c/∂t = D_L * ∂²c/∂z² - v * ∂c/∂z - (1-ε_t) * ρ_p * ∂q/∂t
    lhs_mass_g = physics.eps_t * dc_dt
    rhs_mass_g = physics.D_L * d2c_dz2 - physics.v * dc_dz - (1 - physics.eps_t) * physics.rho_p * dq_dt
    res_mass_g = lhs_mass_g - rhs_mass_g

    # ── 2. Mass Balance (Solid / Kinetics) ──
    # Langmuir Isotherm (Temperature dependent b)
    # b = b0 * exp(-ΔH / (R * T))
    b = physics.b0 * torch.exp(-physics.delta_H / (physics.R * T_dim))
    q_star = physics.q_max * b * c_dim / (1 + b * c_dim)
    
    # ∂q/∂t = k_LDF * (q* - q)
    lhs_mass_s = dq_dt
    rhs_mass_s = physics.k_LDF * (q_star - q_dim)
    res_mass_s = lhs_mass_s - rhs_mass_s

    # ── 3. Energy Balance ──
    # Heat capacity term
    C_term = physics.eps_t * physics.rho_g * physics.C_pg + (1 - physics.eps_t) * physics.rho_p * physics.C_ps
    lhs_energy = C_term * dT_dt
    
    # Heat transfer terms
    conduction = physics.k_z * d2T_dz2
    convection = physics.v * physics.eps_t * physics.rho_g * physics.C_pg * dT_dz
    heat_of_adsorption = (1 - physics.eps_t) * physics.rho_p * (-physics.delta_H) * dq_dt
    wall_loss = (4 * physics.h_w / physics.D_in) * (T_dim - physics.T_w)
    
    rhs_energy = conduction - convection + heat_of_adsorption - wall_loss
    res_energy = lhs_energy - rhs_energy

    # Normalize residuals to O(1)
    res_mass_g = res_mass_g / nondim.scale_mass_g
    res_mass_s = res_mass_s / nondim.scale_mass_s
    res_energy = res_energy / nondim.scale_energy

    return res_mass_g, res_mass_s, res_energy
