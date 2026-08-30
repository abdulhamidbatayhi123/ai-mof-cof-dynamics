"""Physics-Informed KAN (PIKAN) for 1D Adsorption Dynamics.

Maps (z*, t*) -> (c*, q*, T*)
Uses the localized Gaussian-RBF basis to handle the stiff cycling/breakthrough
while remaining infinitely differentiable for the PDE residuals.
"""
import numpy as np
import torch
import torch.nn as nn

class RBFKANLayer(nn.Module):
    """KAN layer with a LOCALIZED Gaussian-RBF basis.
        y_o = Σ_i Σ_g  C[i,o,g] · exp(-((LN(x_i) − c_g)/h)²)
    """
    def __init__(self, in_features, out_features, num_grids=10, use_layernorm=True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.norm = nn.LayerNorm(in_features) if use_layernorm else None
        
        grid = torch.linspace(-2.0, 2.0, num_grids)
        self.register_buffer("grid", grid)
        self.h = float(grid[1] - grid[0])
        
        coeffs = torch.empty(in_features, out_features, num_grids)
        nn.init.normal_(coeffs, mean=0.0, std=1.0 / np.sqrt(in_features * num_grids))
        self.coeffs = nn.Parameter(coeffs)

    def forward(self, x):
        if self.norm is not None:
            x = self.norm(x)
        z = (x.unsqueeze(-1) - self.grid) / self.h        # (N, in, G)
        phi = torch.exp(-z * z)
        return torch.einsum("nig,iog->no", phi, self.coeffs)


class PIKAN_Adsorption(nn.Module):
    """Physics-informed KAN for multiphysics adsorption.
    
    Inputs:
        z*: Normalized spatial coordinate [0, 1]
        t*: Normalized time [0, 1]
    
    Outputs:
        c*: Normalized gas concentration
        q*: Normalized solid uptake
        T*: Normalized temperature
    """
    def __init__(self, width: int = 64, depth: int = 3, num_grids: int = 10, use_layernorm: bool = True):
        super().__init__()
        
        input_dim = 2  # z*, t*
        output_dim = 3 # c*, q*, T*
        
        dims = [input_dim] + [width] * depth + [output_dim]
        
        self.layers = nn.ModuleList(
            RBFKANLayer(dims[i], dims[i + 1], num_grids, use_layernorm=use_layernorm)
            for i in range(len(dims) - 1)
        )

    def forward(self, z_star, t_star):
        h = torch.cat([z_star, t_star], dim=1)
        for layer in self.layers:
            h = layer(h)
            
        raw_c = h[:, 0:1]
        raw_q = h[:, 1:2]
        raw_T = h[:, 2:3]
        
        # Hard Initial Conditions at t*=0
        # Assume initially clean bed at ambient temperature T_w
        # c(t=0) = 0, q(t=0) = 0, T(t=0) = T_w (normalized to 1.0 or similar)
        # Using the t* envelope trick from the machining project:
        env = t_star 
        
        c_star = env * torch.nn.functional.softplus(raw_c)
        q_star = env * torch.nn.functional.softplus(raw_q)
        
        # Temperature is initially at ambient (T* = T_w / T_ref)
        # T_star = T_ambient_star + env * NN_out
        # For simplicity, assuming T_ambient is baseline 1.0 when normalized to itself
        T_star = 1.0 + env * raw_T 
        
        return torch.cat([c_star, q_star, T_star], dim=1)
