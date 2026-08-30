"""Parametric FNO2d for Multiphysics Adsorption Dynamics.

Maps MOF parameters -> the full spatiotemporal (z, t) FRAME on a uniform grid:
    (params) -> [c*(z,t), q*(z,t), T*(z,t)]

This acts as the Digital Twin Operator: given a MOF's properties, it instantly 
outputs the full 2D breakthrough field over the entire spatial column and time horizon.
"""
import torch
import torch.nn as nn

from output_head import apply_output_head

class SpectralConv2d(nn.Module):
    """Fourier-space convolution keeping the lowest `modes` frequencies."""
    def __init__(self, in_ch, out_ch, modes):
        super().__init__()
        self.in_ch, self.out_ch, self.modes = in_ch, out_ch, modes
        scale = 1.0 / (in_ch * out_ch)
        self.w = nn.Parameter(scale * torch.randn(2, in_ch, out_ch, modes, modes, 2))

    def _mul(self, x_ft, w):
        return torch.einsum("bixy,ioxy->boxy", x_ft, w)

    def forward(self, x):
        B, C, H, W = x.shape
        m = self.modes
        x_ft = torch.fft.rfft2(x)
        out_ft = torch.zeros(B, self.out_ch, H, W // 2 + 1, dtype=torch.cfloat, device=x.device)
        w0 = torch.view_as_complex(self.w[0])
        w1 = torch.view_as_complex(self.w[1])
        
        out_ft[:, :, :m, :m] = self._mul(x_ft[:, :, :m, :m], w0)
        out_ft[:, :, -m:, :m] = self._mul(x_ft[:, :, -m:, :m], w1)
        
        return torch.fft.irfft2(out_ft, s=(H, W))


class FNO2d_Adsorption(nn.Module):
    def __init__(self, num_params=4, modes=16, width=64, n_layers=4):
        super().__init__()
        self.modes, self.width = modes, width
        
        # Inputs: (z, t) coordinates [2] + parametric properties [num_params]
        in_ch = 2 + num_params
        
        self.lift = nn.Conv2d(in_ch, width, 1)
        self.spectral = nn.ModuleList(SpectralConv2d(width, width, modes) for _ in range(n_layers))
        self.pointwise = nn.ModuleList(nn.Conv2d(width, width, 1) for _ in range(n_layers))
        self.act = nn.GELU()
        
        self.proj1 = nn.Conv2d(width, width, 1)
        # Outputs: c, q, T [3 channels]
        self.proj2 = nn.Conv2d(width, 3, 1)

    def _inputs(self, params, grid_z, grid_t, device):
        B = params.shape[0]
        
        # Create coordinate grid
        az = torch.linspace(0.0, 1.0, grid_z, device=device)
        at = torch.linspace(0.0, 1.0, grid_t, device=device)
        gz, gt = torch.meshgrid(az, at, indexing="ij")  # (grid_z, grid_t)
        
        coords = torch.stack([gz, gt]).unsqueeze(0).expand(B, -1, -1, -1)
        
        # Broadcast params across the entire (z, t) grid
        cond = params[:, :, None, None].expand(-1, -1, grid_z, grid_t)
        
        return torch.cat([coords, cond], dim=1)  # (B, 2+num_params, grid_z, grid_t)

    def forward(self, params, grid_z=100, grid_t=100):
        # params shape: (B, num_params)
        z = self.lift(self._inputs(params, grid_z, grid_t, params.device))
        
        for spec, pw in zip(self.spectral, self.pointwise):
            z = self.act(spec(z) + pw(z))
            
        out = self.proj2(self.act(self.proj1(z)))  # (B, 3, grid_z, grid_t)
        
        # Hard IC/Positivity
        # T* = 1.0 + t* * NN_out
        # c* = t* * softplus(NN_out)
        # q* = t* * softplus(NN_out)
        
        at = torch.linspace(0.0, 1.0, grid_t, device=params.device)
        t_env = at.view(1, 1, 1, grid_t)
        
        c_star, q_star, T_star = apply_output_head(
            out[:, 0:1, :, :], out[:, 1:2, :, :], out[:, 2:3, :, :], t_env
        )
        return torch.cat([c_star, q_star, T_star], dim=1)
