"""O1 discovery: from one observation (p2_observe.observe format) to coefficients.

Every probe position is an independent time series of (c, q, T). The library is Lib-B
with q* = the MEASURED equilibrium evaluated at the observed (c, T). Rows from all
probes are stacked (strong form: one row per sample; weak form: one row per test
function per probe), so the fitted law is shared along the column -- which it is.
"""
import numpy as np

from p2 import methods
from p2.features import derivative, lib_b
from p2.weak import weak_system

SOLVERS = {"best_subset": methods.best_subset, "stlsq": methods.stlsq,
           "ensemble": methods.ensemble}


def discover_o1(obs, method, form):
    t = obs["t"]
    ch = obs["channels"]
    blocks_F, blocks_y = [], []
    for j in range(ch["q"].shape[0]):
        c, q, T = ch["c"][j], ch["q"][j], ch["T"][j]
        F = lib_b(c, q, T, obs["qstar_meas"](c, T))
        if form == "strong":
            blocks_F.append(F)
            blocks_y.append(derivative(q, t))
        elif form == "weak":
            G, b = weak_system(F, q, t)
            blocks_F.append(G)
            blocks_y.append(b)
        else:
            raise ValueError(form)
    F_all = {k: np.concatenate([B[k] for B in blocks_F]) for k in blocks_F[0]}
    return SOLVERS[method](F_all, np.concatenate(blocks_y))
