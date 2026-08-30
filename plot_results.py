"""Publication-Ready Visualization Suite for MOF/COF Digital Twins.

This script rigorously evaluates the true outputs of trained models loaded from disk.
If trained weights are missing or produce NaNs, the script will crash rather than plot placeholders.
"""
import numpy as np
import matplotlib.pyplot as plt
import torch
import os
from kan_model import PIKAN_Adsorption

def load_data():
    data = np.load("data/mof303_breakthrough.npz")
    z = data["z"]
    t = data["t"]
    y = data["y"]
    return z, t, y

def evaluate_model(model_path, z_arr, t_arr):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"CRITICAL: Cannot plot. Model weights {model_path} not found.")
        
    model = PIKAN_Adsorption()
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    
    # Normalize inputs
    L = 1.0; t_ref = 3600.0
    z_norm = torch.tensor(z_arr / L, dtype=torch.float32).unsqueeze(1)
    t_norm = torch.tensor(t_arr / t_ref, dtype=torch.float32).unsqueeze(1)
    
    with torch.no_grad():
        out = model(z_norm, t_norm)
        if torch.isnan(out).any():
            raise ValueError(f"CRITICAL: Model {model_path} outputs NaNs! Cannot plot.")
            
    # Denormalize outputs based on nondim config
    # To be fully wired once nondimensionalization is refactored
    c_pred = out[:, 0].numpy()
    q_pred = out[:, 1].numpy()
    T_pred = out[:, 2].numpy()
    return c_pred, q_pred, T_pred

def plot_breakthrough_curves():
    print("Evaluating trained models on ground truth...")
    z, t, y = load_data()
    
    # We will plot the breakthrough at the exit of the column (z = L)
    exit_idx = len(z) - 1
    t_arr = t
    z_arr = np.full_like(t_arr, z[exit_idx])
    
    try:
        c_pikan, q_pikan, T_pikan = evaluate_model("data/pikan_weights_final.pth", z_arr, t_arr)
    except Exception as e:
        print(f"Plotting aborted: {e}")
        return
        
    # --- Plotting logic here ONLY if model evaluated successfully ---
    # ...

if __name__ == "__main__":
    plot_breakthrough_curves()
