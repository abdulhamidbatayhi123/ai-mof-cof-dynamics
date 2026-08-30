"""Automates the deployment of the MOF Dynamics codebase to a Kaggle GPU Kernel."""
import os
import json
import shutil
import subprocess

def deploy_to_kaggle():
    kaggle_dir = "kaggle_run"
    os.makedirs(kaggle_dir, exist_ok=True)
    
    # 1. Create kernel-metadata.json
    metadata = {
      "id": "abdulhamidbatayhi/mof-cof-digital-twin",
      "title": "MOF-COF Digital Twin (Physics-Informed)",
      "code_file": "kaggle_main.py",
      "language": "python",
      "kernel_type": "script",
      "is_private": "true",
      "enable_gpu": "true",
      "enable_internet": "true",
      "dataset_sources": [],
      "competition_sources": [],
      "kernel_sources": []
    }
    
    with open(os.path.join(kaggle_dir, "kernel-metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    # 2. Write the main Kaggle execution script
    kaggle_main = """
import os
import sys

# Train the PIKAN
print("--- Launching PIKAN GPU Training ---")
import train_pikan
# Override epochs for a full run if not smoke test
# We will just run the standard train() which is 20000 epochs + L-BFGS
train_pikan.train(is_smoke_test=False)

print("--- Launching SINDy Discovery ---")
import sindy_discovery
# SINDy runs instantly on CPU/GPU
import numpy as np
# Generate fresh test data for SINDy
np.random.seed(42)
N = 1000
q = np.random.rand(N, 1) * 10
c = np.random.rand(N, 1)
q_star = np.random.rand(N, 1) * 20
dQ_dt_noisy = (0.05 * q_star - 0.05 * q) + np.random.randn(N, 1) * 0.001
disc = sindy_discovery.SINDy_Discoverer(threshold=0.01)
disc.discover(q, c, q_star, dQ_dt_noisy)

print("Kaggle Run Complete.")
"""
    with open(os.path.join(kaggle_dir, "kaggle_main.py"), "w") as f:
        f.write(kaggle_main.strip())
        
    # 3. Copy dependencies
    deps = [
        "train_pikan.py",
        "kan_model.py",
        "pde_adsorption.py",
        "solver_fd.py",
        "sindy_discovery.py"
    ]
    
    for dep in deps:
        shutil.copy(dep, os.path.join(kaggle_dir, dep))
        
    # Copy data dir
    os.makedirs(os.path.join(kaggle_dir, "data"), exist_ok=True)
    shutil.copy("data/synthetic_breakthrough.npz", os.path.join(kaggle_dir, "data/synthetic_breakthrough.npz"))
    
    # 4. Push to Kaggle
    print("Pushing to Kaggle...")
    result = subprocess.run(["kaggle", "kernels", "push", "-p", kaggle_dir], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Successfully pushed to Kaggle!")
        print(result.stdout)
    else:
        print("Failed to push to Kaggle:")
        print(result.stderr)

if __name__ == "__main__":
    deploy_to_kaggle()
