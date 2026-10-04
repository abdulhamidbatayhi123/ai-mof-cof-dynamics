"""Does L4's gas-mass residual vanish on the solver's own fields?  (B72 check)

Owner of results/l4_residual_check.json. The Methods draft (2026-10-04) found by
algebra that run_l4.pde_residual's gas-mass equation lacks a 1/eps_t on its advection
and dispersion terms relative to what solver_fd.py integrates:

  solver, made dimensionless by the adsorption-sink scale
      (1/Lam) c_t + tau/(eps Lam) c_z - tau/(Pe Lam)     c_zz + q_t = 0
  run_l4.py:167
      (1/Lam) c_t + tau/Lam       c_z - tau/(Pe Lam)       c_zz + q_t

with c = c/c_in, q = q/q_max, z = z/L, t = t/t_final, tau = t_final v / L,
Lam = (1-eps) rho_p q_max / (eps c_in), Pe = v L / D_L.

The decisive test is not algebra but the data: a residual that is the right equation
must be small when evaluated on the solver's own stored fields. Here both forms are
evaluated by finite differences on stored v2 fields (256 x 256, the generator's
uniform resample), and their RMS is reported relative to the RMS of the sink term q_t.
Finite differences on a resampled field are not exact, so the test is COMPARATIVE:
the form that is the solver's equation must be far smaller than the one that is not.

    python verify_l4_residual.py
"""
import json
import os

import numpy as np

from ladder_data import param_keys_for
from run_l4 import physics_from_params
from v2_common import ROOT_V2

OUT = "results/l4_residual_check.json"
N_SAMPLES = 30
SEED = 20261004


def residuals(f, p, t_final):
    c, q = f[0].astype(np.float64), f[1].astype(np.float64)
    nz, nt = c.shape
    z = np.linspace(0.0, 1.0, nz)
    t = np.linspace(0.0, 1.0, nt)
    c_z = np.gradient(c, z, axis=0)
    c_zz = np.gradient(c_z, z, axis=0)
    c_t = np.gradient(c, t, axis=1)
    q_t = np.gradient(q, t, axis=1)
    eps = p.eps_t
    lam = (1 - eps) * p.rho_p * p.q_max / (eps * p.c_in)
    pe = p.v * p.L / p.D_L
    tau = t_final * p.v / p.L
    code = c_t / lam + (tau / lam) * c_z - (tau / (pe * lam)) * c_zz + q_t
    fixed = c_t / lam + (tau / (eps * lam)) * c_z - (tau / (pe * lam)) * c_zz + q_t
    inner = (slice(2, -2), slice(2, -2))                 # away from one-sided stencils
    scale = np.sqrt(np.mean(q_t[inner] ** 2))
    rel = lambda r: float(np.sqrt(np.mean(r[inner] ** 2)) / scale)
    return rel(code), rel(fixed), float(eps)


def main():
    man = json.load(open(os.path.join(ROOT_V2, "manifest.json")))
    keys = param_keys_for(man)
    mats = {m["material_id"]: m for m in man["materials"]}
    conds = {c["condition_id"]: c for c in man["conditions"]}
    samples = [s for s in man["samples"]
               if os.path.exists(os.path.join(ROOT_V2, f"m{s['mat']:04d}_c{s['cond']:04d}.npy"))]
    pick = np.random.default_rng(SEED).choice(len(samples), N_SAMPLES, replace=False)
    rows = []
    for i in pick:
        s = samples[i]
        m, c = mats[s["mat"]], conds[s["cond"]]
        vec = [(m if k in m else c)[k] for k in keys]
        p = physics_from_params(np.asarray(vec, float), keys)
        if not hasattr(p, "c_in") or p.c_in is None:
            raise SystemExit("physics_from_params returned no c_in; cannot scale c")
        f = np.load(os.path.join(ROOT_V2, f"m{s['mat']:04d}_c{s['cond']:04d}.npy"))
        rc, rf, eps = residuals(f, p, s["t_final"])
        rows.append({"mat": s["mat"], "cond": s["cond"], "eps_t": eps,
                     "rel_rms_pre_b72_form": rc, "rel_rms_solver_form": rf})
        print(f"  m{s['mat']:04d} c{s['cond']:04d}  eps {eps:.3f}   pre-B72 form {rc:8.3f}   "
              f"solver form {rf:8.3f}", flush=True)
    code = np.array([r["rel_rms_pre_b72_form"] for r in rows])
    fixed = np.array([r["rel_rms_solver_form"] for r in rows])
    out = {"_what": __doc__.splitlines()[0], "n_samples": len(rows), "seed": SEED,
           "median_rel_rms_pre_b72_form": float(np.median(code)),
           "median_rel_rms_solver_form": float(np.median(fixed)),
           "median_ratio_pre_b72_over_solver": float(np.median(code / fixed)),
           "n_pre_b72_worse": int((code > fixed).sum()), "rows": rows}
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"median relative residual: pre-B72 form {out['median_rel_rms_pre_b72_form']:.3f}, "
          f"solver form {out['median_rel_rms_solver_form']:.3f}; pre-B72 form worse in "
          f"{out['n_pre_b72_worse']}/{len(rows)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
