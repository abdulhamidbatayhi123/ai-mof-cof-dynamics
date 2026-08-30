"""Physics-Informed KAN (PIKAN) for 1D Adsorption Dynamics.

Maps (z*, t*) -> (c*, q*, T*)
Uses a localized Gaussian-RBF basis with a SiLU base path, learnable centers,
and learnable widths to rigorously handle shock fronts and avoid dead units.
"""
import numpy as np
import torch
import torch.nn as nn

class RBFKANLayer(nn.Module):
    """Advanced KAN layer combining a global base path with a localized RBF path.
       y_o = w_b * SiLU(x) + Σ_i Σ_g C[i,o,g] * exp(-((x_i - c_g)/h_g)^2)
    """
    def __init__(self, in_features, out_features, num_grids=10, use_layernorm=False):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.norm = nn.LayerNorm(in_features) if use_layernorm else None
        
        # 1. Global Base Path (from Liu et al. 2024)
        self.base_activation = nn.SiLU()
        self.base_weight = nn.Linear(in_features, out_features, bias=False)
        
        # 2. Localized RBF Path with learnable centers and widths
        grid = torch.linspace(-2.0, 2.0, num_grids)
        self.centers = nn.Parameter(grid.clone())
        self.h = nn.Parameter(torch.ones_like(grid) * (4.0 / (num_grids - 1)))
        
        coeffs = torch.empty(in_features, out_features, num_grids)
        nn.init.normal_(coeffs, mean=0.0, std=1.0 / np.sqrt(in_features * num_grids))
        self.coeffs = nn.Parameter(coeffs)

    def forward(self, x):
        if self.norm is not None:
            x = self.norm(x)
            
        # Base path
        base = self.base_weight(self.base_activation(x))
        
        # RBF path
        # x: (N, in, 1), centers: (1, 1, G), h: (1, 1, G)
        x_expand = x.unsqueeze(-1)
        c_expand = self.centers.view(1, 1, -1)
        h_expand = self.h.view(1, 1, -1)
        
        # Guard against zero division in width
        h_safe = torch.clamp(h_expand, min=1e-4)
        
        z = (x_expand - c_expand) / h_safe
        phi = torch.exp(-z * z) # (N, in, G)
        
        rbf_out = torch.einsum("nig,iog->no", phi, self.coeffs)
        
        return base + rbf_out


class PIKAN_Adsorption(nn.Module):
    """Physics-informed KAN for multiphysics adsorption."""
    def __init__(self, width: int = 64, depth: int = 3, num_grids: int = 20, dT_max: float = 0.5):
        super().__init__()
        
        input_dim = 2  # z*, t*
        output_dim = 3 # c*, q*, T*
        
        dims = [input_dim] + [width] * depth + [output_dim]
        self.dT_max = dT_max

        self.layers = nn.ModuleList()
        for i in range(len(dims) - 1):
            # NO layernorm on the input (i=0) to preserve coordinate system
            apply_ln = (i > 0)
            self.layers.append(RBFKANLayer(dims[i], dims[i + 1], num_grids, use_layernorm=apply_ln))

    def forward(self, z_star, t_star):
        h = torch.cat([z_star, t_star], dim=1)
        for layer in self.layers:
            h = layer(h)
            
        raw_c = h[:, 0:1]
        raw_q = h[:, 1:2]
        raw_T = h[:, 2:3]
        
        env = t_star
        c_star = env * torch.nn.functional.softplus(raw_c)
        q_star = env * torch.nn.functional.softplus(raw_q)

        # Temperature is bounded, not free. An unconstrained T* can cross zero,
        # which makes the isotherm's van't Hoff exponential diverge and NaNs the
        # whole graph. The excursion is capped at `self.dT_max` in units of
        # T_ref, which is generous next to the adiabatic rise (beta ~ 3) and
        # never binds on a physical solution.
        T_star = 1.0 + self.dT_max * torch.tanh(env * raw_T)

        return torch.cat([c_star, q_star, T_star], dim=1)
