"""Regenerate both ground-truth datasets with the verified solver."""
import time, numpy as np, os
from solver_fd import AdsorptionPhysicsConfig, generate_breakthrough_data, grid_convergence
from isotherm import henry_constant
import fetch_real_mof_data as mof

t0 = time.time()
print("="*70, flush=True)
print("[1/2] Generic Type I sorbent (baseline / ablation case)", flush=True)
print("="*70, flush=True)
p = AdsorptionPhysicsConfig(); c_in = 1.0
w, N = p.mtz_width(c_in)
ts = p.stoichiometric_time(c_in)
print(f"  MTZ {w*1e3:.3f} mm -> N_z(20c)={N} | t_stoich {ts/3600:.2f} h | K_H {henry_constant(p.T_w,p):.4g}", flush=True)
z,t,y = generate_breakthrough_data(p, N_z=2000, t_final=2.5*ts, c_in=c_in)
print("  grid convergence...", flush=True)
err = grid_convergence(p, c_in, 2.5*ts, N_coarse=1000, N_fine=2000)
print(f"    exit-curve change 1000->2000: {100*err:.3f} %", flush=True)
os.makedirs("data", exist_ok=True)
np.savez("data/synthetic_breakthrough.npz", z=z,t=t,y=y, c_in=c_in, N_z=2000,
         scheme="upwind", grid_convergence_err=err)
n=len(z)
print(f"  exit c/c_in={y[n-1,-1]/c_in:.4f} q_max={y[n:2*n].max():.3f} T_peak={y[2*n:].max():.2f}K "
      f"[{time.time()-t0:.0f}s]", flush=True)

print("", flush=True)
print("="*70, flush=True)
print("[2/2] MOF-303 Type V water harvesting", flush=True)
print("="*70, flush=True)
mof.generate(N_z=2000, rh_feed=0.30, run_convergence=True)
print(f"\nALL DONE in {time.time()-t0:.0f}s", flush=True)
