"""Baseline Data-Driven architectures for comparison.

To prove that pure data-driven models hallucinate when extrapolating to unseen
boundary conditions (e.g., new MOFs or weather profiles), we implement standard
MLP and purely data-driven KAN/FNO models here.

These are trained ONLY on the data loss (no PDE physics loss).
"""
import torch
import torch.nn as nn

from output_head import apply_output_head
from kan_model import PIKAN_Adsorption

# 1. Data-Driven MLP (Standard Black Box)
class DataDrivenMLP(nn.Module):
    def __init__(self, width=64, depth=3):
        super().__init__()
        layers = []
        in_dim = 2 # (z, t)
        
        for _ in range(depth):
            layers.append(nn.Linear(in_dim, width))
            layers.append(nn.GELU())
            in_dim = width
            
        layers.append(nn.Linear(width, 3)) # (c, q, T)
        self.net = nn.Sequential(*layers)
        
    def forward(self, z_star, t_star):
        h = torch.cat([z_star, t_star], dim=1)
        raw_out = self.net(h)
        
        c, q, T = apply_output_head(raw_out[:, 0:1], raw_out[:, 1:2], raw_out[:, 2:3], t_star)
        return torch.cat([c, q, T], dim=1)


# 2. PINN (Physics-Informed Neural Network - MLP backbone)
# This uses the exact same MLP backbone as above, but in the training script
# it will be trained WITH the multiphysics PDE loss.
class PINN_Adsorption(DataDrivenMLP):
    """Identical to DataDrivenMLP, but trained with Physics loss."""
    pass


# 3. Data-Driven KAN
# Uses the exact same KAN architecture as PIKAN, but will be trained
# without physics to show that KANs alone cannot extrapolate without thermodynamics.
class DataDrivenKAN(PIKAN_Adsorption):
    pass


# 4. DeepONet (Branch-Trunk Architecture for Operators)
# Complementary to the FNO. Maps parametric boundary conditions (Branch)
# and spatial-temporal coordinates (Trunk) to the field output.
class DeepONet_Adsorption(nn.Module):
    def __init__(self, branch_dim=4, trunk_dim=2, p=64):
        super().__init__()
        self.p = p
        
        # Branch net processes MOF parameters (k_LDF, delta_H, etc.)
        self.branch = nn.Sequential(
            nn.Linear(branch_dim, 64),
            nn.GELU(),
            nn.Linear(64, p * 3) # p basis functions for 3 outputs
        )
        
        # Trunk net processes coordinates (z, t)
        self.trunk = nn.Sequential(
            nn.Linear(trunk_dim, 64),
            nn.GELU(),
            nn.Linear(64, p * 3)
        )
        
        self.bias = nn.Parameter(torch.zeros(1, 3))
        
    def forward(self, params, coords):
        # params: (B, branch_dim)
        # coords: (B, N, trunk_dim)
        B, N, _ = coords.shape
        
        b_out = self.branch(params) # (B, p*3)
        b_out = b_out.view(B, 3, self.p).unsqueeze(2) # (B, 3, 1, p)
        
        t_out = self.trunk(coords) # (B, N, p*3)
        t_out = t_out.view(B, N, 3, self.p).permute(0, 2, 1, 3) # (B, 3, N, p)
        
        # Dot product over p
        out = torch.sum(b_out * t_out, dim=-1) + self.bias.unsqueeze(-1) # (B, 3, N)
        out = out.permute(0, 2, 1) # (B, N, 3)
        
        t_star = coords[:, :, 1:2]
        c, q, T = apply_output_head(out[:, :, 0:1], out[:, :, 1:2], out[:, :, 2:3], t_star)
        return torch.cat([c, q, T], dim=-1)
