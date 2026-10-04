"""PREREG_P2 §4.3. Success (primary): support == {qstar, q} exactly, qstar coefficient
> 0, q coefficient < 0, and -coef(q)/coef(qstar) within 10 % of 1.
Accuracy (secondary): |k_hat - k| / k with k_hat = -coef(q)."""
import numpy as np


def success_L1(coefs, ratio_tol=0.10):
    sel = {k for k, v in coefs.items() if v != 0.0}
    if sel != {"qstar", "q"}:
        return False
    a, b = coefs["qstar"], coefs["q"]
    return a > 0 and b < 0 and abs(-b / a - 1.0) <= ratio_tol


def k_accuracy(coefs, k_true):
    return abs(-coefs.get("q", 0.0) - k_true) / k_true


def success_manifold(coefs, tol=0.05):
    """M9 success: the algebraic law q = q*_meas recovered -- support {qstar} with
    coefficient 1 within `tol`."""
    sel = {k for k, v in coefs.items() if v != 0.0}
    return sel == {"qstar"} and abs(coefs["qstar"] - 1.0) <= tol


def success_L2(coefs, c, q, q_max, n_bins=10, rho_max=-0.8, drop_max=0.6):
    """H2d (L2, exploratory) success, as PREREG_P2 §4.3 makes it operational.

    With q*_meas held fixed, the fitted law f's implied rate is k_hat = -df/dq. In
    Lib-B the q-dependent terms are q, c*q and q^2, so k_hat = -(b + d c + 2 e q). It is
    evaluated at the observed samples, averaged in n_bins equal bins of q/q_max over the
    observed range; the state dependence is DISCOVERED iff q*_meas and q are selected,
    k_hat decreases across the bins (Spearman rho < rho_max) and the top bin's k_hat is
    at most drop_max of the bottom bin's (the true k falls to 0.2 of k0)."""
    from scipy.stats import spearmanr
    sel = {k for k, v in coefs.items() if v != 0.0}
    if not {"qstar", "q"} <= sel:
        return False
    c, q = np.asarray(c, float), np.asarray(q, float)
    k_hat = -(coefs.get("q", 0.0) + coefs.get("c*q", 0.0) * c + 2.0 * coefs.get("q^2", 0.0) * q)
    x = q / q_max
    edges = np.linspace(x.min(), x.max(), n_bins + 1)
    idx = np.clip(np.digitize(x, edges[1:-1]), 0, n_bins - 1)
    means = np.array([k_hat[idx == b].mean() for b in range(n_bins) if np.any(idx == b)])
    if means.size < 3 or means[0] <= 0:
        return False
    rho = spearmanr(np.arange(means.size), means).correlation
    return bool(rho < rho_max and means[-1] <= drop_max * means[0])


def heldout_fidelity(pred, true):
    """Lib-A fidelity (PREREG_P2 §4.3): relative RMS error of the predicted dq/dt on the
    held-out probes, RMS(pred - true) / RMS(true)."""
    pred, true = np.asarray(pred, float), np.asarray(true, float)
    return float(np.sqrt(np.mean((pred - true) ** 2)) / np.sqrt(np.mean(true ** 2)))


def success_M6(coefs):
    """M6 (SINDy-PI, isothermal control, no isotherm given) success, PREREG_P2 §3: the
    implicit Langmuir-LDF structure dq + b c dq = k qm b c - k q - k b c q, i.e. support
    exactly {dq, c*dq, c, q, c*q} with, normalised to the dq coefficient = 1,
    c*dq > 0, c < 0, q > 0, c*q > 0 (all of b, k, qm positive)."""
    sel = {k for k, v in coefs.items() if v != 0.0}
    if sel != {"dq", "c*dq", "c", "q", "c*q"} or coefs["dq"] == 0:
        return False
    s = {k: v / coefs["dq"] for k, v in coefs.items()}
    return s["c*dq"] > 0 and s["c"] < 0 and s["q"] > 0 and s["c*q"] > 0
