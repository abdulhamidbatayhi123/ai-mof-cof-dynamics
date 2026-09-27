"""PREREG_P2 §4.3. Success (primary): support == {qstar, q} exactly, qstar coefficient
> 0, q coefficient < 0, and -coef(q)/coef(qstar) within 10 % of 1.
Accuracy (secondary): |k_hat - k| / k with k_hat = -coef(q)."""


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
