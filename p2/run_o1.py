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


WEAK_SUPPORTS = (31, 61, 121)     # PREREG_P2 §3 M2: test-function support swept
HOLDOUT_EVERY = 5                 # every 5th probe held out to choose the support
MIN_ROWS_PER_TERM = 3             # a support's training system must be this overdetermined


def _stack(blocks):
    F = {k: np.concatenate([B[0][k] for B in blocks]) for k in blocks[0][0]}
    return F, np.concatenate([B[1] for B in blocks])


def _weak_blocks(obs, support):
    t, ch = obs["t"], obs["channels"]
    out = []
    for j in range(ch["q"].shape[0]):
        c, q, T = ch["c"][j], ch["q"][j], ch["T"][j]
        out.append(weak_system(lib_b(c, q, T, obs["qstar_meas"](c, T)), q, t, support=support))
    return out


def choose_support(obs, method):
    """M2's support, chosen by held-out weak-system residual: fit on the probes not
    held out, score ||G theta - b|| / ||b|| on every HOLDOUT_EVERY-th probe. Probes are
    independent time series of one shared law, so this is a genuine hold-out."""
    n = obs["channels"]["q"].shape[0]
    held = [j for j in range(n) if j % HOLDOUT_EVERY == HOLDOUT_EVERY // 2]
    if not held or len(held) == n:
        return WEAK_SUPPORTS[1], {}
    scores = {}
    for s in WEAK_SUPPORTS:
        blocks = _weak_blocks(obs, s)
        Ftr, ytr = _stack([B for j, B in enumerate(blocks) if j not in held])
        # well-posedness: a long support leaves few test functions per probe, and an
        # under-determined weak system fits a WRONG, dense law with zero residual --
        # which a residual criterion would then prefer (found on the known-answer
        # test). Admissible only with >= MIN_ROWS_PER_TERM equations per library term.
        if len(ytr) < MIN_ROWS_PER_TERM * len(Ftr):
            continue
        Fte, yte = _stack([blocks[j] for j in held])
        coefs = SOLVERS[method](Ftr, ytr)
        pred = sum(coefs.get(k, 0.0) * Fte[k] for k in Fte)
        scores[s] = float(np.linalg.norm(pred - yte) / max(np.linalg.norm(yte), 1e-300))
    if not scores:
        return WEAK_SUPPORTS[0], {}
    return min(scores, key=scores.get), scores


def discover_o1(obs, method, form):
    t = obs["t"]
    ch = obs["channels"]
    if form == "weak":
        support, _ = choose_support(obs, method)
        F_all, y_all = _stack(_weak_blocks(obs, support))
        return SOLVERS[method](F_all, y_all)
    if form != "strong":
        raise ValueError(form)
    blocks_F, blocks_y = [], []
    for j in range(ch["q"].shape[0]):
        c, q, T = ch["c"][j], ch["q"][j], ch["T"][j]
        blocks_F.append(lib_b(c, q, T, obs["qstar_meas"](c, T)))
        blocks_y.append(derivative(q, t))
    F_all = {k: np.concatenate([B[k] for B in blocks_F]) for k in blocks_F[0]}
    return SOLVERS[method](F_all, np.concatenate(blocks_y))


def discover_o2(obs, phys, method, form, probes=None):
    """O2 via M1b: invert the gas balance for q at every observed position, then run
    the O1 pipeline on (c, q_recovered, T). `probes` selects which positions enter the
    regression (the inversion needs neighbours in z, so edge positions are dropped)."""
    from p2.massbal import invert_uptake
    c, T = obs["channels"]["c"], obs["channels"]["T"]
    q_hat = invert_uptake(c, obs["z"], obs["t"], phys, obs["c_in"])
    sel = probes if probes is not None else slice(1, c.shape[0] - 1)
    o1 = {"t": obs["t"], "qstar_meas": obs["qstar_meas"],
          "channels": {"c": c[sel], "q": q_hat[sel], "T": T[sel]}}
    return discover_o1(o1, method, form)
