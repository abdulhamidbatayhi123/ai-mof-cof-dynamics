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