"""Publication-grade training script for PIKAN on 1D Adsorption Dynamics.
Incorporates Cosine Annealing and an L-BFGS polish for absolute minimum loss.
"""
import torch
import torch.optim as optim
import numpy as np
from kan_model import PIKAN_Adsorption
from pde_adsorption import compute_adsorption_pde_residuals
from solver_fd import AdsorptionPhysicsConfig
import time

class NondimConfig:
    def __init__(self, physics):
        self.L_ref = physics.L
        self.t_ref = 600.0  
        self.c_ref = 1.0    
        self.q_ref = physics.q_max
        self.T_ref = physics.T_w
        
        self.scale_mass_g = 1e-4
        self.scale_mass_s = 1.0
        self.scale_energy = 1e3

def load_anchor_data():
    data = np.load("data/synthetic_breakthrough.npz")
    z = data["z"]
    t = data["t"]
    y = data["y"]
    
    N_z = len(z)
    N_t = len(t)
    
    Z, T_grid = np.meshgrid(z, t, indexing='ij')
    return Z.flatten(), T_grid.flatten(), y[0:N_z, :].flatten(), y[N_z:2*N_z, :].flatten(), y[2*N_z:3*N_z, :].flatten()

def train(is_smoke_test=False):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"--- Starting High-Quality PIKAN Training on {device} ---")
    
    physics = AdsorptionPhysicsConfig()
    nondim = NondimConfig(physics)
    
    model = PIKAN_Adsorption(width=64, depth=3, num_grids=10).to(device)
    
    # 1. Load Anchor Data (10% sampling)
    Z_f, T_f, C_f, Q_f, Temp_f = load_anchor_data()
    np.random.seed(42)
    idx = np.random.choice(len(Z_f), int(0.1 * len(Z_f)), replace=False)
    
    z_anc = torch.tensor(Z_f[idx] / nondim.L_ref, dtype=torch.float32).unsqueeze(1).to(device)
    t_anc = torch.tensor(T_f[idx] / nondim.t_ref, dtype=torch.float32).unsqueeze(1).to(device)
    c_tgt = torch.tensor(C_f[idx] / nondim.c_ref, dtype=torch.float32).unsqueeze(1).to(device)
    q_tgt = torch.tensor(Q_f[idx] / nondim.q_ref, dtype=torch.float32).unsqueeze(1).to(device)
    T_tgt = torch.tensor(Temp_f[idx] / nondim.T_ref, dtype=torch.float32).unsqueeze(1).to(device)
    
    # 2. PDE Collocation Points
    N_colloc = 500 if is_smoke_test else 10000
    epochs_adam = 50 if is_smoke_test else 20000
    
    w_data = 100.0
    w_pde = 1.0
    
    # 3. Adam Phase with Cosine Annealing
    optimizer_adam = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer_adam, T_max=epochs_adam, eta_min=1e-5)
    
    start_time = time.time()
    for epoch in range(epochs_adam):
        optimizer_adam.zero_grad()
        
        # Resample collocation points to avoid grid-overfitting
        z_col = torch.rand(N_colloc, 1, requires_grad=True).to(device)
        t_col = torch.rand(N_colloc, 1, requires_grad=True).to(device)
        
        out_anc = model(z_anc, t_anc)
        loss_data = torch.mean((out_anc[:, 0:1] - c_tgt)**2) + \
                    torch.mean((out_anc[:, 1:2] - q_tgt)**2) + \
                    torch.mean((out_anc[:, 2:3] - T_tgt)**2)
                    
        res_mass_g, res_mass_s, res_energy = compute_adsorption_pde_residuals(model, z_col, t_col, nondim, physics)
        loss_pde = torch.mean(res_mass_g**2) + torch.mean(res_mass_s**2) + torch.mean(res_energy**2)
        
        loss = w_data * loss_data + w_pde * loss_pde
        loss.backward()
        optimizer_adam.step()
        scheduler.step()
        
        if epoch % (10 if is_smoke_test else 1000) == 0:
            print(f"Adam Epoch {epoch:05d} | Loss: {loss.item():.4e} | Data: {loss_data.item():.4e} | PDE: {loss_pde.item():.4e}")
            
    # 4. L-BFGS Polish Phase (for absolute minimum)
    print("--- Starting L-BFGS Polish ---")
    optimizer_lbfgs = optim.LBFGS(model.parameters(), max_iter=10 if is_smoke_test else 5000, 
                                  tolerance_grad=1e-7, tolerance_change=1e-9, 
                                  history_size=50, line_search_fn="strong_wolfe")
    
    z_col = torch.rand(N_colloc, 1, requires_grad=True).to(device)
    t_col = torch.rand(N_colloc, 1, requires_grad=True).to(device)
    
    def closure():
        optimizer_lbfgs.zero_grad()
        out_anc = model(z_anc, t_anc)
        loss_d = torch.mean((out_anc[:, 0:1] - c_tgt)**2) + torch.mean((out_anc[:, 1:2] - q_tgt)**2) + torch.mean((out_anc[:, 2:3] - T_tgt)**2)
        res_g, res_s, res_e = compute_adsorption_pde_residuals(model, z_col, t_col, nondim, physics)
        loss_p = torch.mean(res_g**2) + torch.mean(res_s**2) + torch.mean(res_e**2)
        loss_total = w_data * loss_d + w_pde * loss_p
        loss_total.backward()
        return loss_total
        
    optimizer_lbfgs.step(closure)
    final_loss = closure()
    print(f"Final L-BFGS Loss: {final_loss.item():.4e} | Time: {time.time()-start_time:.1f}s")
    
    torch.save(model.state_dict(), "data/pikan_weights_final.pth")
    print("Saved publication-grade weights to data/pikan_weights_final.pth")

if __name__ == "__main__":
    # Run as a 50-epoch smoke test locally
    train(is_smoke_test=True)
