"""Finite Difference / Method of Lines Solver for 1D Adsorption Column.
This acts as the high-fidelity ground truth for training and verifying the Neural Operators.
"""
import numpy as np
from scipy.integrate import solve_ivp

class AdsorptionPhysicsConfig:
    def __init__(self):
        # Default MOF properties (e.g., Zeolite 13X or a standard MOF like MOF-801 for water)
        self.eps_t = 0.4        # Total porosity
        self.rho_p = 1200.0     # Particle density (kg/m3)
        self.rho_g = 1.2        # Gas density (kg/m3)
        self.C_pg = 1000.0      # Gas heat capacity (J/kg.K)
        self.C_ps = 1000.0      # Solid heat capacity (J/kg.K)
        
        self.D_L = 1e-4         # Axial dispersion (m2/s)
        self.v = 0.1            # Interstitial velocity (m/s)
        
        self.k_LDF = 0.05       # LDF mass transfer coefficient (1/s)
        self.delta_H = -50000.0 # Heat of adsorption (J/mol) - exothermic
        self.R = 8.314          # Universal gas constant (J/mol.K)
        
        self.q_max = 20.0       # Max capacity (mol/kg)
        self.b0 = 1e-6          # Langmuir pre-exponential
        
        self.k_z = 0.1          # Axial thermal conductivity (W/m.K)
        self.h_w = 10.0         # Wall heat transfer coefficient (W/m2.K)
        self.D_in = 0.05        # Column inner diameter (m)
        self.T_w = 298.0        # Wall temperature (K)
        
        self.L = 1.0            # Column length (m)

def generate_breakthrough_data(physics, N_z=100, t_final=600.0, c_in=1.0, T_in=298.0):
    """Solves the 1D adsorption column using Method of Lines (MOL)."""
    
    z_edges = np.linspace(0, physics.L, N_z + 1)
    dz = physics.L / N_z
    z_centers = (z_edges[:-1] + z_edges[1:]) / 2.0
    
    # State vector: [c_1...c_N, q_1...q_N, T_1...T_N]
    # Initial conditions (clean bed)
    c0 = np.zeros(N_z)
    q0 = np.zeros(N_z)
    T0 = np.ones(N_z) * physics.T_w
    
    y0 = np.concatenate([c0, q0, T0])
    
    def pde_system(t, y):
        c = y[0:N_z]
        q = y[N_z:2*N_z]
        T = y[2*N_z:3*N_z]
        
        dc_dt = np.zeros(N_z)
        dq_dt = np.zeros(N_z)
        dT_dt = np.zeros(N_z)
        
        # Isotherm
        b = physics.b0 * np.exp(-physics.delta_H / (physics.R * T))
        q_star = physics.q_max * b * c / (1 + b * c)
        
        # Kinetics (Solid Mass Balance)
        dq_dt = physics.k_LDF * (q_star - q)
        
        # Spatial derivatives (Upwind for advection, Central for diffusion)
        for i in range(N_z):
            # Boundary conditions for c and T
            c_prev = c[i-1] if i > 0 else c_in
            c_next = c[i+1] if i < N_z-1 else c[i] # Danckwerts outflow
            
            T_prev = T[i-1] if i > 0 else T_in
            T_next = T[i+1] if i < N_z-1 else T[i]
            
            # First derivatives (Upwind)
            dc_dz = (c[i] - c_prev) / dz
            dT_dz = (T[i] - T_prev) / dz
            
            # Second derivatives (Central)
            if i == 0:
                d2c_dz2 = (c_next - 2*c[i] + c_in) / (dz**2)
                d2T_dz2 = (T_next - 2*T[i] + T_in) / (dz**2)
            elif i == N_z - 1:
                d2c_dz2 = (c_prev - 2*c[i] + c[i]) / (dz**2) # Zero gradient at exit
                d2T_dz2 = (T_prev - 2*T[i] + T[i]) / (dz**2)
            else:
                d2c_dz2 = (c_next - 2*c[i] + c_prev) / (dz**2)
                d2T_dz2 = (T_next - 2*T[i] + T_prev) / (dz**2)
                
            # Gas Mass Balance
            source_mass = (1 - physics.eps_t) * physics.rho_p * dq_dt[i]
            dc_dt[i] = (physics.D_L * d2c_dz2 - physics.v * dc_dz - source_mass) / physics.eps_t
            
            # Energy Balance
            C_term = physics.eps_t * physics.rho_g * physics.C_pg + (1 - physics.eps_t) * physics.rho_p * physics.C_ps
            conduction = physics.k_z * d2T_dz2
            convection = physics.v * physics.eps_t * physics.rho_g * physics.C_pg * dT_dz
            heat_gen = (1 - physics.eps_t) * physics.rho_p * (-physics.delta_H) * dq_dt[i]
            wall_loss = (4 * physics.h_w / physics.D_in) * (T[i] - physics.T_w)
            
            dT_dt[i] = (conduction - convection + heat_gen - wall_loss) / C_term
            
        return np.concatenate([dc_dt, dq_dt, dT_dt])

    print("Solving multiphysics PDEs via BDF method...")
    # BDF is excellent for stiff adsorption PDEs
    sol = solve_ivp(pde_system, [0, t_final], y0, method='BDF', t_eval=np.linspace(0, t_final, 100))
    
    print(f"Solver finished. Status: {sol.status}")
    return z_centers, sol.t, sol.y

if __name__ == "__main__":
    import os
    phys = AdsorptionPhysicsConfig()
    z, t, y = generate_breakthrough_data(phys)
    
    os.makedirs("data", exist_ok=True)
    np.savez("data/synthetic_breakthrough.npz", z=z, t=t, y=y)
    print("Ground truth data saved to data/synthetic_breakthrough.npz")
