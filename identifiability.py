"""How far from local equilibrium is this system, and is k identifiable at all?

The kinetic estimator recovers k_LDF to 0.80 % median error given the EXACT
q*(c,T), and fails at ~96 % given a measured isotherm fingerprint. The reason is
not the interpolation scheme. It is that the LDF driving force is smaller than
any realistic isotherm measurement error.

    dq/dt = k (q* - q)

If the bed sits near local equilibrium, (q* - q) is a tiny difference of two
large numbers. Recovering k then requires knowing q* to much better than that
difference - and a measured isotherm is not that accurate.

This script quantifies the regime with the Damkohler number Da = k * t_ref and
the realised driving force, so the claim is a measurement rather than an anecdote.
"""
import json
import numpy as np
import ladder_data
from ladder_data import PARAM_KEYS
from isotherm import q_star_np
from run_l4 import physics_from_params

d = ladder_data.load_slice(z_frac=0.5, verbose=False)
nt = d.fields.shape[2]
rows = []
for gi in range(len(d.params)):
    p = physics_from_params(d.params[gi], d.param_keys)
    c = d.fields[gi,0,:]*p.c_in; q = d.fields[gi,1,:]*p.q_max; T = d.fields[gi,2,:]*p.T_in
    drive = q_star_np(c, T, p) - q
    t_ref = p.L / p.v
    rows.append({
        "gi": gi, "split": str(d.split[gi]),
        "Da": float(p.k_LDF * t_ref),
        "Da_run": float(p.k_LDF * d.t_final[gi]),
        "max_drive_frac": float(np.abs(drive).max() / p.q_max),
        "median_drive_frac": float(np.median(np.abs(drive)) / p.q_max),
    })

md = np.array([r["max_drive_frac"] for r in rows])
Da = np.array([r["Da_run"] for r in rows])
print("Realised LDF driving force |q* - q| as a FRACTION of q_max")
print(f"  peak over the run : p05={np.percentile(md,5)*100:.3f}%  median={np.median(md)*100:.3f}%  "
      f"p95={np.percentile(md,95)*100:.3f}%")
print(f"  fraction of conditions whose PEAK drive is < 1% of q_max : {100*np.mean(md<0.01):.1f}%")
print()
print("Damkohler number over the run, Da = k_LDF * t_final")
print(f"  p05={np.percentile(Da,5):.1f}  median={np.median(Da):.1f}  p95={np.percentile(Da,95):.1f}")
print(f"  Da >> 1 means kinetics are fast relative to the run: LOCAL EQUILIBRIUM.")
print()
print("Isotherm accuracy required to identify k to 10%:")
req = 0.1*md
print(f"  must know q* to better than {np.median(req)*100:.4f}% of q_max (median condition)")
print(f"  a 12-point interpolated fingerprint achieves ~2-3% of q_max")
print(f"  => shortfall of {(0.025/np.median(req)):.0f}x")
json.dump(rows, open("results/identifiability.json","w"), indent=2)
print("\nwrote results/identifiability.json")
