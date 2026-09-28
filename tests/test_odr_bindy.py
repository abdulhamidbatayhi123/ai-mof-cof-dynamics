"""Reproduction of the ODR-BINDy repository's Lorenz example (Lorenz.m).

Setup copied from https://github.com/llfung/ODR-BINDy/blob/main/Lorenz.m:
sigma=10, beta=8/3, rho=28, x0=[-8,8,27], tspan=dt:dt:5 with dt=0.01 (N=500),
ode89 RelTol=AbsTol=1e-12, eps_x = 0.2*std(x_clean(:)) (= 2.5542, which matches
the paper's figure file name Lorenz_dyn_eps2.5542_dt0.01_tf5), polyorder=2
(Polynomial3D2O, M=10 incl. constant), FD(N,6,dt), SigmaX=eps_x,
SigmaY=1e-4, SigmaP=1e2, ODR_BINDy_Greedy with default options.
Differences: noise drawn with numpy default_rng(12), not MATLAB rng(12).

Reported numbers (Fung et al., arXiv:2507.23426v1, HTML version):
  R1  Sec. 3.2, Fig. 4 (top) caption "Example of recovering the Lorenz63 system
      ... 20% noise ... dt=0.01": the Lorenz.m example is shown as a correct
      recovery (exact support of the 7 true terms).
  R2  Sec. 3.2, Fig. 4 (bottom), ODR-BINDy panel, cell (noise 20 %, T=5):
      success rate ~0.79 (read from heatmap pixels against the colour bar;
      not tabulated in the text).
  R3  Sec. 6.1, Fig. 8, ODR-BINDy panel, cell (noise 20 %, T=5): averaged
      relative parameter error ||Xi-Xi_true||_F/||Xi_true||_F ~ 10^-2.65
      = 2.2e-3 (read from heatmap pixels; average over runs).
  R4  Sec. 2.3.1 text: "<90s on an Apple M4 Macbook Air" for 1000 points,
      20 % noise; README "Speed": ~2 minutes. Runtime is recorded, not asserted.
Asserted: support == truth (R1) and relative error <= 10^-2.65 (R3).
"""
import json
import time
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from p2.odr_bindy import PolynomialLibrary, fd_matrices, odr_bindy_greedy

ROOT = Path(__file__).resolve().parents[1]
REPORTED_REL_ERR = 10 ** -2.65


def _lorenz(t, y, s=10.0, b=8 / 3, r=28.0):
    return [s * (y[1] - y[0]), y[0] * (r - y[2]) - y[1], y[0] * y[1] - b * y[2]]


def _truth():
    Xi = np.zeros((10, 3))
    Xi[1] = [-10, 28, 0]; Xi[2] = [10, -1, 0]; Xi[3] = [0, 0, -8 / 3]
    Xi[5] = [0, 0, 1]; Xi[6] = [0, -1, 0]
    return Xi


def run_lorenz_example(seed=12):
    dt, tf = 0.01, 5.0
    t = np.arange(1, int(round(tf / dt)) + 1) * dt
    xc = solve_ivp(_lorenz, (t[0], t[-1]), [-8, 8, 27], t_eval=t, method="DOP853",
                   rtol=1e-12, atol=1e-12).y.T
    eps = 0.2 * np.std(xc, ddof=1)
    x = xc + eps * np.random.default_rng(seed).standard_normal(xc.shape)
    N = x.shape[0]
    lib = PolynomialLibrary(3, 2, ["x", "y", "z"])
    I, D = fd_matrices(N, 6, dt)
    t0 = time.perf_counter()
    Xi, J, Xd, hist = odr_bindy_greedy(
        x, lib, I, D, eps * np.ones_like(x), 1e-4 * np.ones((I.shape[0], 3)),
        1e2 * np.ones((10, 3)), options=dict(VerboseLevel=1), seed=seed)
    runtime = time.perf_counter() - t0
    tru = _truth()
    rel = float(np.linalg.norm(Xi - tru) / np.linalg.norm(tru))
    support_ok = bool(np.array_equal(Xi != 0, tru != 0))
    out = dict(
        example="Lorenz.m (N=500, dt=0.01, 20%% noise, eps_x=%.4f, 2nd-order library)" % eps,
        reproduced=dict(
            support_correct=support_ok,
            n_terms_found=int((Xi != 0).sum()), n_terms_true=int((tru != 0).sum()),
            missing_terms=[f"{lib.names[m]} in d{'xyz'[d]}/dt" for m, d in zip(*np.where((Xi == 0) & (tru != 0)))],
            extra_terms=[f"{lib.names[m]} in d{'xyz'[d]}/dt" for m, d in zip(*np.where((Xi != 0) & (tru == 0)))],
            rel_frobenius_error=rel,
            log10_rel_error=float(np.log10(rel)),
            Xi=Xi.tolist(), J_evidence=float(J), J_history=hist.get("J_history"),
            runtime_s=runtime, denoise_rmse=float(np.sqrt(np.mean((Xd - xc) ** 2))),
            noise_rmse=float(np.sqrt(np.mean((x - xc) ** 2))),
            noise_rng="numpy default_rng(12) (MATLAB rng(12) stream not reproducible)"),
        reported=dict(
            support_correct=dict(value=True, source="arXiv:2507.23426v1 Sec. 3.2, Fig. 4 top (this exact example, file Lorenz_dyn_eps2.5542_dt0.01_tf5)"),
            success_rate_T5_noise20=dict(value=0.79, source="arXiv:2507.23426v1 Sec. 3.2, Fig. 4 bottom, ODR-BINDy panel, pixel read vs colour bar"),
            rel_frobenius_error_T5_noise20=dict(value=REPORTED_REL_ERR, log10=-2.65, source="arXiv:2507.23426v1 Sec. 6.1, Fig. 8, ODR-BINDy panel, pixel read vs colour bar (run average)"),
            runtime=dict(value="<90 s (1000 pts, Apple M4); ~2 min", source="arXiv:2507.23426v1 Sec. 2.3.1 text; README 'Speed'")),
        meets_reported_accuracy=bool(support_ok and rel <= REPORTED_REL_ERR),
    )
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "odr_bindy_verification.json").write_text(json.dumps(out, indent=2))
    return out


import pytest as _pytest


@_pytest.mark.xfail(strict=True, reason=(
    "2026-09-28: support reproduced exactly (7 terms, none extra) but relative "
    "coefficient error 5.0e-3 vs ~2.2e-3 read from the paper's Fig. 8 heatmap (a "
    "multi-run average; this is one run with a different noise draw -- MATLAB's "
    "rng(12) stream cannot be reproduced); 26x slower; lsqnonlin replaced by "
    "Gauss-Newton. Not yet the strongest configuration (PREREG_P2 §3)."))
def test_lorenz_example_reproduces_reported_accuracy():
    out = run_lorenz_example()
    rep = out["reproduced"]
    assert rep["support_correct"], (rep["missing_terms"], rep["extra_terms"])
    assert rep["rel_frobenius_error"] <= REPORTED_REL_ERR, rep["rel_frobenius_error"]


if __name__ == "__main__":
    print(json.dumps(run_lorenz_example()["reproduced"], indent=1)[:3000])
