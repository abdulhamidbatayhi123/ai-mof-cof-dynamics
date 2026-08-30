"""Advanced Physics-Informed Operator Networks (PI-DeepONet & PI-DeepOKAN).

This module contains the full suite of Operator Networks to complement the FNO,
ensuring a comprehensive benchmark of state-of-the-art physics-informed AI.
"""
import torch
import torch.nn as nn

from output_head import apply_output_head
from kan_model import RBFKANLayer

# ---------------------------------------------------------
# 1. Physics-Informed DeepONet (PI-DeepONet)
# Uses standard MLPs for the Branch and Trunk.
# ---------------------------------------------------------
class PI_DeepONet(nn.Module):
    def __init__(self, branch_dim=4, trunk_dim=2, p=64, width=64, depth=3):
        super().__init__()
        self.p = p
        
        # Branch (MLP): Processes parametric inputs (k_LDF, delta_H, etc.)
        b_layers = []
        in_d = branch_dim
        for _ in range(depth):
            b_layers.extend([nn.Linear(in_d, width), nn.GELU()])
            in_d = width
        b_layers.append(nn.Linear(width, p * 3))
        self.branch = nn.Sequential(*b_layers)
        
        # Trunk (MLP): Processes coordinates (z, t)
        t_layers = []
        in_d = trunk_dim
        for _ in range(depth):
            t_layers.extend([nn.Linear(in_d, width), nn.GELU()])
            in_d = width
        t_layers.append(nn.Linear(width, p * 3))
        self.trunk = nn.Sequential(*t_layers)
        
        self.bias = nn.Parameter(torch.zeros(1, 3))
        
    def forward(self, params, coords):
        B, N, _ = coords.shape
        
        b_out = self.branch(params).view(B, 3, self.p).unsqueeze(2)
        t_out = self.trunk(coords).view(B, N, 3, self.p).permute(0, 2, 1, 3)
        
        out = torch.sum(b_out * t_out, dim=-1) + self.bias.unsqueeze(-1)
        out = out.permute(0, 2, 1)
        
        t_star = coords[:, :, 1:2]
        c, q, T = apply_output_head(out[:, :, 0:1], out[:, :, 1:2], out[:, :, 2:3], t_star)
        return torch.cat([c, q, T], dim=-1)

# ---------------------------------------------------------
# 2. Physics-Informed DeepOKAN (PI-DeepOKAN)
# Uses Kolmogorov-Arnold Networks (KAN) for the Branch and Trunk.
# ---------------------------------------------------------
class PI_DeepOKAN(nn.Module):
    def __init__(self, branch_dim=4, trunk_dim=2, p=64, width=64, depth=3, num_grids=10):
        super().__init__()
        self.p = p
        
        # Branch (KAN): Learns univariate functions for material parameters
        b_dims = [branch_dim] + [width] * depth + [p * 3]
        self.branch_layers = nn.ModuleList([
            RBFKANLayer(b_dims[i], b_dims[i+1], num_grids) for i in range(len(b_dims)-1)
        ])
        
        # Trunk (KAN): Learns coordinate embeddings
        t_dims = [trunk_dim] + [width] * depth + [p * 3]
        self.trunk_layers = nn.ModuleList([
            RBFKANLayer(t_dims[i], t_dims[i+1], num_grids) for i in range(len(t_dims)-1)
        ])
        
        self.bias = nn.Parameter(torch.zeros(1, 3))
        
    def forward(self, params, coords):
        B, N, _ = coords.shape
        
        # Process Branch
        b_out = params
        for layer in self.branch_layers: b_out = layer(b_out)
        b_out = b_out.view(B, 3, self.p).unsqueeze(2)
        
        # Process Trunk
        t_out = coords.view(-1, 2) # Flatten batch and points
        for layer in self.trunk_layers: t_out = layer(t_out)
        t_out = t_out.view(B, N, 3, self.p).permute(0, 2, 1, 3)
        
        out = torch.sum(b_out * t_out, dim=-1) + self.bias.unsqueeze(-1)
        out = out.permute(0, 2, 1)
        
        t_star = coords[:, :, 1:2]
        c, q, T = apply_output_head(out[:, :, 0:1], out[:, :, 1:2], out[:, :, 2:3], t_star)
        return torch.cat([c, q, T], dim=-1)

# ---------------------------------------------------------
# 3. Wavelet Neural Operator (WNO) - Data-Driven Baseline
# Uses localized wavelets (approximated here via continuous 
# wavelet convolution structures) to handle sharp shock fronts.
# ---------------------------------------------------------
class WaveletNeuralOperator(nn.Module):
    """A proxy implementation of a Wavelet Neural Operator for benchmarking.
    
    In literature, WNOs use Discrete/Continuous Wavelet Transforms. Here, we 
    simulate the localized time-frequency decomposition using dilated convolutions
    which map to a wavelet filter bank behavior, avoiding Fourier Gibbs ringing.
    """
    def __init__(self, in_channels=6, out_channels=3, width=64, num_levels=3):
        super().__init__()
        self.lift = nn.Conv2d(in_channels, width, 1)
        
        # Dilated convolutions simulate multi-scale wavelet decomposition
        self.wavelet_blocks = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(width, width, kernel_size=3, padding=2**i, dilation=2**i),
                nn.GELU()
            ) for i in range(num_levels)
        ])
        
        self.proj1 = nn.Conv2d(width, width, 1)
        self.proj2 = nn.Conv2d(width, out_channels, 1)

    def _inputs(self, params, grid_z, grid_t, device):
        B = params.shape[0]
        az = torch.linspace(0.0, 1.0, grid_z, device=device)
        at = torch.linspace(0.0, 1.0, grid_t, device=device)
        gz, gt = torch.meshgrid(az, at, indexing="ij")
        coords = torch.stack([gz, gt]).unsqueeze(0).expand(B, -1, -1, -1)
        cond = params[:, :, None, None].expand(-1, -1, grid_z, grid_t)
        return torch.cat([coords, cond], dim=1)
        
    def forward(self, params, grid_z=100, grid_t=100):
        z = self.lift(self._inputs(params, grid_z, grid_t, params.device))
        
        # Multi-scale feature extraction (Wavelet Proxy)
        for block in self.wavelet_blocks:
            z = z + block(z)
            
        out = self.proj2(torch.nn.functional.gelu(self.proj1(z)))
        
        at = torch.linspace(0.0, 1.0, grid_t, device=params.device)
        t_env = at.view(1, 1, 1, grid_t)
        
        c_star, q_star, T_star = apply_output_head(
            out[:, 0:1, :, :], out[:, 1:2, :, :], out[:, 2:3, :, :], t_env
        )
        return torch.cat([c_star, q_star, T_star], dim=1)
